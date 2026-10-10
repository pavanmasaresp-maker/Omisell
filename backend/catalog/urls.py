from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# bulk-import FIRST: router's "products/<pk>" pattern (trailing_slash=False,
# pk regex [^/.]+) would otherwise swallow "products/bulk-import" as if
# "bulk-import" were a pk — same class of bug we hit with orders/returns.
urlpatterns = [
    path("products/bulk-import", views.BulkImportView.as_view()),
]

router = DefaultRouter(trailing_slash=False)
router.register("categories", views.CategoryViewSet)
router.register("products", views.ProductViewSet)
router.register("variants", views.VariantViewSet)
router.register("skus", views.SKUViewSet)
router.register("media", views.MediaViewSet)
urlpatterns += router.urls
