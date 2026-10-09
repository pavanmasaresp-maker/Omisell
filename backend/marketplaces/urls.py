from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)
router.register("connections", views.ConnectionViewSet)
router.register("jobs", views.JobViewSet)
router.register("listings", views.ListingViewSet)
urlpatterns = router.urls + [path("publish", views.PublishView.as_view())]
