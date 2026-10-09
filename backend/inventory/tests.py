from django.test import TestCase
from accounts.testutils import client_for, make_user
from tenants.models import Tenant


class InventoryTests(TestCase):
    def setUp(self):
        t = Tenant.objects.create(name="T")
        self.c = client_for(make_user(t, "o", "OWNER"))
        self.catalog_only = client_for(make_user(t, "c", "CATALOG_MANAGER"))
        self.pid = self.c.post("/api/v1/products", {"title": "Shirt"}, format="json").json()["id"]
        v = self.c.post("/api/v1/variants", {"product": self.pid, "name": "D"}, format="json").json()
        k = self.c.post("/api/v1/skus", {"variant": v["id"], "sku_code": "S1", "price": "10"},
                        format="json").json()
        self.sku = k["id"]

    def adj(self, delta, etype="ADJUSTMENT", key="", client=None):
        return (client or self.c).post("/api/v1/inventory/adjust", {
            "sku": self.sku, "entry_type": etype, "quantity_delta": delta,
            "idempotency_key": key}, format="json")

    def row(self):
        return self.c.get("/api/v1/inventory/").json()["results"][0]

    def test_add_then_sale(self):
        self.assertEqual(self.adj(50).status_code, 201)
        self.assertEqual(self.adj(-5, "SALE").status_code, 201)
        self.assertEqual(self.row()["on_hand"], 45)

    def test_cannot_go_below_zero(self):
        self.adj(10)
        self.assertEqual(self.adj(-20).status_code, 400)
        self.assertEqual(self.row()["on_hand"], 10)

    def test_sign_rules(self):
        self.assertEqual(self.adj(5, "SALE").status_code, 400)
        self.assertEqual(self.adj(0).status_code, 400)

    def test_idempotency_key_prevents_double_count(self):
        self.assertEqual(self.adj(10, key="k1").status_code, 201)
        self.assertEqual(self.adj(10, key="k1").status_code, 200)
        self.assertEqual(self.row()["on_hand"], 10)

    def test_reservation_limited_by_available(self):
        self.adj(10)
        self.assertEqual(self.adj(5, "RESERVATION").status_code, 201)
        self.assertEqual(self.row()["available"], 5)
        self.assertEqual(self.adj(6, "RESERVATION").status_code, 400)

    def test_only_inventory_roles_can_adjust(self):
        self.assertEqual(self.adj(1, client=self.catalog_only).status_code, 403)

    def test_ledger_and_dashboard(self):
        self.adj(3)
        led = self.c.get("/api/v1/inventory/ledger?sku=" + self.sku).json()["results"]
        self.assertEqual(len(led), 1)
        d = self.c.get("/api/v1/dashboard").json()
        self.assertEqual((d["products"], d["skus"], d["total_on_hand"]), (1, 1, 3))
        self.assertEqual(len(d["low_stock"]), 1)

    def test_cannot_delete_product_with_stock_history(self):
        self.adj(3)
        self.assertEqual(self.c.delete("/api/v1/products/" + self.pid).status_code, 409)
