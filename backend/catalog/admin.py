from django.contrib import admin
from .models import SKU, Category, Product, ProductMedia, Variant

for m in (Category, Product, Variant, SKU, ProductMedia):
    admin.site.register(m)
