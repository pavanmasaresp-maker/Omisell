from .demo import DemoAdapter
from .shopify import ShopifyAdapter
from .woocommerce import WooCommerceAdapter


def get_adapter(connection):
    creds = connection.get_credentials()
    token = creds.get("access_token", "")
    if connection.channel == "SHOPIFY":
        return ShopifyAdapter(connection.shop_domain, token)
    if connection.channel == "WOOCOMMERCE":
        return WooCommerceAdapter(connection.shop_domain, token)
    if connection.channel == "DEMO":
        return DemoAdapter(token)
    raise ValueError("Unknown channel")
