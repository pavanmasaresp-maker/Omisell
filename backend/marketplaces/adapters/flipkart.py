import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from .base import AdapterError, MarketplaceAdapter

BASE = "https://api.flipkart.net"
PRE_STATES = ["APPROVED", "PACKING_IN_PROGRESS", "PACKED", "READY_TO_DISPATCH"]
MAX_PAGES = 5          # 5 x 20 = 100 shipments har baar
BATCH = 10             # Flipkart listing APIs: max 10 SKU per call


class FlipkartAdapter(MarketplaceAdapter):
    """Flipkart Seller API (self-access app). BETA: docs se bana hai, asli seller account par
    abhi test nahi hua. Token field mein 'application_id:application_secret' daalo.

    Kya karta hai:
      - orders: pre-dispatch shipments -> orders (address/phone Flipkart is API mein nahi deta)
      - stock: jo SKU Flipkart par pehle se listed hai uska inventory update
      - publish: naya listing banata NAHI (Flipkart ko category-wise bahut data chahiye);
        Flipkart panel mein listing banao (SKU wahi rakho), app use jod leta hai aur stock bhejta hai.
    """

    def __init__(self, shop_domain, token):
        app_id, _, secret = (token or "").partition(":")
        self.app_id, self.secret = app_id.strip(), secret.strip()
        self._tok = None
        self._tok_exp = 0

    # ---------- low level ----------
    def _http(self, method, url, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AdapterError("Flipkart ne access nahi diya. Application ID/Secret check karo.",
                                   needs_action=True)
            if e.code in (408, 429) or e.code >= 500:
                raise AdapterError(f"Flipkart temporary error (HTTP {e.code}).", retryable=True)
            raise AdapterError(f"Flipkart ne request reject ki (HTTP {e.code}).", needs_action=True)
        except (urllib.error.URLError, TimeoutError):
            raise AdapterError("Flipkart tak pahunch nahi paaye.", retryable=True)
        except ValueError:
            raise AdapterError("Flipkart ka jawab samajh nahi aaya.", retryable=True)

    def _token(self):
        if not self.app_id or not self.secret:
            raise AdapterError("Token 'application_id:application_secret' format mein daalo.",
                               needs_action=True)
        if self._tok and time.time() < self._tok_exp - 60:
            return self._tok
        auth = base64.b64encode(f"{self.app_id}:{self.secret}".encode()).decode()
        q = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": "Seller_Api"})
        res = self._http("GET", f"{BASE}/oauth-service/oauth/token?{q}",
                         headers={"Authorization": f"Basic {auth}"})
        tok = res.get("access_token")
        if not tok:
            raise AdapterError("Flipkart se token nahi mila. Application ID/Secret check karo.",
                               needs_action=True)
        self._tok = tok
        self._tok_exp = time.time() + int(res.get("expires_in") or 3600)
        return tok

    def _api(self, method, path, body=None):
        return self._http(method, f"{BASE}/sellers{path}", body, {
            "Authorization": f"Bearer {self._token()}",
            "Content-Type": "application/json; charset=utf-8"})

    # ---------- contract ----------
    def authenticate(self):
        self._token()

    def health_check(self):
        self._token()
        return {"shop_name": "Flipkart"}

    def validate_product(self, product):
        errors = []
        if not product.get("title"):
            errors.append("Title zaroori hai.")
        if not (product.get("skus") or []):
            errors.append("Kam se kam ek SKU chahiye.")
        return errors

    def _details(self, sku_codes):
        """sku -> {"product_id", "locations": [ids]} (sirf jo Flipkart par listed hain)."""
        out = {}
        codes = list(sku_codes)
        for i in range(0, len(codes), BATCH):
            res = self._api("POST", "/listings/v3/details", {"sku_ids": codes[i:i + BATCH]})
            for sku, d in (res.get("available") or {}).items():
                locs = [str(l.get("id")) for l in (d.get("locations") or []) if l.get("id")]
                out[sku] = {"product_id": d.get("product_id"), "locations": locs}
        return out

    def _push_inventory(self, items):
        """items: [(sku, quantity)]. Flipkart par na mile to needs_action error."""
        det = self._details([s for s, _ in items])
        missing = [s for s, _ in items if s not in det or not det[s]["product_id"]]
        if missing:
            raise AdapterError("Flipkart par ye SKU listed nahi mila: " + ", ".join(missing[:5]) +
                               ". Pehle Flipkart panel mein listing banao (SKU wahi rakho).",
                               needs_action=True)
        no_loc = [s for s, _ in items if not det[s]["locations"]]
        if no_loc:
            raise AdapterError("Flipkart listing par selling location nahi mili: " + ", ".join(no_loc[:5]),
                               needs_action=True)
        for i in range(0, len(items), BATCH):
            body = {s: {"product_id": det[s]["product_id"],
                        "locations": [{"id": loc, "inventory": max(int(q), 0)} for loc in det[s]["locations"]]}
                    for s, q in items[i:i + BATCH]}
            res = self._api("POST", "/listings/v3/update/inventory", body)
            bad = [f"{s}: {r.get('errors') or r.get('status')}" for s, r in (res or {}).items()
                   if str(r.get("status", "")).upper() not in ("SUCCESS", "OK", "")]
            if bad:
                raise AdapterError("Flipkart stock update fail: " + "; ".join(bad)[:250], needs_action=True)

    def create_listing(self, product):
        skus = product["skus"]
        det = self._details([k["sku_code"] for k in skus])
        missing = [k["sku_code"] for k in skus if k["sku_code"] not in det]
        if missing:
            raise AdapterError("Flipkart par listing nahi mili (" + ", ".join(missing[:5]) + "). "
                               "Flipkart seller panel mein listing banao, SKU wahi rakho, phir dobara Publish karo.",
                               needs_action=True)
        self._push_inventory([(k["sku_code"], k.get("available", 0)) for k in skus])
        return {"external_product_id": str(det[skus[0]["sku_code"]]["product_id"])}

    def update_listing(self, external_id, product):
        return self.create_listing(product)

    def update_inventory(self, external_id, sku_code, quantity):
        self._push_inventory([(sku_code, quantity)])
        return {"quantity": quantity}

    def update_price(self, external_id, sku_code, price):
        raise AdapterError("Flipkart par price app se abhi nahi badalta. Flipkart panel se badlo.",
                           needs_action=True)

    def fetch_orders(self):
        since = (datetime.now(timezone(timedelta(hours=5, minutes=30))) - timedelta(days=30)).isoformat(timespec="seconds")
        body = {"filter": {"type": "preDispatch", "states": PRE_STATES,
                           "orderDate": {"from": since}},
                "pagination": {"pageSize": 20}, "sort": {"field": "orderDate", "order": "desc"}}
        shipments, res = [], self._api("POST", "/v3/shipments/filter/", body)
        for _ in range(MAX_PAGES):
            shipments += res.get("shipments") or []
            nxt = res.get("nextPageUrl")
            if not (res.get("hasMore") and nxt):
                break
            u = urllib.parse.urlparse(nxt)
            path = (u.path + ("?" + u.query if u.query else "")).replace("/sellers/", "/", 1) \
                if u.path.startswith("/sellers/") else (u.path + ("?" + u.query if u.query else ""))
            res = self._api("GET", path)
        orders = {}
        for s in shipments:
            for it in s.get("orderItems") or []:
                oid = str(it.get("orderId") or "")
                if not oid or not it.get("sku"):
                    continue
                o = orders.setdefault(oid, {"external_order_id": oid, "customer_name": "",
                                            "customer_phone": "", "shipping_address": {}, "items": []})
                item = {"sku_code": it["sku"], "quantity": int(it.get("quantity") or 1)}
                pc = it.get("priceComponents") or {}
                if pc.get("sellingPrice") not in (None, ""):
                    item["unit_price"] = str(pc["sellingPrice"])   # VERIFY: per piece ya line total (asli order par check)
                o["items"].append(item)
        return list(orders.values())
