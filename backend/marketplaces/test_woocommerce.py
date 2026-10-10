import unittest
from unittest import mock

from marketplaces.adapters.base import AdapterError
from marketplaces.adapters.woocommerce import WooCommerceAdapter, assert_public_host

ONE = {"id": "p1", "title": "Cap", "description": "Red <cap>", "status": "ACTIVE",
       "skus": [{"sku_code": "CAP-R", "price": "199", "available": 5}]}
TWO = {"id": "p2", "title": "Shirt", "description": "", "status": "DRAFT",
       "skus": [{"sku_code": "S-M", "price": "499", "available": 3},
                {"sku_code": "S-L", "price": "549", "available": -2}]}


def woo():
    return WooCommerceAdapter("shop.example.com", "ck_1:cs_1")


class WooTests(unittest.TestCase):
    def test_simple_product_create(self):
        a, sent = woo(), []
        with mock.patch.object(a, "_request", side_effect=lambda m, p, b=None: (sent.append((m, p, b)), {"id": 77})[1]):
            res = a.create_listing(ONE)
        self.assertEqual(res["external_product_id"], "77")
        m, p, b = sent[0]
        self.assertEqual((m, p, b["type"], b["sku"], b["regular_price"]), ("POST", "/products", "simple", "CAP-R", "199"))
        self.assertEqual((b["manage_stock"], b["stock_quantity"], b["status"]), (True, 5, "publish"))
        self.assertEqual(b["description"], "Red &lt;cap&gt;")

    def test_variable_product_create_batches_variations(self):
        a, sent = woo(), []

        def fake(m, p, b=None):
            sent.append((m, p, b))
            if p.endswith("per_page=100"):
                return []
            return {"id": 9}

        with mock.patch.object(a, "_request", side_effect=fake):
            res = a.create_listing(TWO)
        self.assertEqual(res["external_product_id"], "9")
        self.assertEqual(sent[0][2]["type"], "variable")
        self.assertEqual(sent[0][2]["status"], "draft")
        batch = [s for s in sent if s[1].endswith("/batch")][0][2]
        self.assertEqual([v["sku"] for v in batch["create"]], ["S-M", "S-L"])
        self.assertEqual(batch["create"][1]["stock_quantity"], 0)  # negative -> 0
        self.assertEqual(batch["update"], [])

    def test_variable_update_updates_existing_creates_new(self):
        a, sent = woo(), []

        def fake(m, p, b=None):
            sent.append((m, p, b))
            if p == "/products/9":
                return {"type": "variable"} if m == "GET" else {}
            if p.endswith("per_page=100"):
                return [{"id": 100, "sku": "S-M"}]
            return {}

        with mock.patch.object(a, "_request", side_effect=fake):
            a.update_listing("9", TWO)
        batch = [s for s in sent if s[1].endswith("/batch")][0][2]
        self.assertEqual([v["id"] for v in batch["update"]], [100])
        self.assertEqual([v["sku"] for v in batch["create"]], ["S-L"])

    def test_inventory_simple_and_variation(self):
        a, sent = woo(), []

        def fake(m, p, b=None):
            sent.append((m, p, b))
            if m == "GET" and p == "/products/5":
                return {"type": "simple", "sku": "CAP-R"}
            if m == "GET" and p == "/products/6":
                return {"type": "variable"}
            if m == "GET":
                return [{"id": 61, "sku": "S-M"}]
            return {}

        with mock.patch.object(a, "_request", side_effect=fake):
            a.update_inventory("5", "CAP-R", 11)
            a.update_inventory("6", "S-M", 4)
            a.update_price("6", "S-M", "599")
        puts = [s for s in sent if s[0] == "PUT"]
        self.assertEqual(puts[0][1:], ("/products/5", {"manage_stock": True, "stock_quantity": 11}))
        self.assertEqual(puts[1][1], "/products/6/variations/61")
        self.assertEqual(puts[2][2], {"regular_price": "599"})

    def test_unknown_sku_needs_action(self):
        a = woo()
        with mock.patch.object(a, "_request", return_value={"type": "simple", "sku": "OTHER"}):
            with self.assertRaises(AdapterError) as cm:
                a.update_inventory("5", "CAP-R", 1)
        self.assertTrue(cm.exception.needs_action)

    def test_bad_token_format(self):
        with self.assertRaises(AdapterError) as cm:
            WooCommerceAdapter("shop.example.com", "just-one-part")._request("GET", "/products")
        self.assertTrue(cm.exception.needs_action)

    def test_blocks_private_hosts(self):
        for h in ["127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1", "localhost"]:
            with self.assertRaises(AdapterError, msg=h):
                assert_public_host(h)

    def test_validate_product(self):
        a = woo()
        self.assertEqual(a.validate_product(ONE), [])
        self.assertTrue(a.validate_product({"title": "x", "skus": []}))


if __name__ == "__main__":
    unittest.main()
