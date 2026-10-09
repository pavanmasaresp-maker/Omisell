from django.test import TestCase
from accounts.testutils import client_for, make_user
from tenants.models import Tenant


class OrderTests(TestCase):
    def setUp(self):
        t = Tenant.objects.create(name="T")
        self.c = client_for(make_user(t, "owner", "OWNER"))
        pid = self.c.post("/api/v1/products", {"title": "Shirt"}, format="json").json()["id"]
        v = self.c.post("/api/v1/variants", {"product": pid, "name": "D"}, format="json").json()
        k = self.c.post("/api/v1/skus", {"variant": v["id"], "sku_code": "S1", "price": "100"},
                        format="json").json()
        self.sku = k["id"]
        # stock in
        self.c.post("/api/v1/inventory/adjust",
                    {"sku": self.sku, "entry_type": "ADJUSTMENT", "quantity_delta": 20},
                    format="json")

    def create_order(self, qty=2):
        return self.c.post("/api/v1/orders", {
            "customer_name": "Asha", "items": [{"sku": self.sku, "quantity": qty}],
        }, format="json")

    def balance(self):
        return self.c.get("/api/v1/inventory/").json()["results"][0]

    def test_create_reserves_stock(self):
        r = self.create_order(5)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "IMPORTED")
        bal = self.balance()
        self.assertEqual(bal["on_hand"], 20)
        self.assertEqual(bal["reserved"], 5)
        self.assertEqual(bal["available"], 15)

    def test_cannot_oversell(self):
        r = self.create_order(50)
        self.assertEqual(r.status_code, 400)

    def test_full_happy_path_ships_and_decrements(self):
        oid = self.create_order(3).json()["id"]
        self.c.post(f"/api/v1/orders/{oid}/confirm")
        self.c.post(f"/api/v1/orders/{oid}/pack")
        r = self.c.post(f"/api/v1/orders/{oid}/ship", {"carrier": "BlueDart"}, format="json")
        self.assertEqual(r.json()["status"], "SHIPPED")
        bal = self.balance()
        self.assertEqual(bal["on_hand"], 17)
        self.assertEqual(bal["reserved"], 0)

    def test_cancel_releases_reservation(self):
        oid = self.create_order(4).json()["id"]
        r = self.c.post(f"/api/v1/orders/{oid}/cancel", {"reason": "customer request"}, format="json")
        self.assertEqual(r.json()["status"], "CANCELLED")
        bal = self.balance()
        self.assertEqual(bal["on_hand"], 20)
        self.assertEqual(bal["reserved"], 0)

    def test_cannot_ship_before_pack(self):
        oid = self.create_order(1).json()["id"]
        self.c.post(f"/api/v1/orders/{oid}/confirm")
        r = self.c.post(f"/api/v1/orders/{oid}/ship")
        self.assertEqual(r.status_code, 400)

    def test_return_flow_restocks(self):
        oid = self.create_order(2).json()["id"]
        self.c.post(f"/api/v1/orders/{oid}/confirm")
        self.c.post(f"/api/v1/orders/{oid}/pack")
        self.c.post(f"/api/v1/orders/{oid}/ship")
        self.c.post(f"/api/v1/orders/{oid}/deliver")
        item_id = self.c.get(f"/api/v1/orders/{oid}").json()["items"][0]["id"]
        rr = self.c.post("/api/v1/orders/returns", {
            "order_item": item_id, "quantity": 1, "reason": "damaged"}, format="json").json()
        self.c.post(f"/api/v1/orders/returns/{rr['id']}/decide", {"approve": True}, format="json")
        self.assertEqual(self.balance()["on_hand"], 19)

    def test_idempotency_key_prevents_duplicate_order(self):
        body = {"customer_name": "Asha", "items": [{"sku": self.sku, "quantity": 1}],
               "idempotency_key": "ext-123"}
        r1 = self.c.post("/api/v1/orders", body, format="json")
        r2 = self.c.post("/api/v1/orders", body, format="json")
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(self.balance()["reserved"], 1)
