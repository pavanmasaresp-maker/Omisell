import io

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

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


class BulkImportTests(TestCase):
    def setUp(self):
        self.t = Tenant.objects.create(name="T")
        self.c = client_for(make_user(self.t, "owner", "OWNER"))
        self.cv = client_for(make_user(self.t, "viewer", "VIEWER"))

    def csv_file(self, text):
        return SimpleUploadedFile("products.csv", text.encode("utf-8"), content_type="text/csv")

    def test_happy_path_creates_products_and_stock(self):
        csv_text = "title,sku_code,price,stock\nShirt,SH-1,499,20\nCap,CP-1,199,5\n"
        r = self.c.post("/api/v1/products/bulk-import", {"file": self.csv_file(csv_text)})
        body = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(body["created"], 2)
        self.assertEqual(body["skipped"], 0)
        bal = self.c.get("/api/v1/inventory/").json()["results"]
        self.assertEqual(sum(b["on_hand"] for b in bal), 25)

    def test_duplicate_sku_skipped_rest_still_imported(self):
        self.c.post("/api/v1/products/bulk-import", {
            "file": self.csv_file("title,sku_code,price\nShirt,SH-1,499\n")})
        r = self.c.post("/api/v1/products/bulk-import", {
            "file": self.csv_file("title,sku_code,price\nShirt Again,SH-1,500\nCap,CP-1,199\n")})
        body = r.json()
        self.assertEqual(body["created"], 1)
        self.assertEqual(body["skipped"], 1)

    def test_missing_columns_rejected(self):
        r = self.c.post("/api/v1/products/bulk-import", {
            "file": self.csv_file("title,price\nShirt,499\n")})
        self.assertEqual(r.status_code, 400)

    def test_viewer_cannot_bulk_import(self):
        r = self.cv.post("/api/v1/products/bulk-import", {
            "file": self.csv_file("title,sku_code,price\nShirt,SH-1,499\n")})
        self.assertEqual(r.status_code, 403)
