import base64
import html
import ipaddress
import json
import socket
import urllib.error
import urllib.request

from .base import AdapterError, MarketplaceAdapter

ATTR = "Variant"
STATUS_MAP = {"ACTIVE": "publish", "DRAFT": "draft", "ARCHIVED": "private"}


def assert_public_host(host):
    """SSRF se bachav: server ko kabhi private / internal address par request nahi bhejni."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise AdapterError("Store address nahi mila. Spelling check karo.", needs_action=True)
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise AdapterError("Ye store address allowed nahi hai.", needs_action=True)


class WooCommerceAdapter(MarketplaceAdapter):
    """WooCommerce REST API v3 (HTTPS + Basic auth).
    Token format: consumer_key:consumer_secret (WooCommerce > Settings > Advanced > REST API,
    permission: Read/Write)."""

    def __init__(self, shop_domain, token):
        self.host = (shop_domain or "").strip().lower()
        key, _, secret = (token or "").partition(":")
        self.key, self.secret = key.strip(), secret.strip()

    # ---------- low level ----------
    def _request(self, method, path, body=None):
        if not self.key or not self.secret:
            raise AdapterError("Token 'consumer_key:consumer_secret' format mein daalo.",
                               needs_action=True)
        assert_public_host(self.host)
        url = f"https://{self.host}/wp-json/wc/v3{path}"
        auth = base64.b64encode(f"{self.key}:{self.secret}".encode()).decode()
        req = urllib.request.Request(
            url, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            msg = ""
            try:
                msg = json.load(e).get("message", "")
            except Exception:
                pass
            if e.code in (401, 403):
                raise AdapterError("WooCommerce key galat hai ya Read/Write permission nahi hai.",
                                   needs_action=True)
            if e.code == 404:
                raise AdapterError("WooCommerce REST API nahi mili. Site WooCommerce hai aur "
                                   "permalinks ON hain?", needs_action=True)
            if e.code in (408, 429) or e.code >= 500:
                raise AdapterError(f"WooCommerce temporary error (HTTP {e.code}).", retryable=True)
            raise AdapterError("WooCommerce ne data reject kiya: " + (msg or f"HTTP {e.code}")[:200],
                               needs_action=True)
        except (urllib.error.URLError, TimeoutError):
            raise AdapterError("WooCommerce site tak pahunch nahi paaye.", retryable=True)
        except ValueError:
            raise AdapterError("WooCommerce ka jawab samajh nahi aaya.", retryable=True)

    # ---------- contract ----------
    def authenticate(self):
        self.health_check()

    def health_check(self):
        self._request("GET", "/products?per_page=1")
        return {"shop_name": self.host}

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

    @staticmethod
    def _stock(k):
        return {"manage_stock": True, "stock_quantity": max(int(k.get("available", 0)), 0)}

    def _base(self, product):
        desc = "<br>".join(html.escape(l) for l in (product.get("description") or "").splitlines())
        return {"name": product["title"], "description": desc,
                "status": STATUS_MAP.get(product.get("status"), "draft")}

    def _variations(self, pid):
        return {v["sku"]: v for v in self._request("GET", f"/products/{pid}/variations?per_page=100")}

    def _sync_variations(self, pid, skus):
        existing = self._variations(pid)
        create, update = [], []
        for k in skus:
            data = {"sku": k["sku_code"], "regular_price": str(k["price"]), **self._stock(k),
                    "attributes": [{"name": ATTR, "option": k["sku_code"]}]}
            if k["sku_code"] in existing:
                data["id"] = existing[k["sku_code"]]["id"]
                update.append(data)
            else:
                create.append(data)
        self._request("POST", f"/products/{pid}/variations/batch", {"create": create, "update": update})

    def create_listing(self, product):
        skus = product["skus"]
        if len(skus) == 1:
            k = skus[0]
            res = self._request("POST", "/products", {
                **self._base(product), "type": "simple", "sku": k["sku_code"],
                "regular_price": str(k["price"]), **self._stock(k)})
            return {"external_product_id": str(res["id"])}
        res = self._request("POST", "/products", {
            **self._base(product), "type": "variable",
            "attributes": [{"name": ATTR, "visible": True, "variation": True,
                            "options": [k["sku_code"] for k in skus]}]})
        self._sync_variations(res["id"], skus)
        return {"external_product_id": str(res["id"])}

    def update_listing(self, external_id, product):
        skus = product["skus"]
        cur = self._request("GET", f"/products/{external_id}")
        if cur.get("type") == "variable":
            self._request("PUT", f"/products/{external_id}", {
                **self._base(product),
                "attributes": [{"name": ATTR, "visible": True, "variation": True,
                                "options": [k["sku_code"] for k in skus]}]})
            self._sync_variations(external_id, skus)
        else:
            k = skus[0]
            self._request("PUT", f"/products/{external_id}", {
                **self._base(product), "sku": k["sku_code"],
                "regular_price": str(k["price"]), **self._stock(k)})
        return {"external_product_id": str(external_id)}

    def _locate(self, external_id, sku_code):
        """Return (path, product_dict) jis par stock/price likhna hai."""
        cur = self._request("GET", f"/products/{external_id}")
        if cur.get("type") == "variable":
            v = self._variations(external_id).get(sku_code)
            if not v:
                raise AdapterError(f"WooCommerce par SKU {sku_code} nahi mila. "
                                   "Product dobara publish karo.", needs_action=True)
            return f"/products/{external_id}/variations/{v['id']}"
        if cur.get("sku") != sku_code:
            raise AdapterError(f"WooCommerce par SKU {sku_code} nahi mila. "
                               "Product dobara publish karo.", needs_action=True)
        return f"/products/{external_id}"

    def update_inventory(self, external_id, sku_code, quantity):
        path = self._locate(external_id, sku_code)
        self._request("PUT", path, {"manage_stock": True, "stock_quantity": max(int(quantity), 0)})
        return {"quantity": quantity}

    def update_price(self, external_id, sku_code, price):
        path = self._locate(external_id, sku_code)
        self._request("PUT", path, {"regular_price": str(price)})
        return {"price": str(price)}
