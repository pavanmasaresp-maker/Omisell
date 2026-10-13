from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import HasTenant
from catalog.models import SKU, Product
from .models import InventoryBalance, InventoryLedger


class DashboardView(APIView):
    permission_classes = [HasTenant]

    def get(self, request):
        tid = request.user.tenant_id
        try:
            threshold = int(request.query_params.get("threshold", 5))
        except ValueError:
            threshold = 5
        products = Product.objects.filter(tenant_id=tid)
        skus = SKU.objects.filter(tenant_id=tid, is_active=True).select_related("variant__product")
        balances = {b.sku_id: b for b in InventoryBalance.objects.filter(tenant_id=tid)}
        totals = InventoryBalance.objects.filter(tenant_id=tid).aggregate(
            on_hand=Sum("on_hand"), reserved=Sum("reserved"))
        low = []
        for k in skus:
            b = balances.get(k.id)
            available = (b.on_hand - b.reserved) if b else 0
            if available <= threshold:
                low.append({"sku": str(k.id), "sku_code": k.sku_code,
                            "product": k.variant.product.title, "available": available})
        low.sort(key=lambda x: x["available"])
        recent = InventoryLedger.objects.filter(tenant_id=tid).select_related("sku")[:5]
        return Response({
            "products": products.count(),
            "products_active": products.filter(status="ACTIVE").count(),
            "skus": skus.count(),
            "total_on_hand": totals["on_hand"] or 0,
            "total_reserved": totals["reserved"] or 0,
            "low_stock_threshold": threshold,
            "low_stock": low[:20],
            "recent": [{"sku_code": e.sku.sku_code, "entry_type": e.entry_type,
                        "quantity_delta": e.quantity_delta, "created_at": e.created_at}
                       for e in recent],
        })


SOLD_EXCLUDE = ("CANCELLED", "RETURN_REQUESTED", "RETURNED")
PIPELINE = ["IMPORTED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]


class OverviewView(APIView):
    """Seller dashboard: kaunsa product kis channel par, kitna bika, charges, delivery."""
    permission_classes = [HasTenant]

    def get(self, request):
        from datetime import timedelta
        from decimal import Decimal
        from django.db.models import Count, F, Sum as S, DecimalField, ExpressionWrapper
        from django.utils import timezone
        from marketplaces.models import ChannelConnection, ChannelListing
        from orders.models import Order, OrderItem

        tid = request.user.tenant_id
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30
        days = max(0, min(days, 3650))
        since = timezone.now() - timedelta(days=days) if days else None

        orders = Order.objects.filter(tenant_id=tid)
        items = OrderItem.objects.filter(order__tenant_id=tid)
        if since:
            orders = orders.filter(placed_at__gte=since)
            items = items.filter(order__placed_at__gte=since)

        # delivery pipeline
        counts = {r["status"]: r["n"] for r in orders.values("status").annotate(n=Count("id"))}
        pipeline = {s: counts.get(s, 0) for s in PIPELINE}
        pipeline["RETURNED"] += counts.get("RETURN_REQUESTED", 0)

        line = ExpressionWrapper(F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2))
        sold_items = items.exclude(order__status__in=SOLD_EXCLUDE)
        per_conn = {}
        for r in sold_items.values("order__channel_connection").annotate(units=S("quantity"), rev=S(line)):
            per_conn[r["order__channel_connection"]] = r
        order_cnt = {}
        for r in orders.exclude(status__in=SOLD_EXCLUDE).values("channel_connection").annotate(n=Count("id")):
            order_cnt[r["channel_connection"]] = r["n"]
        deliv = {}
        for r in orders.values("channel_connection", "status").annotate(n=Count("id")):
            d = deliv.setdefault(r["channel_connection"], {})
            d[r["status"]] = r["n"]

        listings = {}
        for r in ChannelListing.objects.filter(tenant_id=tid).values("connection", "status").annotate(n=Count("id")):
            listings.setdefault(r["connection"], {})[r["status"]] = r["n"]

        def pack(conn_id, name, channel, pct, per):
            m = per_conn.get(conn_id, {})
            rev = m.get("rev") or Decimal("0")
            n = order_cnt.get(conn_id, 0)
            fees = (rev * pct / Decimal("100")) + per * n
            dl = deliv.get(conn_id, {})
            ls = listings.get(conn_id, {})
            return {
                "id": str(conn_id) if conn_id else None, "name": name, "channel": channel,
                "orders": n, "units": m.get("units") or 0,
                "revenue": str(rev.quantize(Decimal("0.01"))),
                "fees": str(fees.quantize(Decimal("0.01"))),
                "net": str((rev - fees).quantize(Decimal("0.01"))),
                "commission_pct": str(pct), "charge_per_order": str(per),
                "delivered": dl.get("DELIVERED", 0),
                "in_transit": dl.get("SHIPPED", 0),
                "to_ship": dl.get("IMPORTED", 0) + dl.get("CONFIRMED", 0) + dl.get("PACKED", 0),
                "returned": dl.get("RETURNED", 0) + dl.get("RETURN_REQUESTED", 0),
                "cancelled": dl.get("CANCELLED", 0),
                "listed": ls.get("ACTIVE", 0), "pending": ls.get("PENDING", 0),
                "failed": ls.get("FAILED", 0) + ls.get("NEEDS_ACTION", 0),
            }

        channels = []
        conns = list(ChannelConnection.objects.filter(tenant_id=tid))
        for c in conns:
            channels.append(pack(c.id, c.name, c.channel, c.commission_pct, c.charge_per_order))
        if None in per_conn or None in order_cnt:
            channels.append(pack(None, "Direct / manual", "DIRECT", Decimal("0"), Decimal("0")))
        channels.sort(key=lambda x: -float(x["revenue"]))

        tot_rev = sum(Decimal(c["revenue"]) for c in channels)
        tot_fees = sum(Decimal(c["fees"]) for c in channels)

        # top products
        top = []
        for r in (sold_items.values("sku__variant__product", "sku__variant__product__title")
                  .annotate(units=S("quantity"), rev=S(line)).order_by("-units")[:5]):
            top.append({"product": r["sku__variant__product__title"], "units": r["units"],
                        "revenue": str((r["rev"] or 0))})

        # product -> channels matrix
        by_prod = {}
        for l in ChannelListing.objects.filter(tenant_id=tid).select_related("connection"):
            by_prod.setdefault(l.product_id, []).append(
                {"channel": l.connection.name, "status": l.status})
        sold_by_prod = {}
        for r in sold_items.values("sku__variant__product").annotate(units=S("quantity")):
            sold_by_prod[r["sku__variant__product"]] = r["units"]
        products = []
        for p in Product.objects.filter(tenant_id=tid).order_by("-created_at")[:60]:
            products.append({"id": str(p.id), "title": p.title, "status": p.status,
                             "sold": sold_by_prod.get(p.id, 0), "channels": by_prod.get(p.id, [])})

        live = ChannelListing.objects.filter(tenant_id=tid, status="ACTIVE").values("product").distinct().count()
        return Response({
            "days": days,
            "totals": {
                "products": Product.objects.filter(tenant_id=tid).count(),
                "listed_products": live,
                "orders": sum(c["orders"] for c in channels),
                "units": sum(c["units"] for c in channels),
                "revenue": str(tot_rev.quantize(Decimal("0.01"))),
                "fees": str(tot_fees.quantize(Decimal("0.01"))),
                "net": str((tot_rev - tot_fees).quantize(Decimal("0.01"))),
            },
            "pipeline": pipeline,
            "channels": channels,
            "top_products": top,
            "products": products,
        })
