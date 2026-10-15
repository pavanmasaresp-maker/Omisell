class AdapterError(Exception):
    """Marketplace se aaya error, normalized.
    retryable=True    -> baad mein dobara try karna theek (429, timeout, 5xx)
    needs_action=True -> seller ko kuch karna hoga (token galat, permission, data galat)"""

    def __init__(self, message, retryable=False, needs_action=False):
        super().__init__(message)
        self.retryable = retryable
        self.needs_action = needs_action


class MarketplaceAdapter:
    """Har marketplace is contract ko implement karta hai. Core app mein
    marketplace-specific logic kabhi nahi hota."""

    def authenticate(self):
        raise NotImplementedError

    def health_check(self) -> dict:
        raise NotImplementedError

    def validate_product(self, product: dict) -> list:
        raise NotImplementedError

    def create_listing(self, product: dict) -> dict:
        raise NotImplementedError

    def update_listing(self, external_id: str, product: dict) -> dict:
        raise NotImplementedError

    def update_inventory(self, external_id: str, sku_code: str, quantity: int) -> dict:
        raise NotImplementedError

    def update_price(self, external_id: str, sku_code: str, price: str) -> dict:
        raise NotImplementedError

    def fetch_orders(self) -> list:
        """Marketplace ke naye/recent orders, normalized dict list (order_import.py ka format).
        Jo adapter order pull nahi karta wo khali list deta hai."""
        return []

    def fetch_products(self) -> list:
        """Store ke maujooda products: [{external_id, title, description, status, variants:[{sku_code, price, quantity, name}]}].
        Jo adapter ye nahi karta wo khali list deta hai."""
        return []
