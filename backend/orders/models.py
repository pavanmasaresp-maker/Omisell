import uuid
from django.db import models


class TimeStamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderStatus(models.TextChoices):
    IMPORTED = "IMPORTED"
    CONFIRMED = "CONFIRMED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"


# States from which an order may still be cancelled (before anything shipped)
CANCELLABLE_STATES = {OrderStatus.IMPORTED, OrderStatus.CONFIRMED, OrderStatus.PACKED}


class Order(TimeStamped):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    order_number = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=OrderStatus.choices,
                               default=OrderStatus.IMPORTED)
    channel_connection = models.ForeignKey(
        "marketplaces.ChannelConnection", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
        help_text="Null = order placed directly on own store/manual entry.")
    external_order_id = models.CharField(max_length=200, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=32, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=200, blank=True, default="")
    placed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-placed_at"]
        indexes = [models.Index(fields=["tenant", "status"]),
                   models.Index(fields=["tenant", "-placed_at"])]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "order_number"],
                                    name="uniq_tenant_order_number"),
            models.UniqueConstraint(
                fields=["tenant", "idempotency_key"], name="uniq_tenant_order_idem_key",
                condition=~models.Q(idempotency_key="")),
        ]

    @property
    def total_amount(self):
        return sum((i.unit_price * i.quantity for i in self.items.all()), start=0)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    sku = models.ForeignKey("catalog.SKU", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.order.order_number}:{self.sku.sku_code} x{self.quantity}"


class ShipmentStatus(models.TextChoices):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"


class Shipment(TimeStamped):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipments")
    carrier = models.CharField(max_length=120, blank=True)
    tracking_number = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=ShipmentStatus.choices,
                               default=ShipmentStatus.PENDING)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipment({self.order.order_number})"


class ReturnStatus(models.TextChoices):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"


class ReturnRequest(TimeStamped):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="returns")
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=ReturnStatus.choices,
                               default=ReturnStatus.REQUESTED)

    def __str__(self):
        return f"Return({self.order_item}, {self.quantity})"
