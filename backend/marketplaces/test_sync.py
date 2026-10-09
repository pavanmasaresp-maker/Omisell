from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from accounts.testutils import client_for, make_user
from marketplaces.adapters.base import AdapterError
from marketplaces.adapters.demo import DemoAdapter
from marketplaces.models import ChannelListing, SyncJob
from marketplaces.sync import run_due
from tenants.models import Tenant

GQL = "marketplaces.adapters.shopify.ShopifyAdapter._graphql"


class SyncTests(TestCase):
    def setUp(self):
        t1 = Tenant.objects.create(name="T1")
        t2 = Tenant.objects.create(name="T2")
        self.owner = client_for(make_user(t1, "o1", "OWNER"))
        self.viewer = client_for(make_user(t1, "v1", "VIEWER"))
        self.other = client_for(make_user(t2, "o2", "OWNER"))
        r = self.owner.post("/api/v1/channels/connections",
                            {"channel": "DEMO", "name": "Demo", "access_token": "demo"}, format="json")
        self.conn = r.json()["id"]
        self.pid, self.sku = self.make_product("Shirt", "S1")

    def make_product(self, title, code=None):
        p = self.owner.post("/api/v1/products", {"title": title}, format="json").json()
        if not code:
            return p["id"], None
        v = self.owner.post("/api/v1/variants", {"product": p["id"], "name": "D"}, format="json").json()
        k = self.owner.post("/api/v1/skus", {"variant": v["id"], "sku_code": code, "price": "100"},
                            format="json").json()
        return p["id"], k["id"]

    def publish(self, client=None, product=None, conn=None):
        return (client or self.owner).post("/api/v1/channels/publish", {
            "product": product or self.pid, "connection": conn or self.conn}, format="json")

    def test_publish_then_worker_activates_listing(self):
        r = self.publish()
        self.assertEqual(r.status_code, 202)
        self.assertEqual(r.json()["status"], "PENDING")
        self.assertEqual(run_due(), 1)
        listing = ChannelListing.objects.get()
        self.assertEqual(listing.status, "ACTIVE")
        self.assertEqual(listing.external_product_id, "demo-" + self.pid)
        job = SyncJob.objects.get()
        self.assertEqual((job.status, job.attempts), ("SUCCEEDED", 1))
        self.assertEqual(job.attempt_log.count(), 1)

    def test_publish_is_idempotent(self):
        r1, r2 = self.publish(), self.publish()
        self.assertEqual((r1.status_code, r2.status_code), (202, 200))
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(SyncJob.objects.count(), 1)

    def test_retryable_failure_backs_off_then_fails(self):
        with mock.patch.object(DemoAdapter, "create_listing",
                               side_effect=AdapterError("429", retryable=True)):
            self.publish()
            run_due()
            job = SyncJob.objects.get()
            self.assertEqual((job.status, job.attempts), ("PENDING", 1))
            self.assertGreater(job.next_run_at, timezone.now())
            self.assertEqual(run_due(), 0)  # abhi due nahi
            for _ in range(4):
                SyncJob.objects.update(next_run_at=timezone.now() - timedelta(seconds=1))
                run_due()
        job.refresh_from_db()
        self.assertEqual((job.status, job.attempts), ("FAILED", 5))
        self.assertEqual(ChannelListing.objects.get().status, "FAILED")
        self.assertEqual(job.attempt_log.count(), 5)

    def test_needs_action_then_manual_retry(self):
        with mock.patch.object(DemoAdapter, "create_listing",
                               side_effect=AdapterError("token expired", needs_action=True)):
            jid = self.publish().json()["id"]
            run_due()
        job = SyncJob.objects.get()
        self.assertEqual(job.status, "NEEDS_ACTION")
        self.assertEqual(ChannelListing.objects.get().status, "NEEDS_ACTION")
        r = self.owner.post(f"/api/v1/channels/jobs/{jid}/retry")
        self.assertEqual(r.status_code, 200)
        run_due()
        self.assertEqual(ChannelListing.objects.get().status, "ACTIVE")
        # succeeded job retry nahi hota
        self.assertEqual(self.owner.post(f"/api/v1/channels/jobs/{jid}/retry").status_code, 400)

    def test_product_without_sku_needs_action(self):
        pid, _ = self.make_product("Empty")
        self.publish(product=pid)
        run_due()
        job = SyncJob.objects.get()
        self.assertEqual(job.status, "NEEDS_ACTION")
        self.assertIn("SKU", job.last_error)

    def test_inventory_change_enqueues_sync_after_publish(self):
        self.publish()
        run_due()
        with self.captureOnCommitCallbacks(execute=True):
            r = self.owner.post("/api/v1/inventory/adjust",
                                {"sku": self.sku, "quantity_delta": 7}, format="json")
        self.assertEqual(r.status_code, 201)
        job = SyncJob.objects.get(job_type="UPDATE_INVENTORY")
        self.assertEqual(job.status, "PENDING")
        with mock.patch.object(DemoAdapter, "update_inventory", return_value={}) as m:
            run_due()
        m.assert_called_once_with("demo-" + self.pid, "S1", 7)
        job.refresh_from_db()
        self.assertEqual(job.status, "SUCCEEDED")

    def test_no_inventory_job_when_not_published(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.owner.post("/api/v1/inventory/adjust",
                            {"sku": self.sku, "quantity_delta": 5}, format="json")
        self.assertEqual(SyncJob.objects.count(), 0)

    def test_roles_and_tenant_isolation(self):
        self.assertEqual(self.publish(client=self.viewer).status_code, 403)
        self.assertEqual(self.publish(client=self.other).status_code, 404)
        self.publish()
        self.assertEqual(self.other.get("/api/v1/channels/jobs").json()["results"], [])
        self.assertEqual(self.viewer.get("/api/v1/channels/jobs").status_code, 200)
        self.assertEqual(len(self.owner.get("/api/v1/channels/listings").json()["results"]), 1)

    def test_cannot_publish_to_broken_connection(self):
        with mock.patch(GQL, side_effect=AdapterError("bad token", needs_action=True)):
            r = self.owner.post("/api/v1/channels/connections", {
                "channel": "SHOPIFY", "name": "Shop", "shop_domain": "x.myshopify.com",
                "access_token": "t"}, format="json")
        self.assertEqual(r.json()["status"], "ERROR")
        self.assertEqual(self.publish(conn=r.json()["id"]).status_code, 400)
