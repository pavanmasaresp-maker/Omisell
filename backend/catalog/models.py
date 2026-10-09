import uuid
from django.db import models


class TimeStamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStamped):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="children")

    class Meta:
        unique_together = [("tenant", "name", "parent")]

    def __str__(self):
        return self.name


class Product(TimeStamped):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        ACTIVE = "ACTIVE"
        ARCHIVED = "ARCHIVED"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    attributes = models.JSONField(default=dict, blank=True)  # e.g. {"material": "cotton"}
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [models.Index(fields=["tenant", "status"])]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.version += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Variant(TimeStamped):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=200)  # e.g. "Red / M"
    options = models.JSONField(default=dict, blank=True)  # {"color": "Red", "size": "M"}

    def __str__(self):
        return f"{self.product_id}:{self.name}"


class SKU(TimeStamped):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="skus")
    sku_code = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mrp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "sku_code"], name="uniq_tenant_sku")]
        indexes = [models.Index(fields=["tenant", "sku_code"])]

    def __str__(self):
        return self.sku_code


class ProductMedia(TimeStamped):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    url = models.URLField(max_length=1000)  # file upload / S3 baad mein
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]
