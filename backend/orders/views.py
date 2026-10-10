from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from catalog.models import SKU
from .models import Order, OrderItem, ReturnRequest
from .permissions import OrderPermission
from .serializers import (CancelActionSerializer, OrderCreateSerializer, OrderSerializer,
                          ReturnCreateSerializer, ReturnDecisionSerializer,
                          ReturnRequestSerializer, ShipActionSerializer)
from . import services
from .services import OrderError


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    permission_classes = [OrderPermission]
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.filter(tenant_id=self.request.user.tenant_id).select_related(
            "channel_connection").prefetch_related("items__sku", "shipments")
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    def create(self, request):
        s = OrderCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            order, created = services.create_order(
                tenant_id=request.user.tenant_id, user=request.user, items=d["items"],
                customer_name=d["customer_name"], customer_phone=d["customer_phone"],
                shipping_address=d["shipping_address"], idempotency_key=d["idempotency_key"])
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(OrderSerializer(order).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._transition(services.confirm_order, request, pk)

    @action(detail=True, methods=["post"])
    def pack(self, request, pk=None):
        return self._transition(services.pack_order, request, pk)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        return self._transition(services.deliver_order, request, pk)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        s = CancelActionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        order = self.get_object()
        try:
            services.cancel_order(order, request.user, reason=s.validated_data["reason"])
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        s = ShipActionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        order = self.get_object()
        try:
            order, _shipment = services.ship_order(order, request.user, **s.validated_data)
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(OrderSerializer(order).data)

    def _transition(self, fn, request, pk):
        order = self.get_object()
        try:
            fn(order, request.user)
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(OrderSerializer(order).data)


class ReturnViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    permission_classes = [OrderPermission]
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        return ReturnRequest.objects.filter(
            order_item__order__tenant_id=self.request.user.tenant_id
        ).select_related("order_item__order", "order_item__sku")

    def create(self, request):
        s = ReturnCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            item = OrderItem.objects.get(id=d["order_item"],
                                         order__tenant_id=request.user.tenant_id)
        except OrderItem.DoesNotExist:
            return Response({"order_item": "Not found."}, status=404)
        try:
            rr = services.request_return(item, request.user, d["quantity"], d["reason"])
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(ReturnRequestSerializer(rr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        s = ReturnDecisionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        rr = self.get_object()
        try:
            services.process_return(rr, request.user, s.validated_data["approve"])
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(ReturnRequestSerializer(rr).data)
