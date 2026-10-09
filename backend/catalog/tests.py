from django.test import TestCase
from accounts.testutils import client_for, make_user
from tenants.models import Tenant


class CatalogTests(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="T1")
        self.t2 = Tenant.objects.create(name="T2")
        self.c1 = client_for(make_user(self.t1, "o1", "OWNER"))
        self.c2 = client_for(make_user(self.t2, "o2", "OWNER"))
        self.cv = client_for(make_user(self.t1, "v1", "VIEWER"))

    def product(self, title="Shirt"):
        return self.c1.post("/api/v1/products", {"title": title}, format="json").json()

    def test_viewer_cannot_write_but_can_read(self):
        self.assertEqual(self.cv.post("/api/v1/products", {"title": "X"}, format="json").status_code, 403)
        self.product()
        self.assertEqual(self.cv.get("/api/v1/products").status_code, 200)

    def test_tenant_isolation(self):
        p = self.product()
        self.assertEqual(self.c2.get("/api/v1/products").json()["results"], [])
        self.assertEqual(self.c2.get("/api/v1/products/" + p["id"]).status_code, 404)
        r = self.c2.post("/api/v1/variants", {"product": p["id"], "name": "D"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_duplicate_sku_code_rejected_within_tenant(self):
        p = self.product()
        v = self.c1.post("/api/v1/variants", {"product": p["id"], "name": "D"}, format="json").json()
        body = {"variant": v["id"], "sku_code": "S1", "price": "10"}
        self.assertEqual(self.c1.post("/api/v1/skus", body, format="json").status_code, 201)
        self.assertEqual(self.c1.post("/api/v1/skus", body, format="json").status_code, 400)

    def test_search_edit_and_delete(self):
        p = self.product("Blue Shirt")
        self.product("Red Cap")
        r = self.c1.get("/api/v1/products?search=shirt").json()["results"]
        self.assertEqual(len(r), 1)
        r = self.c1.patch("/api/v1/products/" + p["id"], {"status": "ACTIVE"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["version"], 2)
        self.assertEqual(self.c1.delete("/api/v1/products/" + p["id"]).status_code, 204)
