"""Flipkart adapter: mock HTTP par test (asli Flipkart par nahi). Django ki zaroorat nahi."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from marketplaces.adapters.base import AdapterError  # noqa: E402
from marketplaces.adapters.flipkart import FlipkartAdapter  # noqa: E402


class Fake(FlipkartAdapter):
    def __init__(self, token="app:sec", listed=("CH-1",), locs=("LOC1",)):
        super().__init__("", token)
        self.calls, self.listed, self.locs = [], listed, locs

    def _http(self, method, url, body=None, headers=None):
        self.calls.append((method, url.replace("https://api.flipkart.net", ""), body, headers))
        if "oauth" in url:
            return {"access_token": "T", "expires_in": 3600}
        if url.endswith("/listings/v3/details"):
            return {"available": {s: {"listing_id": "L", "product_id": "MOBXXXXXXXXXXXX",
                                       "locations": [{"id": l} for l in self.locs]}
                                  for s in body["sku_ids"] if s in self.listed}}
        if url.endswith("/listings/v3/update/inventory"):
            return {s: {"status": "SUCCESS"} for s in body}
        if url.endswith("/shipments/filter/"):
            return {"hasMore": False, "shipments": [
                {"shipmentId": "S1", "orderItems": [
                    {"orderId": "OD1", "sku": "CH-1", "quantity": 2, "priceComponents": {"sellingPrice": 499}},
                    {"orderId": "OD1", "sku": "CH-2", "quantity": 1, "priceComponents": {"sellingPrice": 99}}]},
                {"shipmentId": "S2", "orderItems": [{"orderId": "OD2", "sku": "CH-1", "quantity": 1}]}]}
        raise AssertionError(url)


class FlipkartTests(unittest.TestCase):
    def test_token_format_and_health(self):
        with self.assertRaises(AdapterError) as c:
            FlipkartAdapter("", "justone").health_check()
        self.assertTrue(c.exception.needs_action)
        a = Fake(); a.health_check()
        self.assertEqual(a.calls[0][3]["Authorization"].split()[0], "Basic")
        self.assertIn("client_credentials", a.calls[0][1])

    def test_token_cached(self):
        a = Fake(); a.health_check(); a.health_check()
        self.assertEqual(len([c for c in a.calls if "oauth" in c[1]]), 1)

    def test_orders_grouped_by_order_id(self):
        o = {x["external_order_id"]: x for x in Fake().fetch_orders()}
        self.assertEqual(set(o), {"OD1", "OD2"})
        self.assertEqual(len(o["OD1"]["items"]), 2)
        self.assertEqual(o["OD1"]["items"][0], {"sku_code": "CH-1", "quantity": 2, "unit_price": "499"})
        self.assertNotIn("unit_price", o["OD2"]["items"][0])

    def test_inventory_uses_listing_product_id_and_location(self):
        a = Fake(); a.update_inventory("x", "CH-1", 7)
        body = [c for c in a.calls if c[1].endswith("update/inventory")][0][2]
        self.assertEqual(body, {"CH-1": {"product_id": "MOBXXXXXXXXXXXX",
                                         "locations": [{"id": "LOC1", "inventory": 7}]}})
        a.update_inventory("x", "CH-1", -3)
        self.assertEqual([c for c in a.calls if c[1].endswith("update/inventory")][-1][2]["CH-1"]["locations"][0]["inventory"], 0)

    def test_unlisted_sku_needs_action(self):
        with self.assertRaises(AdapterError) as c:
            Fake().update_inventory("x", "NOPE", 1)
        self.assertTrue(c.exception.needs_action)
        self.assertIn("NOPE", str(c.exception))

    def test_publish_links_existing_listing_and_pushes_stock(self):
        a = Fake()
        r = a.create_listing({"title": "T", "skus": [{"sku_code": "CH-1", "available": 5}]})
        self.assertEqual(r["external_product_id"], "MOBXXXXXXXXXXXX")
        self.assertTrue(any(c[1].endswith("update/inventory") for c in a.calls))
        with self.assertRaises(AdapterError):
            Fake(listed=()).create_listing({"title": "T", "skus": [{"sku_code": "CH-1", "available": 5}]})

    def test_next_page_path_has_no_double_sellers(self):
        a = Fake(); pages = []
        def http(method, url, body=None, headers=None):
            pages.append((method, url))
            if "oauth" in url:
                return {"access_token": "T"}
            if len(pages) < 4:
                return {"hasMore": True, "nextPageUrl": "/sellers/v3/shipments/filter?next=abc", "shipments": []}
            return {"hasMore": False, "shipments": []}
        a._http = http; a.fetch_orders()
        self.assertTrue(all("/sellers/sellers" not in u for _, u in pages))
        self.assertIn("https://api.flipkart.net/sellers/v3/shipments/filter?next=abc", [u for _, u in pages])

    def test_batches_of_ten(self):
        a = Fake(listed=tuple(f"S{i}" for i in range(25)))
        a._push_inventory([(f"S{i}", 1) for i in range(25)])
        self.assertEqual(len([c for c in a.calls if c[1].endswith("update/inventory")]), 3)

    def test_per_sku_failure_reported(self):
        a = Fake()
        a._http_orig = a._http
        def bad(method, url, body=None, headers=None):
            if url.endswith("update/inventory"):
                return {"CH-1": {"status": "FAILURE", "errors": [{"description": "x"}]}}
            return a._http_orig(method, url, body, headers)
        a._http = bad
        with self.assertRaises(AdapterError):
            a.update_inventory("x", "CH-1", 1)


if __name__ == "__main__":
    unittest.main()
