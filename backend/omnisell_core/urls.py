from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from accounts.views import GoogleLoginView, LoginView, MeView
from inventory.dashboard import DashboardView

urlpatterns = [
    path("healthz", lambda request: HttpResponse("ok")),  # Render health check
    path("admin/", admin.site.urls),
    path("api/v1/auth/login", LoginView.as_view()),
    path("api/v1/auth/google", GoogleLoginView.as_view()),
    path("api/v1/auth/me", MeView.as_view()),
    path("api/v1/dashboard", DashboardView.as_view()),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/channels/", include("marketplaces.urls")),
    path("api/v1/orders", include("orders.urls")),
    path("api/v1/", include("catalog.urls")),
]
