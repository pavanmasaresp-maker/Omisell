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
