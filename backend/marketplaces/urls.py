from django.urls import path
from rest_framework.routers import DefaultRouter
from . import shopify_oauth, views

router = DefaultRouter(trailing_slash=False)
router.register("connections", views.ConnectionViewSet)
router.register("jobs", views.JobViewSet)
router.register("listings", views.ListingViewSet)
urlpatterns = router.urls + [
    path("publish", views.PublishView.as_view()),
    path("shopify/config", shopify_oauth.ShopifyConfigView.as_view()),
    path("shopify/start", shopify_oauth.ShopifyStartView.as_view()),
    path("shopify/callback", shopify_oauth.ShopifyCallbackView.as_view()),
]
