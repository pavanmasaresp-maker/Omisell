import uuid
from django.db import transaction
from django.utils import timezone

from catalog.models import SKU
from inventory.models import EntryType
from inventory.services import InventoryError, apply_entry
from .models import (CANCELLABLE_STATES, Order, OrderItem, OrderStatus,
                     ReturnRequest, ReturnStatus, Shipment, ShipmentStatus)


class OrderError(Exception):
    pass


def _order_number():
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


@transaction.atomic
def create_order(*, tenant_id, user, items, customer_name="", customer_phone="",
                 shipping_address=None, channel_connection=None, external_order_id="",
                 idempotency_key=""):
    """items: list of {sku: SKU instance or id, quantity, unit_price}.
    Reserves stock for every line; rolls back the whole order if any line
    can't be reserved (never partially publish an order)."""
    if idempotency_key:
        existing = Order.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    if not items:
        raise OrderError("Order mein kam se kam ek item hona chahiye.")

    order = Order.objects.create(
        tenant_id=tenant_id, order_number=_order_number(), status=OrderStatus.IMPORTED,
        channel_connection=channel_connection, external_order_id=external_order_id,
        customer_name=customer_name, customer_phone=customer_phone,
        shipping_address=shipping_address or {}, idempotency_key=idempotency_key)

    for line in items:
        sku = line["sku"]
        if not isinstance(sku, SKU):
            try:
                sku = SKU.objects.get(id=sku, tenant_id=tenant_id)
            except SKU.DoesNotExist:
                raise OrderError(f"SKU {sku} nahi mila.")
        qty = int(line["quantity"])
        if qty <= 0:
            raise OrderError("Quantity 0 se zyada honi chahiye.")
        unit_price = line.get("unit_price", sku.price)
        OrderItem.objects.create(order=order, sku=sku, quantity=qty, unit_price=unit_price)
        try:
            apply_entry(tenant_id=tenant_id, sku=sku, entry_type=EntryType.RESERVATION,
                       delta=qty, reason=f"Reserved for {order.order_number}", user=user)
        except InventoryError as e:
            raise OrderError(f"{sku.sku_code}: {e}")

    return order, True


def confirm_order(order, user):
    if order.status != OrderStatus.IMPORTED:
        raise OrderError(f"{order.status} se CONFIRMED nahi kar sakte.")
    order.status = OrderStatus.CONFIRMED
    order.save(update_fields=["status", "updated_at"])
    return order


def pack_order(order, user):
    if order.status != OrderStatus.CONFIRMED:
        raise OrderError(f"{order.status} se PACKED nahi kar sakte.")
    order.status = OrderStatus.PACKED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def cancel_order(order, user, reason=""):
    if order.status not in CANCELLABLE_STATES:
        raise OrderError(f"{order.status} order cancel nahi ho sakta (already shipped/delivered).")
    for item in order.items.select_related("sku"):
        apply_entry(tenant_id=order.tenant_id, sku=item.sku, entry_type=EntryType.RELEASE,
                   delta=-item.quantity, reason=f"Cancelled {order.order_number}: {reason}",
                   user=user)
    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def ship_order(order, user, carrier="", tracking_number=""):
    if order.status != OrderStatus.PACKED:
        raise OrderError(f"{order.status} se SHIPPED nahi kar sakte (pehle PACKED hona zaroori hai).")
    for item in order.items.select_related("sku"):
        # reservation se actual sale: on_hand ghatao, reserved release karo
        apply_entry(tenant_id=order.tenant_id, sku=item.sku, entry_type=EntryType.SALE,
                   delta=-item.quantity, reason=f"Shipped {order.order_number}", user=user)
        apply_entry(tenant_id=order.tenant_id, sku=item.sku, entry_type=EntryType.RELEASE,
                   delta=-item.quantity, reason=f"Shipped {order.order_number}", user=user)
    shipment = Shipment.objects.create(order=order, carrier=carrier, tracking_number=tracking_number,
                                       status=ShipmentStatus.SHIPPED, shipped_at=timezone.now())
    order.status = OrderStatus.SHIPPED
    order.save(update_fields=["status", "updated_at"])
    return order, shipment


def deliver_order(order, user):
    if order.status != OrderStatus.SHIPPED:
        raise OrderError(f"{order.status} se DELIVERED nahi kar sakte.")
    order.status = OrderStatus.DELIVERED
    order.save(update_fields=["status", "updated_at"])
    Shipment.objects.filter(order=order, status=ShipmentStatus.SHIPPED).update(
        status=ShipmentStatus.DELIVERED, delivered_at=timezone.now())
    return order


@transaction.atomic
def request_return(order_item, user, quantity, reason=""):
    order = order_item.order
    if order.status != OrderStatus.DELIVERED:
        raise OrderError("Sirf DELIVERED order pe return request ho sakti hai.")
    if quantity <= 0 or quantity > order_item.quantity:
        raise OrderError("Invalid return quantity.")
    rr = ReturnRequest.objects.create(order_item=order_item, quantity=quantity, reason=reason)
    order.status = OrderStatus.RETURN_REQUESTED
    order.save(update_fields=["status", "updated_at"])
    return rr


@transaction.atomic
def process_return(return_request, user, approve):
    if return_request.status != ReturnStatus.REQUESTED:
        raise OrderError("Ye return already process ho chuki hai.")
    item = return_request.order_item
    order = item.order
    if approve:
        apply_entry(tenant_id=order.tenant_id, sku=item.sku, entry_type=EntryType.RETURN,
                   delta=return_request.quantity,
                   reason=f"Return approved {order.order_number}", user=user)
        return_request.status = ReturnStatus.REFUNDED
        order.status = OrderStatus.RETURNED
    else:
        return_request.status = ReturnStatus.REJECTED
        order.status = OrderStatus.DELIVERED
    return_request.save(update_fields=["status", "updated_at"])
    order.save(update_fields=["status", "updated_at"])
    return return_request
