import random

from django.test import TestCase

from accounts.testutils import client_for, make_user
from inventory.models import InventoryBalance
from marketplaces.models import ChannelConnection, SyncJob
from marketplaces.order_import import import_order, make_demo_order
from marketplaces.sync import run_due
from orders.models import Order, OrderStatus
from orders.services import OrderError
from tenants.models import Tenant


class OrderImportTests(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="T1")
        t2 = Tenant.objects.create(name="T2")
        self.owner = client_for(make_user(self.t1, "o1", "OWNER"))
        self.viewer = client_for(make_user(self.t1, "v1", "VIEWER"))
        self.other = client_for(make_user(t2, "o2", "OWNER"))
        self.conn_id = self.owner.post("/api/v1/channels/connections", {
            "channel": "DEMO", "name": "Demo store", "access_token": "demo"}, format="json").json()["id"]
        self.conn = ChannelConnection.objects.get(id=self.conn_id)
        p = self.owner.post("/api/v1/products", {"title": "Shirt"}, format="json").json()
        v = self.owner.post("/api/v1/variants", {"product": p["id"], "name": "D"}, format="json").json()
        self.sku = self.owner.post("/api/v1/skus", {"variant": v["id"], "sku_code": "S1", "price": "100"},
                                   format="json").json()["id"]
        self.pid = p["id"]

    def stock(self, n):
        self.owner.post("/api/v1/inventory/adjust", {"sku": self.sku, "entry_type": "ADJUSTMENT",
                        "quantity_delta": n, "idempotency_key": f"s{n}"}, format="json")

    def order(self, ext="E1", qty=2, code="S1"):
        return {"external_order_id": ext, "customer_name": "Ravi", "items": [
            {"sku_code": code, "quantity": qty, "unit_price": "120.00"}]}

    def test_import_creates_order_and_reserves_stock(self):
        self.stock(10)
        order, created = import_order(self.conn, self.order())
        self.assertTrue(created)
        self.assertEqual(order.status, OrderStatus.IMPORTED)
        self.assertEqual(order.channel_connection_id, self.conn.id)
        self.assertEqual(order.total_amount, 240)
        bal = InventoryBalance.objects.get(sku_id=self.sku)
        self.assertEqual((bal.on_hand, bal.reserved), (10, 2))

    def test_same_external_order_is_not_duplicated(self):
        self.stock(10)
        import_order(self.conn, self.order())
        order, created = import_order(self.conn, self.order())
        self.assertFalse(created)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(InventoryBalance.objects.get(sku_id=self.sku).reserved, 2)

    def test_unknown_sku_rejected(self):
        with self.assertRaises(OrderError) as cm:
            import_order(self.conn, self.order(code="NOPE"))
        self.assertIn("NOPE", str(cm.exception))
        self.assertEqual(Order.objects.count(), 0)

    def test_not_enough_stock_rolls_back(self):
        self.stock(1)
        with self.assertRaises(OrderError):
            import_order(self.conn, self.order(qty=2))
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(InventoryBalance.objects.get(sku_id=self.sku).reserved, 0)

    def test_simulate_endpoint_and_order_list_shows_channel(self):
        self.stock(10)
        r = self.owner.post(f"/api/v1/channels/connections/{self.conn_id}/simulate-order")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["channel"], "DEMO")
        self.assertEqual(r.json()["channel_name"], "Demo store")
        listed = self.owner.get("/api/v1/orders").json()
        rows = listed if isinstance(listed, list) else listed["results"]
        self.assertEqual(rows[0]["channel_name"], "Demo store")

    def test_simulate_without_stock_gives_clear_error(self):
        r = self.owner.post(f"/api/v1/channels/connections/{self.conn_id}/simulate-order")
        self.assertEqual(r.status_code, 400)  # SKU hai par stock 0 -> reserve fail
        self.assertTrue(r.json()["error"])

    def test_simulate_only_for_demo_and_roles_and_tenants(self):
        self.stock(5)
        url = f"/api/v1/channels/connections/{self.conn_id}/simulate-order"
        self.assertEqual(self.viewer.post(url).status_code, 403)
        self.assertEqual(self.other.post(url).status_code, 404)

    def test_manual_orders_have_no_channel(self):
        self.stock(5)
        r = self.owner.post("/api/v1/orders", {"customer_name": "X", "items": [{"sku": self.sku, "quantity": 1}]},
                            format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.json()["channel"])

    def test_imported_order_triggers_stock_sync_to_published_channel(self):
        self.stock(10)
        self.owner.post("/api/v1/channels/publish", {"product": self.pid, "connection": self.conn_id}, format="json")
        run_due()
        SyncJob.objects.all().delete()
        with self.captureOnCommitCallbacks(execute=True):
            import_order(self.conn, self.order())
        self.assertTrue(SyncJob.objects.filter(job_type="UPDATE_INVENTORY").exists())

    def test_demo_generator_uses_real_sku(self):
        self.stock(10)
        d = make_demo_order(self.conn, rng=random.Random(1))
        self.assertEqual(d["items"][0]["sku_code"], "S1")
        self.assertTrue(d["external_order_id"].startswith("DEMO-"))


class AutoProcessTests(TestCase):
    setUp = OrderImportTests.setUp
    stock = OrderImportTests.stock
    order = OrderImportTests.order

    def set_level(self, level):
        r = self.owner.post(f"/api/v1/channels/connections/{self.conn_id}/auto-process",
                            {"auto_process": level}, format="json")
        self.assertEqual(r.status_code, 200)
        self.conn.refresh_from_db()

    def test_manual_stays_imported(self):
        self.stock(10)
        o, _ = import_order(self.conn, self.order("A1"))
        self.assertEqual(o.status, OrderStatus.IMPORTED)

    def test_confirm_level(self):
        self.stock(10)
        self.set_level("CONFIRM")
        o, _ = import_order(self.conn, self.order("A2"))
        self.assertEqual(o.status, OrderStatus.CONFIRMED)

    def test_pack_level_never_ships(self):
        self.stock(10)
        self.set_level("PACK")
        o, _ = import_order(self.conn, self.order("A3"))
        self.assertEqual(o.status, OrderStatus.PACKED)

    def test_bad_level_and_permissions(self):
        url = f"/api/v1/channels/connections/{self.conn_id}/auto-process"
        self.assertEqual(self.owner.post(url, {"auto_process": "SHIP"}, format="json").status_code, 400)
        self.assertIn(self.viewer.post(url, {"auto_process": "PACK"}, format="json").status_code, (403, 404))
        self.assertEqual(self.other.post(url, {"auto_process": "PACK"}, format="json").status_code, 404)
