import logging

from django.db import transaction
from .models import EntryType, InventoryBalance, InventoryLedger

ON_HAND = {EntryType.ADJUSTMENT, EntryType.SALE, EntryType.RETURN}


class InventoryError(Exception):
    pass


def validate_sign(entry_type, delta):
    if delta == 0:
        raise InventoryError("quantity_delta cannot be 0.")
    if entry_type in (EntryType.SALE, EntryType.RELEASE) and delta > 0:
        raise InventoryError(f"{entry_type} must be negative.")
    if entry_type in (EntryType.RETURN, EntryType.RESERVATION) and delta < 0:
        raise InventoryError(f"{entry_type} must be positive.")


@transaction.atomic
def apply_entry(*, tenant_id, sku, entry_type, delta, reason="", idempotency_key="", user=None):
    """Writes ledger entry + updates balance atomically. Returns (entry, balance, created)."""
    validate_sign(entry_type, delta)
    InventoryBalance.objects.get_or_create(tenant_id=tenant_id, sku=sku)
    balance = InventoryBalance.objects.select_for_update().get(sku=sku)

    if idempotency_key:
        existing = InventoryLedger.objects.filter(
            tenant_id=tenant_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, balance, False

    if entry_type in ON_HAND:
        new_on_hand, new_reserved = balance.on_hand + delta, balance.reserved
    else:
        new_on_hand, new_reserved = balance.on_hand, balance.reserved + delta
    if new_on_hand < 0:
        raise InventoryError("Stock cannot go below 0.")
    if new_reserved < 0:
        raise InventoryError("Reserved cannot go below 0.")
    if entry_type == EntryType.RESERVATION and new_reserved > new_on_hand:
        raise InventoryError("Not enough available stock to reserve.")

    entry = InventoryLedger.objects.create(
        tenant_id=tenant_id, sku=sku, entry_type=entry_type, quantity_delta=delta,
        reason=reason, idempotency_key=idempotency_key, created_by=user)
    balance.on_hand, balance.reserved = new_on_hand, new_reserved
    balance.save()
    _schedule_channel_sync(tenant_id, sku.id, entry.id)
    return entry, balance, True


def _schedule_channel_sync(tenant_id, sku_id, entry_id):
    """Commit ke baad hi job banao (outbox-style): rollback hua to sync job nahi banega."""
    def _run():
        try:
            from marketplaces.sync import enqueue_inventory_sync
            enqueue_inventory_sync(tenant_id, sku_id, entry_id)
        except Exception:
            logging.getLogger(__name__).exception("inventory sync enqueue failed")
    transaction.on_commit(_run)
