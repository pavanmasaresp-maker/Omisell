from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response

from .adapters.base import AdapterError
from .adapters.registry import get_adapter
from catalog.models import Product
from .models import ChannelConnection, ChannelListing, SyncJob
from .permissions import ChannelPermission, SyncPermission
from .serializers import (ConnectionCreateSerializer, ConnectionSerializer, JobSerializer,
                          ListingSerializer, PublishSerializer)
from .order_import import import_order, make_demo_order
from .sync import enqueue_publish
from orders.serializers import OrderSerializer
from orders.services import OrderError


def run_check(conn):
    try:
        get_adapter(conn).health_check()
        conn.status = ChannelConnection.Status.CONNECTED
        conn.last_error = ""
    except AdapterError as e:
        conn.status = ChannelConnection.Status.ERROR
        conn.last_error = str(e)[:300]
    conn.last_checked_at = timezone.now()


class ConnectionViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    permission_classes = [ChannelPermission]
    serializer_class = ConnectionSerializer
    queryset = ChannelConnection.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)

    def create(self, request):
        s = ConnectionCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        d = s.validated_data
        conn = ChannelConnection(tenant_id=request.user.tenant_id, channel=d["channel"],
                                 name=d["name"], shop_domain=d["shop_domain"])
        conn.set_credentials({"access_token": d["access_token"]})
        run_check(conn)
        conn.save()
        return Response(ConnectionSerializer(conn).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def check(self, request, pk=None):
        conn = self.get_object()
        run_check(conn)
        conn.save()
        return Response(ConnectionSerializer(conn).data)

    @action(detail=True, methods=["post"], url_path="auto-process")
    def set_auto_process(self, request, pk=None):
        conn = self.get_object()
        level = request.data.get("auto_process")
        if level not in ("MANUAL", "CONFIRM", "PACK"):
            return Response({"error": "auto_process MANUAL, CONFIRM ya PACK hona chahiye."}, status=400)
        conn.auto_process = level
        conn.save(update_fields=["auto_process"])
        return Response(ConnectionSerializer(conn).data)

    @action(detail=True, methods=["post"], url_path="simulate-order")
    def simulate_order(self, request, pk=None):
        """Sirf DEMO channel: marketplace se nakli order aaya, bilkul asli import raste se."""
        conn = self.get_object()
        if conn.channel != ChannelConnection.Channel.DEMO:
            return Response({"error": "Nakli order sirf Demo channel par bante hain."}, status=400)
        try:
            order, _ = import_order(conn, make_demo_order(conn))
        except OrderError as e:
            return Response({"error": str(e)}, status=400)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PublishView(APIView):
    """Publish ek durable job banata hai (202). Marketplace call request mein nahi hoti."""
    permission_classes = [SyncPermission]

    def post(self, request):
        s = PublishSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tid = request.user.tenant_id
        conn = get_object_or_404(ChannelConnection, id=s.validated_data["connection"], tenant_id=tid)
        product = get_object_or_404(Product, id=s.validated_data["product"], tenant_id=tid)
        if conn.status != ChannelConnection.Status.CONNECTED:
            return Response({"error": "Channel connected nahi hai. Channels mein Re-check karo."},
                            status=status.HTTP_400_BAD_REQUEST)
        job, created = enqueue_publish(conn, product)
        return Response(JobSerializer(job).data,
                        status=status.HTTP_202_ACCEPTED if created else status.HTTP_200_OK)


class JobViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [SyncPermission]
    serializer_class = JobSerializer
    queryset = SyncJob.objects.select_related("connection", "listing__product", "sku")

    def get_queryset(self):
        qs = super().get_queryset().filter(tenant_id=self.request.user.tenant_id)
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        job = self.get_object()
        if job.status not in (SyncJob.Status.FAILED, SyncJob.Status.NEEDS_ACTION):
            return Response({"error": "Sirf FAILED ya NEEDS_ACTION job retry hota hai."}, status=400)
        job.status, job.attempts, job.last_error, job.finished_at = SyncJob.Status.PENDING, 0, "", None
        job.next_run_at = timezone.now()
        job.save()
        if job.job_type == SyncJob.Type.PUBLISH_PRODUCT and job.listing:
            job.listing.status, job.listing.last_error = ChannelListing.Status.PENDING, ""
            job.listing.save()
        return Response(JobSerializer(job).data)


class ListingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [SyncPermission]
    serializer_class = ListingSerializer
    queryset = ChannelListing.objects.select_related("product", "connection")

    def get_queryset(self):
        qs = super().get_queryset().filter(tenant_id=self.request.user.tenant_id)
        pid = self.request.query_params.get("product")
        return qs.filter(product_id=pid) if pid else qs
