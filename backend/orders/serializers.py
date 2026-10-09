from rest_framework import serializers
from .models import Order, OrderItem, ReturnRequest, Shipment


class OrderItemSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "sku", "sku_code", "quantity", "unit_price", "line_total"]


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "carrier", "tracking_number", "status", "shipped_at", "delivered_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipments = ShipmentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_number", "status", "channel_connection", "external_order_id",
                  "customer_name", "customer_phone", "shipping_address", "placed_at",
                  "total_amount", "items", "shipments"]


class OrderItemInputSerializer(serializers.Serializer):
    sku = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    shipping_address = serializers.JSONField(required=False, default=dict)
    items = OrderItemInputSerializer(many=True)
    idempotency_key = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class ShipActionSerializer(serializers.Serializer):
    carrier = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    tracking_number = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class CancelActionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = ["id", "order_item", "quantity", "reason", "status", "created_at"]
        read_only_fields = ["status", "created_at"]


class ReturnCreateSerializer(serializers.Serializer):
    order_item = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


class ReturnDecisionSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
