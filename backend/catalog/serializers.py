from rest_framework import serializers
from .models import SKU, Category, Product, ProductMedia, Variant


class TenantCheckedMixin:
    """Blocks IDOR: related objects must belong to the caller's tenant."""
    tenant_fields = []

    def validate(self, attrs):
        tenant_id = self.context["request"].user.tenant_id
        for f in self.tenant_fields:
            obj = attrs.get(f)
            if obj is not None and obj.tenant_id != tenant_id:
                raise serializers.ValidationError({f: "Not found."})
        return attrs


class CategorySerializer(TenantCheckedMixin, serializers.ModelSerializer):
    tenant_fields = ["parent"]

    class Meta:
        model = Category
        fields = ["id", "name", "parent"]


class SKUSerializer(TenantCheckedMixin, serializers.ModelSerializer):
    tenant_fields = ["variant"]

    class Meta:
        model = SKU
        fields = ["id", "variant", "sku_code", "barcode", "price", "mrp", "is_active"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        code = attrs.get("sku_code")
        if code is not None:
            qs = SKU.objects.filter(tenant_id=self.context["request"].user.tenant_id,
                                    sku_code=code)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"sku_code": "Ye SKU code pehle se hai."})
        return attrs


class VariantSerializer(TenantCheckedMixin, serializers.ModelSerializer):
    tenant_fields = ["product"]
    skus = SKUSerializer(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = ["id", "product", "name", "options", "skus"]


class MediaSerializer(TenantCheckedMixin, serializers.ModelSerializer):
    tenant_fields = ["product"]

    class Meta:
        model = ProductMedia
        fields = ["id", "product", "url", "position"]


class ProductSerializer(TenantCheckedMixin, serializers.ModelSerializer):
    tenant_fields = ["category"]
    variants = VariantSerializer(many=True, read_only=True)
    media = MediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "title", "description", "brand", "category", "attributes",
                  "status", "version", "variants", "media", "created_at", "updated_at"]
        read_only_fields = ["version"]
