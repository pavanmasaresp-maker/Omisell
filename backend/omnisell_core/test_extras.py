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
