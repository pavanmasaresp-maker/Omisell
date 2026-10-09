from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import InventoryPermission
from catalog.models import SKU
from .models import InventoryBalance, InventoryLedger
from .serializers import AdjustSerializer, BalanceSerializer, LedgerSerializer
from .services import InventoryError, apply_entry


class BalanceListView(generics.ListAPIView):
    permission_classes = [InventoryPermission]
    serializer_class = BalanceSerializer

    def get_queryset(self):
        qs = InventoryBalance.objects.filter(
            tenant_id=self.request.user.tenant_id).select_related("sku").order_by("sku__sku_code")
        code = self.request.query_params.get("sku_code")
        return qs.filter(sku__sku_code=code) if code else qs


class LedgerListView(generics.ListAPIView):
    permission_classes = [InventoryPermission]
    serializer_class = LedgerSerializer

    def get_queryset(self):
        qs = InventoryLedger.objects.filter(
            tenant_id=self.request.user.tenant_id).select_related("sku")
        sku = self.request.query_params.get("sku")
        return qs.filter(sku_id=sku) if sku else qs


class AdjustView(APIView):
    permission_classes = [InventoryPermission]

    def post(self, request):
        s = AdjustSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            sku = SKU.objects.get(id=d["sku"], tenant_id=request.user.tenant_id)
        except SKU.DoesNotExist:
            return Response({"sku": "Not found."}, status=404)
        try:
            entry, balance, created = apply_entry(
                tenant_id=request.user.tenant_id, sku=sku, entry_type=d["entry_type"],
                delta=d["quantity_delta"], reason=d["reason"],
                idempotency_key=d["idempotency_key"], user=request.user)
        except InventoryError as e:
            return Response({"error": str(e)}, status=400)
        return Response({"entry": LedgerSerializer(entry).data,
                         "balance": BalanceSerializer(balance).data},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
