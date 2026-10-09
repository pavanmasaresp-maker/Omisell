from django.contrib import admin
from .models import Order, OrderItem, ReturnRequest, Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class ShipmentInline(admin.TabularInline):
    model = Shipment
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "tenant", "status", "customer_name", "placed_at")
    list_filter = ("status", "tenant")
    search_fields = ("order_number", "customer_name", "external_order_id")
    inlines = [OrderItemInline, ShipmentInline]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("order_item", "quantity", "status", "created_at")
    list_filter = ("status",)
