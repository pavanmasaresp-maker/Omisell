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
