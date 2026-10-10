import html
import json
import os
import re
import urllib.error
import urllib.request

from .base import AdapterError, MarketplaceAdapter

API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-01")
# Token sirf asli Shopify store ko jaye, kisi aur host ko nahi (SSRF / token leak se bachav).
DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$")
OPTION = "Variant"

PRODUCT_SET = """
mutation($input: ProductSetInput!, $identifier: ProductSetIdentifiers) {
  productSet(input: $input, identifier: $identifier, synchronous: true) {
    product { id variants(first: 100) { nodes { id sku inventoryItem { id } } } }
    userErrors { field message code }
  }
}"""
VARIANTS_Q = """
query($id: ID!) {
  product(id: $id) { id variants(first: 100) { nodes { id sku inventoryItem { id } } } }
}"""
LOCATION_Q = "{ locations(first: 1) { nodes { id } } }"
SET_QTY = """
mutation($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    userErrors { field message code }
  }
}"""
BULK_PRICE = """
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    userErrors { field message code }
  }
}"""


class ShopifyAdapter(MarketplaceAdapter):
    """Shopify Admin GraphQL API. Auth header: X-Shopify-Access-Token.
    Token ko in scopes ki zaroorat hai: read_products, write_products,
    read_inventory, write_inventory, read_locations."""

    def __init__(self, shop_domain, access_token, api_version=API_VERSION):
        self.shop_domain = (shop_domain or "").strip().lower()
        self.access_token = access_token
        self.api_version = api_version
        self._location_id = None

    # ---------- low level ----------
    def _graphql(self, query, variables=None):
        if not DOMAIN_RE.match(self.shop_domain):
            raise AdapterError("Store address 'mystore.myshopify.com' jaisa hona chahiye.",
                               needs_action=True)
        url = f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"
        body = json.dumps({"query": query, "variables": variables or {}}).encode()
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token,
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AdapterError("Shopify token galat hai ya permission nahi hai.",
                                   needs_action=True)
            if e.code == 404:
                raise AdapterError("Shopify store nahi mila. Store address check karo.",
                                   needs_action=True)
            if e.code == 429 or e.code >= 500:
                raise AdapterError(f"Shopify temporary error (HTTP {e.code}).", retryable=True)
            raise AdapterError(f"Shopify error HTTP {e.code}.")
        except (urllib.error.URLError, TimeoutError):
            raise AdapterError("Shopify tak pahunch nahi paaye.", retryable=True)
        except ValueError:
            raise AdapterError("Shopify ka jawab samajh nahi aaya.", retryable=True)
        errors = payload.get("errors")
        if errors:
            text = str(errors)
            if "THROTTLED" in text:
                raise AdapterError("Shopify rate limit. Thodi der baad dobara try hoga.",
                                   retryable=True)
            if "ACCESS_DENIED" in text or "access scope" in text.lower():
                raise AdapterError("Shopify token ko zaroori permission (scope) nahi hai: "
                                   "write_products, write_inventory, read_locations.",
                                   needs_action=True)
            raise AdapterError("Shopify GraphQL error: " + text[:200])
        return payload["data"]

    @staticmethod
    def _check_user_errors(errors):
        if errors:
            msg = "; ".join(e.get("message", "") for e in errors)[:250]
            raise AdapterError("Shopify ne data reject kiya: " + msg, needs_action=True)

    def _location(self):
        if not self._location_id:
            nodes = self._graphql(LOCATION_Q)["locations"]["nodes"]
            if not nodes:
                raise AdapterError("Shopify store mein koi location nahi mili.", needs_action=True)
            self._location_id = nodes[0]["id"]
        return self._location_id

    def _variants_by_sku(self, external_id):
        data = self._graphql(VARIANTS_Q, {"id": external_id})
        if not data.get("product"):
            raise AdapterError("Shopify par ye product nahi mila (shayad delete ho gaya). "
                               "Dobara publish karo.", needs_action=True)
        return {v["sku"]: v for v in data["product"]["variants"]["nodes"]}

    def _set_quantities(self, items):
        """items: [(inventory_item_id, quantity)]"""
        if not items:
            return
        loc = self._location()
        data = self._graphql(SET_QTY, {"input": {
            "name": "available", "reason": "correction", "ignoreCompareQuantity": True,
            "quantities": [{"inventoryItemId": i, "locationId": loc, "quantity": max(int(q), 0)}
                           for i, q in items]}})
        self._check_user_errors(data["inventorySetQuantities"]["userErrors"])

    # ---------- contract ----------
    def authenticate(self):
        self.health_check()

    def health_check(self):
        data = self._graphql("{ shop { name } }")
        return {"shop_name": data["shop"]["name"]}

    def validate_product(self, product):
        errors = []
        if not product.get("title"):
            errors.append("Title zaroori hai.")
        skus = product.get("skus") or []
        if not skus:
            errors.append("Kam se kam ek SKU chahiye.")
        for k in skus:
            try:
                if float(k.get("price", 0)) <= 0:
                    errors.append(f"{k.get('sku_code')}: price 0 se zyada honi chahiye.")
            except (TypeError, ValueError):
                errors.append(f"{k.get('sku_code')}: price galat hai.")
        return errors

    def _product_input(self, product):
        skus = product["skus"]
        desc = "<br>".join(html.escape(l) for l in (product.get("description") or "").splitlines())
        return {
            "title": product["title"],
            "descriptionHtml": desc,
            "vendor": product.get("brand") or "",
            "status": product.get("status") if product.get("status") in ("ACTIVE", "DRAFT", "ARCHIVED") else "DRAFT",
            "productOptions": [{"name": OPTION, "values": [{"name": k["sku_code"]} for k in skus]}],
            "variants": [{"optionValues": [{"optionName": OPTION, "name": k["sku_code"]}],
                          "sku": k["sku_code"], "price": str(k["price"]),
                          "inventoryItem": {"tracked": True}} for k in skus],
        }

    def _push(self, product, identifier=None):
        variables = {"input": self._product_input(product)}
        if identifier:
            variables["identifier"] = {"id": identifier}
        data = self._graphql(PRODUCT_SET, variables)["productSet"]
        self._check_user_errors(data["userErrors"])
        prod = data["product"]
        by_sku = {v["sku"]: v for v in prod["variants"]["nodes"]}
        self._set_quantities([(by_sku[k["sku_code"]]["inventoryItem"]["id"], k.get("available", 0))
                              for k in product["skus"] if k["sku_code"] in by_sku])
        return {"external_product_id": prod["id"]}

    def create_listing(self, product):
        return self._push(product)

    def update_listing(self, external_id, product):
        return self._push(product, identifier=external_id)

    def update_inventory(self, external_id, sku_code, quantity):
        v = self._variants_by_sku(external_id).get(sku_code)
        if not v:
            raise AdapterError(f"Shopify par SKU {sku_code} nahi mila. Product dobara publish karo.",
                               needs_action=True)
        self._set_quantities([(v["inventoryItem"]["id"], quantity)])
        return {"quantity": quantity}

    def update_price(self, external_id, sku_code, price):
        v = self._variants_by_sku(external_id).get(sku_code)
        if not v:
            raise AdapterError(f"Shopify par SKU {sku_code} nahi mila.", needs_action=True)
        data = self._graphql(BULK_PRICE, {"productId": external_id,
                                          "variants": [{"id": v["id"], "price": str(price)}]})
        self._check_user_errors(data["productVariantsBulkUpdate"]["userErrors"])
        return {"price": str(price)}
