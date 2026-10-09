from rest_framework import serializers
from .models import EntryType, InventoryBalance, InventoryLedger


class BalanceSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    available = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryBalance
        fields = ["sku", "sku_code", "on_hand", "reserved", "available", "updated_at"]


class LedgerSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)

    class Meta:
        model = InventoryLedger
        fields = ["id", "sku", "sku_code", "entry_type", "quantity_delta", "reason",
                  "idempotency_key", "created_at"]


class AdjustSerializer(serializers.Serializer):
    sku = serializers.UUIDField()
    entry_type = serializers.ChoiceField(choices=EntryType.choices, default=EntryType.ADJUSTMENT)
    quantity_delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")
    idempotency_key = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
