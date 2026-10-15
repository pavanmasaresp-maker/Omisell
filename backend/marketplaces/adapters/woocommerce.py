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

    def fetch_orders(self):
        """Processing / on-hold orders (naye, jinhe bhejna baaki hai)."""
        rows = self._request("GET", "/orders?per_page=50&status=processing,on-hold&orderby=date&order=desc")
        out = []
        for o in rows or []:
            ship = o.get("shipping") or {}
            bill = o.get("billing") or {}
            name = (f"{ship.get('first_name', '')} {ship.get('last_name', '')}".strip()
                    or f"{bill.get('first_name', '')} {bill.get('last_name', '')}".strip())
            items = []
            for li in o.get("line_items", []):
                it = {"sku_code": li.get("sku") or "", "quantity": li.get("quantity", 1)}
                if li.get("price") not in (None, ""):
                    it["unit_price"] = str(li["price"])
                items.append(it)
            addr = {k: ship.get(k) for k in ("address_1", "address_2", "city", "state", "postcode", "country") if ship.get(k)}
            out.append({"external_order_id": str(o.get("number") or o["id"]), "customer_name": name,
                        "customer_phone": bill.get("phone", ""), "shipping_address": addr, "items": items})
        return out

    def fetch_products(self):
        out, page = [], 1
        while len(out) < 200:
            rows = self._request("GET", f"/products?per_page=50&page={page}&status=any")
            if not rows:
                break
            for p in rows:
                st = {"publish": "ACTIVE", "private": "ARCHIVED"}.get(p.get("status"), "DRAFT")
                if p.get("type") == "variable":
                    vs = [{"sku_code": (v.get("sku") or "").strip(), "name": "",
                           "price": v.get("regular_price") or v.get("price") or "0",
                           "quantity": v.get("stock_quantity") or 0}
                          for v in self._request("GET", f"/products/{p['id']}/variations?per_page=100")]
                    for v in vs:
                        v["name"] = v["sku_code"]
                else:
                    vs = [{"sku_code": (p.get("sku") or "").strip(), "name": "Default",
                           "price": p.get("regular_price") or p.get("price") or "0",
                           "quantity": p.get("stock_quantity") or 0}]
                out.append({"external_id": str(p["id"]), "title": p.get("name") or "",
                            "description": html.unescape(p.get("short_description") or p.get("description") or "")[:2000],
                            "status": st, "variants": vs})
            if len(rows) < 50:
                break
            page += 1
        return out[:200]
