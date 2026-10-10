import csv
import io

from django.db import transaction
from django.db.models import ProtectedError, Q
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CatalogPermission
from inventory.models import EntryType
from inventory.services import InventoryError, apply_entry
from .models import SKU, Category, Product, ProductMedia, Variant
from .serializers import (CategorySerializer, MediaSerializer, ProductSerializer,
                          SKUSerializer, VariantSerializer)


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [CatalogPermission]

    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Is item ki stock history hai, isliye delete nahi ho sakta. "
                          "Product ko ARCHIVED kar do."}, status=409)


class CategoryViewSet(TenantScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(TenantScopedViewSet):
    queryset = Product.objects.prefetch_related("variants__skus", "media")
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        status = params.get("status")
        if status:
            qs = qs.filter(status=status)
        search = params.get("search")
        if search:
            qs = qs.filter(Q(title__icontains=search) |
                           Q(variants__skus__sku_code__icontains=search)).distinct()
        return qs


class VariantViewSet(TenantScopedViewSet):
    queryset = Variant.objects.prefetch_related("skus")
    serializer_class = VariantSerializer


class SKUViewSet(TenantScopedViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.query_params.get("sku_code")
        return qs.filter(sku_code=code) if code else qs


class MediaViewSet(TenantScopedViewSet):
    queryset = ProductMedia.objects.all()
    serializer_class = MediaSerializer


class BulkImportView(APIView):
    """CSV bulk product import — Phase 4.
    Expected columns: title, sku_code, price, stock (stock optional).
    Each row is its own small transaction: one bad row doesn't kill the
    whole batch (Phase 4 "bulk publishing" needs partial-success reporting,
    not a single opaque failure for the seller)."""
    permission_classes = [CatalogPermission]
    parser_classes = [MultiPartParser]

    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"error": "CSV file ('file' field) attach karo."}, status=400)
        try:
            text = f.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"error": "File UTF-8 encoded CSV honi chahiye."}, status=400)

        reader = csv.DictReader(io.StringIO(text))
        required = {"title", "sku_code", "price"}
        missing = required - set(h.strip().lower() for h in (reader.fieldnames or []))
        if missing:
            return Response({"error": f"CSV mein ye columns missing hain: {', '.join(sorted(missing))}"},
                            status=400)

        tenant_id = request.user.tenant_id
        created, skipped, errors = 0, 0, []
        for i, row in enumerate(reader, start=2):  # row 1 = header
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            title, sku_code, price_raw = row.get("title"), row.get("sku_code"), row.get("price")
            if not title or not sku_code or not price_raw:
                errors.append(f"Row {i}: title/sku_code/price khali hai, skip kiya.")
                continue
            if SKU.objects.filter(tenant_id=tenant_id, sku_code=sku_code).exists():
                skipped += 1
                errors.append(f"Row {i}: SKU '{sku_code}' already exist karta hai, skip kiya.")
                continue
            try:
                with transaction.atomic():
                    price = float(price_raw)
                    product = Product.objects.create(tenant_id=tenant_id, title=title, status="DRAFT")
                    variant = Variant.objects.create(tenant_id=tenant_id, product=product, name="Default")
                    sku = SKU.objects.create(tenant_id=tenant_id, variant=variant,
                                             sku_code=sku_code, price=price)
                    stock_raw = row.get("stock")
                    if stock_raw:
                        apply_entry(tenant_id=tenant_id, sku=sku, entry_type=EntryType.ADJUSTMENT,
                                   delta=int(float(stock_raw)), reason="Bulk CSV import", user=request.user)
                created += 1
            except (ValueError, InventoryError) as e:
                errors.append(f"Row {i}: {e}")
            except Exception as e:  # noqa: BLE001 — row-level isolation, don't let one bad row 500 the batch
                errors.append(f"Row {i}: unexpected error — {e}")

        return Response({"created": created, "skipped": skipped, "errors": errors})
