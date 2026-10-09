import json
import uuid

from django.db import models
from django.utils import timezone

from . import crypto


class ChannelConnection(models.Model):
    class Channel(models.TextChoices):
        SHOPIFY = "SHOPIFY"
        DEMO = "DEMO"

    class Status(models.TextChoices):
        PENDING = "PENDING"
        CONNECTED = "CONNECTED"
        ERROR = "ERROR"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    name = models.CharField(max_length=120)
    shop_domain = models.CharField(max_length=200, blank=True)
    credentials_encrypted = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(
            fields=["tenant", "channel", "shop_domain"], name="uniq_tenant_channel_shop")]

    def set_credentials(self, data: dict):
        self.credentials_encrypted = crypto.encrypt(json.dumps(data))

    def get_credentials(self) -> dict:
        if not self.credentials_encrypted:
            return {}
        return json.loads(crypto.decrypt(self.credentials_encrypted))


class ChannelListing(models.Model):
    """Product ka ek channel par status. Publish logic Phase 2b/3 mein aayega."""

    class Status(models.TextChoices):
        PENDING = "PENDING"
        ACTIVE = "ACTIVE"
        FAILED = "FAILED"
        NEEDS_ACTION = "NEEDS_ACTION"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    connection = models.ForeignKey(ChannelConnection, on_delete=models.CASCADE,
                                   related_name="listings")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE,
                                related_name="listings")
    external_product_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    last_error = models.CharField(max_length=300, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["connection", "product"], name="uniq_listing_per_connection_product")]


class SyncJob(models.Model):
    """Durable background job. Status, attempts aur error history hamesha save hoti hai."""

    class Type(models.TextChoices):
        PUBLISH_PRODUCT = "PUBLISH_PRODUCT"
        UPDATE_INVENTORY = "UPDATE_INVENTORY"

    class Status(models.TextChoices):
        PENDING = "PENDING"
        RUNNING = "RUNNING"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        NEEDS_ACTION = "NEEDS_ACTION"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    connection = models.ForeignKey(ChannelConnection, on_delete=models.CASCADE, related_name="jobs")
    listing = models.ForeignKey(ChannelListing, null=True, blank=True,
                                on_delete=models.CASCADE, related_name="jobs")
    sku = models.ForeignKey("catalog.SKU", null=True, blank=True, on_delete=models.CASCADE)
    job_type = models.CharField(max_length=30, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    next_run_at = models.DateTimeField(default=timezone.now)
    last_error = models.CharField(max_length=300, blank=True)
    idempotency_key = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "next_run_at"])]
        constraints = [models.UniqueConstraint(
            fields=["tenant", "idempotency_key"], name="uniq_tenant_syncjob_idem_key",
            condition=~models.Q(idempotency_key=""))]


class SyncAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name="attempt_log")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    error = models.CharField(max_length=300, blank=True)
    retryable = models.BooleanField(default=False)
