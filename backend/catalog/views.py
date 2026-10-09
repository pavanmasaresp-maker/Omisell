from django.db.models import ProtectedError, Q
from rest_framework import viewsets
from rest_framework.response import Response
from accounts.permissions import CatalogPermission
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
