from .base import MarketplaceAdapter


class FileAdapter(MarketplaceAdapter):
    """CSV channel: marketplace ki order file app se import hoti hai. Koi API / token nahi."""

    def __init__(self, token=""):
        pass

    def authenticate(self):
        return None

    def health_check(self):
        return {"shop_name": "CSV file"}

    def validate_product(self, product):
        return ["CSV channel par product publish nahi hota. Wahan listing aap khud banate ho."]
