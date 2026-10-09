from .base import AdapterError, MarketplaceAdapter


class DemoAdapter(MarketplaceAdapter):
    """Bina asli marketplace ke poora flow test karne ke liye. Token 'demo' hona chahiye."""

    def __init__(self, token):
        self.token = token

    def authenticate(self):
        if self.token != "demo":
            raise AdapterError("Demo channel ke liye token 'demo' likho.", needs_action=True)

    def health_check(self):
        self.authenticate()
        return {"shop_name": "Demo Store"}

    def validate_product(self, product):
        errors = []
        if not product.get("title"):
            errors.append("Title zaroori hai.")
        if not product.get("skus"):
            errors.append("Kam se kam ek SKU chahiye.")
        return errors

    def create_listing(self, product):
        return {"external_product_id": "demo-" + str(product["id"])}

    def update_listing(self, external_id, product):
        return {"external_product_id": external_id}

    def update_inventory(self, external_id, sku_code, quantity):
        return {"quantity": quantity}

    def update_price(self, external_id, sku_code, price):
        return {"price": price}
