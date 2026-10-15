import unittest
from unittest import mock

from marketplaces.adapters.shopify import ShopifyAdapter
from marketplaces.adapters.woocommerce import WooCommerceAdapter

SHOPIFY = {"orders": {"nodes": [
    {"id": "gid://shopify/Order/1", "name": "#1001", "cancelledAt": None, "phone": "+91999",
     "shippingAddress": {"name": "Asha", "phone": None, "address1": "1 Road", "city": "Pune", "zip": "411001"},
     "lineItems": {"nodes": [{"sku": "CAP-R", "quantity": 2,
                              "originalUnitPriceSet": {"shopMoney": {"amount": "199.00"}}}]}},
    {"id": "gid://shopify/Order/2", "name": "#1002", "cancelledAt": "2026-01-01", "phone": None,
     "shippingAddress": None, "lineItems": {"nodes": []}}]}}

WOO = [{"id": 55, "number": "55", "shipping": {"first_name": "Ravi", "last_name": "S", "city": "Surat"},
        "billing": {"phone": "98765"}, "line_items": [{"sku": "S-M", "quantity": 1, "price": 499}]}]


class FetchOrdersTests(unittest.TestCase):
    def test_shopify_normalizes_and_skips_cancelled(self):
        a = ShopifyAdapter("shop.myshopify.com", "t")
        with mock.patch.object(a, "_graphql", return_value=SHOPIFY):
            out = a.fetch_orders()
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual((o["external_order_id"], o["customer_name"], o["customer_phone"]), ("1001", "Asha", "+91999"))
        self.assertEqual(o["items"], [{"sku_code": "CAP-R", "quantity": 2, "unit_price": "199.00"}])
        self.assertEqual(o["shipping_address"]["city"], "Pune")

    def test_woo_normalizes(self):
        a = WooCommerceAdapter("shop.example.com", "ck:cs")
        with mock.patch.object(a, "_request", return_value=WOO):
            out = a.fetch_orders()
        self.assertEqual(out[0]["external_order_id"], "55")
        self.assertEqual(out[0]["customer_name"], "Ravi S")
        self.assertEqual(out[0]["items"], [{"sku_code": "S-M", "quantity": 1, "unit_price": "499"}])
        self.assertEqual(out[0]["customer_phone"], "98765")


class FetchProductsTests(unittest.TestCase):
    def test_shopify_pages_and_normalizes(self):
        a = ShopifyAdapter("s.myshopify.com", "shpat_x")
        pages = [{"products": {"pageInfo": {"hasNextPage": True, "endCursor": "c1"}, "nodes": [
                    {"id": "gid://shopify/Product/11", "title": "Cap", "description": "d", "status": "DRAFT",
                     "variants": {"nodes": [{"sku": "CAP-R", "title": "Red", "price": "199.00", "inventoryQuantity": 5}]}}]}},
                 {"products": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [
                    {"id": "gid://shopify/Product/12", "title": "Tee", "description": "", "status": "ACTIVE",
                     "variants": {"nodes": [{"sku": "", "title": "M", "price": "1", "inventoryQuantity": None}]}}]}}]
        with mock.patch.object(a, "_graphql", side_effect=pages) as g:
            out = a.fetch_products()
        self.assertEqual([p["external_id"] for p in out], ["11", "12"])
        self.assertEqual(out[0]["status"], "DRAFT")
        self.assertEqual(out[0]["variants"][0], {"sku_code": "CAP-R", "name": "Red", "price": "199.00", "quantity": 5})
        self.assertEqual(g.call_args_list[1][0][1]["after"], "c1")
        self.assertEqual(out[1]["variants"][0]["quantity"], 0)

    def test_woo_simple_and_variable(self):
        a = WooCommerceAdapter("s.com", "k:s")
        def req(method, path, body=None):
            if path.startswith("/products?"):
                return [{"id": 1, "name": "Mug", "type": "simple", "sku": "MUG", "regular_price": "99", "stock_quantity": 4, "status": "publish"},
                        {"id": 2, "name": "Shirt", "type": "variable", "status": "draft"}]
            return [{"sku": "SH-S", "regular_price": "300", "stock_quantity": 2}]
        with mock.patch.object(a, "_request", side_effect=req):
            out = a.fetch_products()
        self.assertEqual(out[0]["status"], "ACTIVE")
        self.assertEqual(out[0]["variants"][0]["quantity"], 4)
        self.assertEqual(out[1]["variants"][0]["sku_code"], "SH-S")
        self.assertEqual(out[1]["status"], "DRAFT")
