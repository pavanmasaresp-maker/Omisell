import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    CATALOG_MANAGER = "CATALOG_MANAGER", "Catalog Manager"
    INVENTORY_MANAGER = "INVENTORY_MANAGER", "Inventory Manager"
    ORDER_MANAGER = "ORDER_MANAGER", "Order Manager"
    VIEWER = "VIEWER", "Viewer"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", null=True, blank=True,
                               on_delete=models.CASCADE, related_name="users")
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.VIEWER)
