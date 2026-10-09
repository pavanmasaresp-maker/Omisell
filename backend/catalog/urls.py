from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)
router.register("categories", views.CategoryViewSet)
router.register("products", views.ProductViewSet)
router.register("variants", views.VariantViewSet)
router.register("skus", views.SKUViewSet)
router.register("media", views.MediaViewSet)
urlpatterns = router.urls
