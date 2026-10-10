import re

from rest_framework import serializers

from .models import ChannelConnection, ChannelListing, SyncJob

SHOP_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$")
SITE_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$")


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelConnection
        fields = ["id", "channel", "name", "shop_domain", "status",
                  "last_checked_at", "last_error", "auto_process", "created_at"]


class ConnectionCreateSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=ChannelConnection.Channel.choices)
    name = serializers.CharField(max_length=120)
    shop_domain = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    access_token = serializers.CharField(max_length=500, write_only=True)

    def validate(self, attrs):
        if attrs["channel"] == "SHOPIFY":
            d = attrs["shop_domain"].strip().lower()
            d = d.replace("https://", "").replace("http://", "").strip("/")
            # SSRF se bachne ke liye sirf *.myshopify.com allowed
            if not SHOP_RE.match(d):
                raise serializers.ValidationError(
                    {"shop_domain": "Aisa likho: mystore.myshopify.com"})
            attrs["shop_domain"] = d
        elif attrs["channel"] == "WOOCOMMERCE":
            d = attrs["shop_domain"].strip().lower()
            d = d.replace("https://", "").replace("http://", "").strip("/")
            if not SITE_RE.match(d):
                raise serializers.ValidationError(
                    {"shop_domain": "Aisa likho: mystore.com (https wali site, bina / ke)"})
            if ":" not in attrs["access_token"]:
                raise serializers.ValidationError(
                    {"access_token": "Aisa likho: consumer_key:consumer_secret"})
            attrs["shop_domain"] = d
        else:
            attrs["shop_domain"] = "demo"
        tenant_id = self.context["request"].user.tenant_id
        if ChannelConnection.objects.filter(
                tenant_id=tenant_id, channel=attrs["channel"],
                shop_domain=attrs["shop_domain"]).exists():
            raise serializers.ValidationError("Ye connection pehle se hai.")
        return attrs


class PublishSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    connection = serializers.UUIDField()


class ListingSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = ChannelListing
        fields = ["id", "product", "product_title", "connection", "connection_name",
                  "status", "external_product_id", "last_error", "last_synced_at"]


class JobSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source="connection.name", read_only=True)
    product_title = serializers.SerializerMethodField()
    sku_code = serializers.SerializerMethodField()

    class Meta:
        model = SyncJob
        fields = ["id", "job_type", "status", "attempts", "max_attempts", "next_run_at",
                  "last_error", "connection_name", "product_title", "sku_code",
                  "created_at", "finished_at"]

    def get_product_title(self, obj):
        return obj.listing.product.title if obj.listing else ""

    def get_sku_code(self, obj):
        return obj.sku.sku_code if obj.sku else ""
