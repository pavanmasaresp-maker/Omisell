"""DB-backed job queue. Worker: python manage.py run_sync_worker
Retry: exponential backoff + jitter. Har attempt SyncAttempt mein save hota hai."""
import logging
import random
from datetime import timedelta

from django.db import connection as db_conn
from django.db import transaction
from django.utils import timezone

from inventory.models import InventoryBalance
from .adapters.base import AdapterError
from .adapters.registry import get_adapter
from .models import ChannelListing, SyncAttempt, SyncJob

log = logging.getLogger(__name__)


def backoff_seconds(attempts):
    return min(3600, 30 * (2 ** attempts)) + random.uniform(0, 5)


def _available(sku_id):
    bal = InventoryBalance.objects.filter(sku_id=sku_id).first()
    return (bal.on_hand - bal.reserved) if bal else 0


def product_payload(product):
    skus = []
    for v in product.variants.all():
        for k in v.skus.all():
            skus.append({"id": str(k.id), "sku_code": k.sku_code, "price": str(k.price),
                         "available": _available(k.id)})
    return {"id": str(product.id), "title": product.title, "description": product.description,
            "brand": product.brand, "status": product.status, "skus": skus}


def enqueue_publish(connection, product):
    """Idempotent: same product version ke liye dobara call karne par wahi job milta hai."""
    listing, _ = ChannelListing.objects.get_or_create(
        tenant_id=connection.tenant_id, connection=connection, product=product)
    key = f"publish:{connection.id}:{product.id}:{product.version}"
    job, created = SyncJob.objects.get_or_create(
        tenant_id=connection.tenant_id, idempotency_key=key,
        defaults={"connection": connection, "listing": listing,
                  "job_type": SyncJob.Type.PUBLISH_PRODUCT})
    if created:
        listing.status = ChannelListing.Status.PENDING
        listing.last_error = ""
        listing.save()
    return job, created


def enqueue_inventory_sync(tenant_id, sku_id, entry_id):
    """Stock badalne par har ACTIVE listing ke liye ek job."""
    listings = ChannelListing.objects.filter(
        tenant_id=tenant_id, status=ChannelListing.Status.ACTIVE,
        product__variants__skus__id=sku_id).select_related("connection").distinct()
    for l in listings:
        SyncJob.objects.get_or_create(
            tenant_id=tenant_id, idempotency_key=f"inv:{l.connection_id}:{sku_id}:{entry_id}",
            defaults={"connection": l.connection, "listing": l, "sku_id": sku_id,
                      "job_type": SyncJob.Type.UPDATE_INVENTORY})


def claim_next():
    now = timezone.now()
    with transaction.atomic():
        qs = SyncJob.objects.filter(status=SyncJob.Status.PENDING,
                                    next_run_at__lte=now).order_by("next_run_at")
        if db_conn.features.has_select_for_update_skip_locked:
            qs = qs.select_for_update(skip_locked=True)
        elif db_conn.features.has_select_for_update:
            qs = qs.select_for_update()
        job = qs.first()
        if job is None:
            return None
        job.status = SyncJob.Status.RUNNING
        job.attempts += 1
        job.save(update_fields=["status", "attempts", "updated_at"])
        return job


def _run_job(job):
    adapter = get_adapter(job.connection)
    listing = job.listing
    if job.job_type == SyncJob.Type.PUBLISH_PRODUCT:
        payload = product_payload(listing.product)
        errors = adapter.validate_product(payload)
        if errors:
            raise AdapterError(" ".join(errors), needs_action=True)
        if listing.external_product_id:
            res = adapter.update_listing(listing.external_product_id, payload)
        else:
            res = adapter.create_listing(payload)
        listing.external_product_id = res["external_product_id"]
        listing.status = ChannelListing.Status.ACTIVE
        listing.last_error = ""
        listing.last_synced_at = timezone.now()
        listing.save()
    elif job.job_type == SyncJob.Type.UPDATE_INVENTORY:
        if listing.status != ChannelListing.Status.ACTIVE:
            return
        adapter.update_inventory(listing.external_product_id, job.sku.sku_code,
                                 _available(job.sku_id))
        listing.last_synced_at = timezone.now()
        listing.save(update_fields=["last_synced_at", "updated_at"])


def _set_listing(job, status, error=""):
    if job.job_type == SyncJob.Type.PUBLISH_PRODUCT and job.listing:
        job.listing.status = status
        job.listing.last_error = error[:300]
        job.listing.save()


def _fail(job, attempt, msg, retryable, needs_action):
    now = timezone.now()
    attempt.ok, attempt.error, attempt.retryable, attempt.finished_at = False, msg[:300], retryable, now
    attempt.save()
    job.last_error = msg[:300]
    if needs_action:
        job.status, job.finished_at = SyncJob.Status.NEEDS_ACTION, now
        _set_listing(job, ChannelListing.Status.NEEDS_ACTION, msg)
    elif retryable and job.attempts < job.max_attempts:
        job.status = SyncJob.Status.PENDING
        job.next_run_at = now + timedelta(seconds=backoff_seconds(job.attempts))
    else:
        job.status, job.finished_at = SyncJob.Status.FAILED, now
        _set_listing(job, ChannelListing.Status.FAILED, msg)
    job.save()


def process(job):
    attempt = SyncAttempt.objects.create(job=job)
    try:
        _run_job(job)
    except AdapterError as e:
        _fail(job, attempt, str(e), e.retryable, e.needs_action)
    except NotImplementedError:
        _fail(job, attempt, "Is channel ke liye ye kaam abhi supported nahi hai.", False, False)
    except Exception as e:  # unexpected: retry karo, par limit ke andar
        log.exception("sync job %s crashed", job.id)
        _fail(job, attempt, f"Unexpected error: {type(e).__name__}", True, False)
    else:
        now = timezone.now()
        attempt.ok, attempt.finished_at = True, now
        attempt.save()
        job.status, job.last_error, job.finished_at = SyncJob.Status.SUCCEEDED, "", now
        job.save()


def run_due(limit=100):
    n = 0
    while n < limit:
        job = claim_next()
        if job is None:
            break
        process(job)
        n += 1
    return n
