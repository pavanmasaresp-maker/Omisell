"""Shopify 'Connect' button: OAuth (authorization code). Seller ko token haath se nahi banana padta.

Setup (ek baar, aapka kaam): Shopify Partners mein app banao -> Client ID/Secret ko Render Environment mein
SHOPIFY_CLIENT_ID / SHOPIFY_CLIENT_SECRET daalo, aur app ke 'Allowed redirection URL' mein
https://<aapka-backend>/api/v1/channels/shopify/callback daalo."""
import hashlib
import hmac
import html
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from django.core import signing
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChannelConnection
from .permissions import ChannelPermission
from .serializers import SHOP_RE

SCOPES = "read_products,write_products,read_inventory,write_inventory,read_locations,read_orders"
STATE_SALT = "shopify-oauth"
STATE_MAX_AGE = 15 * 60


def client():
    return os.environ.get("SHOPIFY_CLIENT_ID", "").strip(), os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()


def redirect_uri(request):
    return os.environ.get("SHOPIFY_REDIRECT_URL", "").strip() or \
        request.build_absolute_uri("/api/v1/channels/shopify/callback")


def clean_shop(raw):
    d = (raw or "").strip().lower().replace("https://", "").replace("http://", "").strip("/")
    if d and "." not in d:
        d += ".myshopify.com"
    return d if SHOP_RE.match(d) else ""


def verify_hmac(params, secret):
    """Shopify callback ka hmac check: baaki sab params sorted, 'k=v&k=v' par HMAC-SHA256."""
    given = params.get("hmac", "")
    msg = "&".join(f"{k}={v}" for k, v in sorted((k, v) for k, v in params.items() if k != "hmac"))
    calc = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return bool(given) and hmac.compare_digest(calc, given)


def exchange_code(shop, code, cid, secret):
    req = urllib.request.Request(
        f"https://{shop}/admin/oauth/access_token", method="POST",
        data=json.dumps({"client_id": cid, "client_secret": secret, "code": code}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("access_token", "")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return ""


class ShopifyConfigView(APIView):
    permission_classes = [ChannelPermission]

    def get(self, request):
        return Response({"enabled": all(client())})


class ShopifyStartView(APIView):
    permission_classes = [ChannelPermission]

    def post(self, request):
        cid, secret = client()
        if not (cid and secret):
            return Response({"error": "Shopify Connect abhi set nahi hai. Admin ko SHOPIFY_CLIENT_ID aur "
                                      "SHOPIFY_CLIENT_SECRET Render mein daalna hoga. Tab tak token se connect karo."},
                            status=400)
        shop = clean_shop(request.data.get("shop_domain"))
        if not shop:
            return Response({"error": "Aisa likho: mystore.myshopify.com"}, status=400)
        name = (request.data.get("name") or "").strip()[:120] or "Shopify"
        state = signing.dumps({"t": str(request.user.tenant_id), "s": shop, "n": name}, salt=STATE_SALT)
        q = urllib.parse.urlencode({"client_id": cid, "scope": SCOPES,
                                    "redirect_uri": redirect_uri(request), "state": state})
        return Response({"url": f"https://{shop}/admin/oauth/authorize?{q}"})


def _page(msg, ok):
    color = "#12733F" if ok else "#B42318"
    body = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<body style='font-family:sans-serif;padding:32px;text-align:center'>"
            f"<h2 style='color:{color}'>{'Connect ho gaya' if ok else 'Connect nahi hua'}</h2>"
            f"<p>{html.escape(msg)}</p><p>OmniSell app par wapas jao.</p></body>")
    return HttpResponse(body, status=200 if ok else 400)


class ShopifyCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        from .views import run_check
        cid, secret = client()
        params = {k: v for k, v in request.query_params.items()}
        if not (cid and secret) or not verify_hmac(params, secret):
            return _page("Shopify ka jawab verify nahi hua. Dobara try karo.", False)
        try:
            st = signing.loads(params.get("state", ""), salt=STATE_SALT, max_age=STATE_MAX_AGE)
        except signing.BadSignature:
            return _page("Link purana ho gaya. App se dobara Connect dabao.", False)
        shop = clean_shop(params.get("shop"))
        if not shop or shop != st["s"]:
            return _page("Store address match nahi hua.", False)
        token = exchange_code(shop, params.get("code", ""), cid, secret)
        if not token:
            return _page("Shopify se token nahi mila. Dobara try karo.", False)
        conn = ChannelConnection.objects.filter(tenant_id=st["t"], channel="SHOPIFY", shop_domain=shop).first() \
            or ChannelConnection(tenant_id=st["t"], channel="SHOPIFY", shop_domain=shop, name=st["n"])
        conn.set_credentials({"access_token": token})
        run_check(conn)
        conn.save()
        return _page(f"{shop} OmniSell se jud gaya.", True)
