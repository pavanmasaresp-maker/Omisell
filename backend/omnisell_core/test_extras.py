from unittest import mock

from django.test import TestCase

from accounts.testutils import client_for, make_user
from catalog.models import Product, SKU, Variant
from inventory.services import apply_entry
from marketplaces.adapters.base import AdapterError
from marketplaces.models import ChannelConnection
from marketplaces.order_import import pull_all, pull_orders
from omnisell_core.exports import safe, to_csv
from orders.models import Order
from tenants.models import Tenant


class PublicPagesTests(TestCase):
    def test_pages_open_without_login(self):
        for url, text in (("/privacy", "Privacy"), ("/account-delete", "Delete")):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertIn(text, r.content.decode())


class CsvTests(TestCase):
    def test_safe_blocks_formulas(self):
        self.assertEqual(safe("=1+1"), "'=1+1")
        self.assertEqual(safe("Ramesh"), "Ramesh")
        self.assertIn("'=cmd", to_csv(["a"], [["=cmd"]]))


class PullTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T")
        self.user = make_user(self.tenant, "own", "OWNER")
        self.api = client_for(self.user)
        p = Product.objects.create(tenant=self.tenant, title="Cap")
        v = Variant.objects.create(tenant=self.tenant, product=p, name="Default")
        self.sku = SKU.objects.create(tenant=self.tenant, variant=v, sku_code="CAP-R", price="199")
        apply_entry(tenant_id=self.tenant.id, sku=self.sku, entry_type="ADJUSTMENT", delta=10,
                    reason="t", idempotency_key="k1", user=None)
        self.conn = ChannelConnection.objects.create(
            tenant=self.tenant, channel="WOOCOMMERCE", name="Shop", shop_domain="shop.example.com",
            status="CONNECTED")
        self.rows = [
            {"external_order_id": "1", "customer_name": "A", "items": [{"sku_code": "CAP-R", "quantity": 2}]},
            {"external_order_id": "2", "customer_name": "B", "items": [{"sku_code": "NOPE", "quantity": 1}]}]

    def test_pull_imports_new_reports_failed_and_is_idempotent(self):
        with mock.patch("marketplaces.adapters.registry.get_adapter") as ga:
            ga.return_value.fetch_orders.return_value = self.rows
            r1 = pull_orders(self.conn)
            r2 = pull_orders(self.conn)
        self.assertEqual((r1["new"], r1["existing"], len(r1["failed"])), (1, 0, 1))
        self.assertEqual((r2["new"], r2["existing"]), (0, 1))
        self.assertEqual(Order.objects.filter(tenant=self.tenant).count(), 1)

    def test_endpoint_and_adapter_error(self):
        url = f"/api/v1/channels/connections/{self.conn.id}/pull-orders"
        with mock.patch("marketplaces.adapters.registry.get_adapter") as ga:
            ga.return_value.fetch_orders.return_value = self.rows
            r = self.api.post(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["new"], 1)
        with mock.patch("marketplaces.adapters.registry.get_adapter") as ga:
            ga.return_value.fetch_orders.side_effect = AdapterError("token galat", needs_action=True)
            r = self.api.post(url)
        self.assertEqual(r.status_code, 400)

    def test_pull_all_survives_channel_error(self):
        with mock.patch("marketplaces.adapters.registry.get_adapter") as ga:
            ga.return_value.fetch_orders.side_effect = AdapterError("down", retryable=True)
            self.assertEqual(pull_all(), 0)
        self.conn.refresh_from_db()
        self.assertEqual(self.conn.last_error, "down")

    def test_csv_endpoints(self):
        with mock.patch("marketplaces.adapters.registry.get_adapter") as ga:
            ga.return_value.fetch_orders.return_value = self.rows[:1]
            pull_orders(self.conn)
        r = self.api.get("/api/v1/export/orders.csv")
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("order_number", body)
        self.assertIn("CAP-R", body)
        r = self.api.get("/api/v1/export/stock.csv")
        self.assertIn("CAP-R", r.content.decode())
        self.assertEqual(self.api.get("/api/v1/export/orders.csv?profile=zzz").status_code, 400)


class FileChannelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T")
        self.api = client_for(make_user(self.tenant, "own", "OWNER"))
        p = Product.objects.create(tenant=self.tenant, title="Cap")
        v = Variant.objects.create(tenant=self.tenant, product=p, name="Default")
        self.sku = SKU.objects.create(tenant=self.tenant, variant=v, sku_code="CAP-R", price="199")
        apply_entry(tenant_id=self.tenant.id, sku=self.sku, entry_type="ADJUSTMENT", delta=10,
                    reason="t", idempotency_key="k2", user=None)
        r = self.api.post("/api/v1/channels/connections", {"channel": "FILE", "name": "Meesho"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.conn_id = r.json()["id"]
        self.url = f"/api/v1/channels/connections/{self.conn_id}/import-orders"

    def body(self):
        return {"orders": [
            {"external_order_id": "M1", "customer_name": "Asha", "shipping_address": {"city": "Pune"},
             "items": [{"sku_code": "CAP-R", "quantity": 2, "unit_price": "180"}]},
            {"external_order_id": "M2", "items": [{"sku_code": "NOPE", "quantity": 1}]}]}

    def test_create_needs_no_token_and_duplicate_name_rejected(self):
        r = self.api.post("/api/v1/channels/connections", {"channel": "FILE", "name": "Meesho"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.api.post("/api/v1/channels/connections", {"channel": "SHOPIFY", "name": "S",
                          "shop_domain": "x.myshopify.com"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_import_creates_orders_reports_failures_and_is_idempotent(self):
        r1 = self.api.post(self.url, self.body(), format="json").json()
        r2 = self.api.post(self.url, self.body(), format="json").json()
        self.assertEqual((r1["new"], len(r1["failed"])), (1, 1))
        self.assertEqual((r2["new"], r2["existing"]), (0, 1))
        o = Order.objects.get(tenant=self.tenant)
        self.assertEqual(o.external_order_id, "M1")
        self.assertEqual(o.items.first().unit_price, 180)

    def test_bad_payload_and_wrong_channel(self):
        self.assertEqual(self.api.post(self.url, {"orders": []}, format="json").status_code, 400)
        bad = {"orders": [{"external_order_id": "X", "items": [{"sku_code": "A", "quantity": 0}]}]}
        self.assertEqual(self.api.post(self.url, bad, format="json").status_code, 400)
        demo = self.api.post("/api/v1/channels/connections", {"channel": "DEMO", "name": "D",
                             "access_token": "demo"}, format="json").json()["id"]
        r = self.api.post(f"/api/v1/channels/connections/{demo}/import-orders", self.body(), format="json")
        self.assertEqual(r.status_code, 400)
        r = self.api.post(f"/api/v1/channels/connections/{self.conn_id}/pull-orders")
        self.assertEqual(r.status_code, 400)


class AutoPublishTests(TestCase):
    def setUp(self):
        from marketplaces.models import SyncJob  # noqa: F401
        self.tenant = Tenant.objects.create(name="T")
        self.api = client_for(make_user(self.tenant, "own", "OWNER"))
        self.demo = self.api.post("/api/v1/channels/connections", {"channel": "DEMO", "name": "D1",
                                  "access_token": "demo"}, format="json").json()["id"]

    def make(self, title, code):
        p = self.api.post("/api/v1/products", {"title": title}, format="json").json()
        v = self.api.post("/api/v1/variants", {"product": p["id"], "name": "D"}, format="json").json()
        k = self.api.post("/api/v1/skus", {"variant": v["id"], "sku_code": code, "price": "100"},
                          format="json").json()
        return p, v, k

    def jobs(self):
        from marketplaces.models import SyncJob
        return SyncJob.objects.filter(tenant=self.tenant, job_type="PUBLISH_PRODUCT").count()

    def test_off_by_default(self):
        self.make("Shirt", "S1")
        self.assertEqual(self.jobs(), 0)

    def test_on_publishes_when_sku_added_and_when_edited(self):
        url = f"/api/v1/channels/connections/{self.demo}/auto-publish"
        self.assertEqual(self.api.post(url, {"enabled": "yes"}, format="json").status_code, 400)
        self.assertTrue(self.api.post(url, {"enabled": True}, format="json").json()["auto_publish"])
        p, v, k = self.make("Shirt", "S1")
        self.assertEqual(self.jobs(), 1)                      # product banne par nahi, SKU banne par
        v2 = self.api.post("/api/v1/skus", {"variant": v["id"], "sku_code": "S2", "price": "120"},
                           format="json").json()
        self.assertEqual(self.jobs(), 2)                      # naya SKU = nayi job
        self.api.patch(f"/api/v1/skus/{k['id']}", {"price": "110"}, format="json")
        self.assertEqual(self.jobs(), 3)                      # price badla
        self.api.patch(f"/api/v1/products/{p['id']}", {"title": "Shirt 2"}, format="json")
        self.assertEqual(self.jobs(), 4)                      # naam badla

    def test_product_without_sku_not_sent(self):
        self.api.post(f"/api/v1/channels/connections/{self.demo}/auto-publish", {"enabled": True}, format="json")
        p = self.api.post("/api/v1/products", {"title": "Empty"}, format="json").json()
        self.api.patch(f"/api/v1/products/{p['id']}", {"title": "Empty 2"}, format="json")
        self.assertEqual(self.jobs(), 0)

    def test_publish_all(self):
        self.make("A", "A1"); self.make("B", "B1")
        self.api.post("/api/v1/products", {"title": "NoSku"}, format="json")
        url = f"/api/v1/channels/connections/{self.demo}/publish-all"
        r = self.api.post(url).json()
        self.assertEqual((r["queued"], r["no_sku"]), (2, 1))
        r = self.api.post(url).json()
        self.assertEqual(r["queued"], 0)                      # dobara dabane par duplicate job nahi
        file_c = self.api.post("/api/v1/channels/connections", {"channel": "FILE", "name": "Meesho"},
                               format="json").json()["id"]
        self.assertEqual(self.api.post(f"/api/v1/channels/connections/{file_c}/publish-all").status_code, 400)
        self.assertEqual(self.api.post(f"/api/v1/channels/connections/{file_c}/auto-publish",
                                       {"enabled": True}, format="json").status_code, 400)


class ProductDeleteTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T")
        self.api = client_for(make_user(self.tenant, "own", "OWNER"))
        self.other = client_for(make_user(Tenant.objects.create(name="T2"), "o2", "OWNER"))
        self.p = self.api.post("/api/v1/products", {"title": "Shirt"}, format="json").json()
        v = self.api.post("/api/v1/variants", {"product": self.p["id"], "name": "D"}, format="json").json()
        self.k = self.api.post("/api/v1/skus", {"variant": v["id"], "sku_code": "S1", "price": "100"},
                               format="json").json()
        self.api.post("/api/v1/inventory/adjust", {"sku": self.k["id"], "entry_type": "ADJUSTMENT",
                      "quantity_delta": 5, "idempotency_key": "d1"}, format="json")

    def test_delete_with_stock_history_works(self):
        r = self.api.delete(f"/api/v1/products/{self.p['id']}")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Product.objects.filter(id=self.p["id"]).exists())
        self.assertFalse(SKU.objects.filter(tenant=self.tenant).exists())

    def test_delete_blocked_when_orders_exist(self):
        r = self.api.post("/api/v1/orders", {"customer_name": "A", "items": [{"sku": self.k["id"], "quantity": 1}],
                          "idempotency_key": "o1"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        r = self.api.delete(f"/api/v1/products/{self.p['id']}")
        self.assertEqual(r.status_code, 409)
        self.assertIn("ARCHIVED", r.json()["error"])
        self.assertTrue(Product.objects.filter(id=self.p["id"]).exists())

    def test_other_tenant_cannot_delete(self):
        self.assertEqual(self.other.delete(f"/api/v1/products/{self.p['id']}").status_code, 404)
        self.assertTrue(Product.objects.filter(id=self.p["id"]).exists())


class OverviewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T")
        self.api = client_for(make_user(self.tenant, "own", "OWNER"))
        p = Product.objects.create(tenant=self.tenant, title="Charger")
        v = Variant.objects.create(tenant=self.tenant, product=p, name="Default")
        self.sku = SKU.objects.create(tenant=self.tenant, variant=v, sku_code="CH-1", price="500")
        apply_entry(tenant_id=self.tenant.id, sku=self.sku, entry_type="ADJUSTMENT", delta=50,
                    reason="t", idempotency_key="ov1", user=None)
        self.conn = self.api.post("/api/v1/channels/connections", {"channel": "FILE", "name": "Meesho"},
                                  format="json").json()["id"]

    def test_fees_validation_and_overview_numbers(self):
        url = f"/api/v1/channels/connections/{self.conn}/fees"
        self.assertEqual(self.api.post(url, {"commission_pct": "150"}, format="json").status_code, 400)
        self.assertEqual(self.api.post(url, {"commission_pct": "abc"}, format="json").status_code, 400)
        r = self.api.post(url, {"commission_pct": "10", "charge_per_order": "20"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        body = {"orders": [
            {"external_order_id": "A", "items": [{"sku_code": "CH-1", "quantity": 2, "unit_price": "500"}]},
            {"external_order_id": "B", "items": [{"sku_code": "CH-1", "quantity": 1, "unit_price": "500"}]}]}
        self.api.post(f"/api/v1/channels/connections/{self.conn}/import-orders", body, format="json")
        Order.objects.filter(external_order_id="B").update(status="CANCELLED")
        d = self.api.get("/api/v1/dashboard/overview?days=0").json()
        ch = [c for c in d["channels"] if c["name"] == "Meesho"][0]
        self.assertEqual((ch["orders"], ch["units"]), (1, 2))
        self.assertEqual(ch["revenue"], "1000.00")
        self.assertEqual(ch["fees"], "120.00")   # 10% of 1000 + 20 x 1 order
        self.assertEqual(ch["net"], "880.00")
        self.assertEqual(d["pipeline"]["CANCELLED"], 1)
        self.assertEqual(d["top_products"][0]["units"], 2)
        self.assertEqual(d["totals"]["products"], 1)

    def test_other_tenant_isolated_and_empty_ok(self):
        other = client_for(make_user(Tenant.objects.create(name="O"), "oth", "OWNER"))
        d = other.get("/api/v1/dashboard/overview").json()
        self.assertEqual((d["totals"]["products"], d["channels"]), (0, []))


class FlipkartConnectTests(TestCase):
    def setUp(self):
        self.api = client_for(make_user(Tenant.objects.create(name="T"), "own", "OWNER"))

    def test_token_format_checked_and_connect_with_mock(self):
        r = self.api.post("/api/v1/channels/connections", {"channel": "FLIPKART", "name": "FK",
                          "access_token": "noColon"}, format="json")
        self.assertEqual(r.status_code, 400)
        with mock.patch("marketplaces.adapters.flipkart.FlipkartAdapter.health_check", return_value={}):
            r = self.api.post("/api/v1/channels/connections", {"channel": "FLIPKART", "name": "FK",
                              "access_token": "app:secret"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["status"], "CONNECTED")
