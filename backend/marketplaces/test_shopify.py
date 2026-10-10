"""Shopify adapter tests. Asli Shopify ko call nahi hota: _graphql mock hota hai."""
import unittest
from unittest import mock

from marketplaces.adapters.base import AdapterError
from marketplaces.adapters.shopify import ShopifyAdapter

PRODUCT = {"id": "p1", "title": "Cotton shirt", "description": "Soft <b>cotton</b>\nWashable",
           "brand": "OmniWear", "status": "ACTIVE",
           "skus": [{"id": "s1", "sku_code": "SHIRT-M", "price": "499.00", "available": 7},
                    {"id": "s2", "sku_code": "SHIRT-L", "price": "549.00", "available": 0}]}
VARIANTS = {"nodes": [{"id": "gid://v/1", "sku": "SHIRT-M", "inventoryItem": {"id": "gid://i/1"}},
                      {"id": "gid://v/2", "sku": "SHIRT-L", "inventoryItem": {"id": "gid://i/2"}}]}


def adapter():
    return ShopifyAdapter("mystore.myshopify.com", "tok")


class ShopifyAdapterTests(unittest.TestCase):
    def test_create_listing_sets_stock(self):
        a = adapter()
        calls = []

        def fake(query, variables=None):
            calls.append((query, variables))
            if "productSet" in query:
                return {"productSet": {"product": {"id": "gid://p/9", "variants": VARIANTS}, "userErrors": []}}
            if "locations" in query:
                return {"locations": {"nodes": [{"id": "gid://loc/1"}]}}
            return {"inventorySetQuantities": {"userErrors": []}}

        with mock.patch.object(a, "_graphql", side_effect=fake):
            res = a.create_listing(PRODUCT)
        self.assertEqual(res["external_product_id"], "gid://p/9")
        pset = calls[0][1]
        self.assertNotIn("identifier", pset)
        self.assertEqual(pset["input"]["variants"][0]["price"], "499.00")
        self.assertEqual(pset["input"]["descriptionHtml"], "Soft &lt;b&gt;cotton&lt;/b&gt;<br>Washable")
        qty = calls[-1][1]["input"]["quantities"]
        self.assertEqual([(q["inventoryItemId"], q["quantity"]) for q in qty],
                         [("gid://i/1", 7), ("gid://i/2", 0)])
        self.assertTrue(calls[-1][1]["input"]["ignoreCompareQuantity"])

    def test_update_listing_uses_identifier(self):
        a = adapter()
        seen = {}

        def fake(query, variables=None):
            if "productSet" in query:
                seen.update(variables)
                return {"productSet": {"product": {"id": "gid://p/9", "variants": VARIANTS}, "userErrors": []}}
            if "locations" in query:
                return {"locations": {"nodes": [{"id": "L"}]}}
            return {"inventorySetQuantities": {"userErrors": []}}

        with mock.patch.object(a, "_graphql", side_effect=fake):
            a.update_listing("gid://p/9", PRODUCT)
        self.assertEqual(seen["identifier"], {"id": "gid://p/9"})

    def test_user_errors_need_action(self):
        a = adapter()
        bad = {"productSet": {"product": None, "userErrors": [{"message": "Title is too long"}]}}
        with mock.patch.object(a, "_graphql", return_value=bad):
            with self.assertRaises(AdapterError) as cm:
                a.create_listing(PRODUCT)
        self.assertTrue(cm.exception.needs_action)
        self.assertIn("Title is too long", str(cm.exception))

    def test_update_inventory_finds_sku(self):
        a = adapter()
        sent = {}

        def fake(query, variables=None):
            if "product(id" in query:
                return {"product": {"id": "gid://p/9", "variants": VARIANTS}}
            if "locations" in query:
                return {"locations": {"nodes": [{"id": "L"}]}}
            sent.update(variables)
            return {"inventorySetQuantities": {"userErrors": []}}

        with mock.patch.object(a, "_graphql", side_effect=fake):
            a.update_inventory("gid://p/9", "SHIRT-L", 12)
        self.assertEqual(sent["input"]["quantities"][0],
                         {"inventoryItemId": "gid://i/2", "locationId": "L", "quantity": 12})

    def test_negative_stock_sent_as_zero(self):
        a = adapter()
        sent = {}

        def fake(query, variables=None):
            if "product(id" in query:
                return {"product": {"id": "x", "variants": VARIANTS}}
            if "locations" in query:
                return {"locations": {"nodes": [{"id": "L"}]}}
            sent.update(variables)
            return {"inventorySetQuantities": {"userErrors": []}}

        with mock.patch.object(a, "_graphql", side_effect=fake):
            a.update_inventory("x", "SHIRT-M", -3)
        self.assertEqual(sent["input"]["quantities"][0]["quantity"], 0)

    def test_unknown_sku_or_deleted_product_needs_action(self):
        a = adapter()
        with mock.patch.object(a, "_graphql", return_value={"product": {"id": "x", "variants": VARIANTS}}):
            with self.assertRaises(AdapterError) as cm:
                a.update_inventory("x", "NOPE", 1)
        self.assertTrue(cm.exception.needs_action)
        with mock.patch.object(a, "_graphql", return_value={"product": None}):
            with self.assertRaises(AdapterError) as cm:
                a.update_inventory("x", "SHIRT-M", 1)
        self.assertTrue(cm.exception.needs_action)

    def test_update_price(self):
        a = adapter()
        sent = {}

        def fake(query, variables=None):
            if "product(id" in query:
                return {"product": {"id": "x", "variants": VARIANTS}}
            sent.update(variables)
            return {"productVariantsBulkUpdate": {"userErrors": []}}

        with mock.patch.object(a, "_graphql", side_effect=fake):
            a.update_price("x", "SHIRT-M", "599.00")
        self.assertEqual(sent["variants"], [{"id": "gid://v/1", "price": "599.00"}])

    def test_validate_product(self):
        a = adapter()
        self.assertEqual(a.validate_product(PRODUCT), [])
        self.assertTrue(a.validate_product({"title": "", "skus": []}))
        zero = {"title": "T", "skus": [{"sku_code": "A", "price": "0"}]}
        self.assertIn("price", a.validate_product(zero)[0])

    def test_rejects_non_shopify_domain(self):
        for d in ["evil.com", "mystore.myshopify.com.evil.com", "http://x.myshopify.com", ""]:
            with self.assertRaises(AdapterError) as cm:
                ShopifyAdapter(d, "tok")._graphql("{ shop { name } }")
            self.assertTrue(cm.exception.needs_action)

    def test_throttle_is_retryable(self):
        import io, json
        a = adapter()
        body = json.dumps({"errors": [{"extensions": {"code": "THROTTLED"}}]}).encode()
        resp = mock.MagicMock(); resp.__enter__.return_value = io.BytesIO(body)
        with mock.patch("urllib.request.urlopen", return_value=resp):
            with self.assertRaises(AdapterError) as cm:
                a._graphql("{ shop { name } }")
        self.assertTrue(cm.exception.retryable)


if __name__ == "__main__":
    unittest.main()
