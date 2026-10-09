from django.contrib import admin
from .models import InventoryBalance, InventoryLedger

admin.site.register(InventoryBalance)
admin.site.register(InventoryLedger)
