"""CSV export. Marketplace ke bulk-upload template (Amazon/Flipkart/Meesho...) ke columns alag hote hain;
unka asli sample file milne par PROFILES mein ek naya mapping jod do. Tab tak 'default' (saaf, generic) chalta hai."""
import csv
import io

from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from accounts.permissions import HasTenant
from inventory.models import InventoryBalance
from orders.models import Order


def safe(v):
    """Excel/Sheets formula injection se bachav: = + - @ se shuru hone wali text ke aage ' laga do."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


def to_csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([safe(c) for c in r])
    return buf.getvalue()


# profile -> (header, row_fn). Naya marketplace template yahan add hota hai.
ORDER_PROFILES = {
    "default": (
        ["order_number", "date", "channel", "external_order_id", "status", "customer_name", "customer_phone",
         "city", "sku", "quantity", "unit_price", "line_total"],
        lambda o, i: [o.order_number, o.placed_at.date().isoformat(),
                      o.channel_connection.name if o.channel_connection else "Direct",
                      o.external_order_id, o.status, o.customer_name, o.customer_phone,
                      (o.shipping_address or {}).get("city", ""), i.sku.sku_code, i.quantity,
                      i.unit_price, i.line_total]),
}
STOCK_PROFILES = {
    "default": (
        ["sku", "product", "price", "on_hand", "reserved", "available"],
        lambda b: [b.sku.sku_code, b.sku.variant.product.title, b.sku.price, b.on_hand, b.reserved,
                   b.on_hand - b.reserved]),
}


def _respond(text, name):
    r = HttpResponse(text, content_type="text/csv; charset=utf-8")
    r["Content-Disposition"] = f'attachment; filename="{name}"'
    return r


class OrdersCsvView(APIView):
    permission_classes = [HasTenant]

    def get(self, request):
        prof = ORDER_PROFILES.get(request.query_params.get("profile", "default"))
        if prof is None:
            return Response({"error": "Ye profile maujood nahi."}, status=400)
        header, fn = prof
        qs = Order.objects.filter(tenant_id=request.user.tenant_id).select_related(
            "channel_connection").prefetch_related("items__sku").order_by("-placed_at")[:5000]
        rows = [fn(o, i) for o in qs for i in o.items.all()]
        return _respond(to_csv(header, rows), "orders.csv")


class StockCsvView(APIView):
    permission_classes = [HasTenant]

    def get(self, request):
        prof = STOCK_PROFILES.get(request.query_params.get("profile", "default"))
        if prof is None:
            return Response({"error": "Ye profile maujood nahi."}, status=400)
        header, fn = prof
        qs = InventoryBalance.objects.filter(tenant_id=request.user.tenant_id).select_related(
            "sku__variant__product").order_by("sku__sku_code")
        return _respond(to_csv(header, [fn(b) for b in qs]), "stock.csv")
