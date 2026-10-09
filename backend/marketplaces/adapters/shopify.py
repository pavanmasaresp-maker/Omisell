import json
import os
import urllib.error
import urllib.request

from .base import AdapterError, MarketplaceAdapter

API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-01")


class ShopifyAdapter(MarketplaceAdapter):
    """Shopify Admin GraphQL API. Auth header: X-Shopify-Access-Token."""

    def __init__(self, shop_domain, access_token, api_version=API_VERSION):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version

    def _graphql(self, query, variables=None):
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
            if e.code == 429 or e.code >= 500:
                raise AdapterError(f"Shopify temporary error (HTTP {e.code}).", retryable=True)
            raise AdapterError(f"Shopify error HTTP {e.code}.")
        except (urllib.error.URLError, TimeoutError):
            raise AdapterError("Shopify tak pahunch nahi paaye.", retryable=True)
        if payload.get("errors"):
            raise AdapterError("Shopify GraphQL error: " + str(payload["errors"])[:200])
        return payload["data"]

    def authenticate(self):
        self.health_check()

    def health_check(self):
        data = self._graphql("{ shop { name } }")
        return {"shop_name": data["shop"]["name"]}
