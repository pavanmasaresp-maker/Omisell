import uuid
from django.db import models


class EntryType(models.TextChoices):
    ADJUSTMENT = "ADJUSTMENT"      # signed, changes on_hand (stock count fix, restock)
    SALE = "SALE"                  # negative, on_hand
    RETURN = "RETURN"              # positive, on_hand
    RESERVATION = "RESERVATION"    # positive, reserved
    RELEASE = "RELEASE"            # negative, reserved


class InventoryLedger(models.Model):
    """Append-only. Balance is derived from these entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    sku = models.ForeignKey("catalog.SKU", on_delete=models.PROTECT, related_name="ledger")
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=300, blank=True)
    idempotency_key = models.CharField(max_length=200, blank=True, default="")
    created_by = models.ForeignKey("accounts.User", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant", "sku", "-created_at"])]
        constraints = [models.UniqueConstraint(
            fields=["tenant", "idempotency_key"], name="uniq_tenant_idem_key",
            condition=~models.Q(idempotency_key=""))]


class InventoryBalance(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    sku = models.OneToOneField("catalog.SKU", on_delete=models.CASCADE, related_name="balance")
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available(self):
        return self.on_hand - self.reserved
