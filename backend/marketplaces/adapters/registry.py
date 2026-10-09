from .demo import DemoAdapter
from .shopify import ShopifyAdapter


def get_adapter(connection):
    creds = connection.get_credentials()
    if connection.channel == "SHOPIFY":
        return ShopifyAdapter(connection.shop_domain, creds.get("access_token", ""))
    if connection.channel == "DEMO":
        return DemoAdapter(creds.get("access_token", ""))
    raise ValueError("Unknown channel")
