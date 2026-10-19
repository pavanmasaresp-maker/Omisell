from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from accounts.views import GoogleLoginView, LoginView, MeView
from inventory.dashboard import DashboardView, OverviewView
from . import public
from .exports import OrdersCsvView, StockCsvView

urlpatterns = [
    path("healthz", lambda request: HttpResponse("ok")),  # Render health check
    path("privacy", public.privacy),
    path("account-delete", public.account_delete),
    path("api/v1/export/orders.csv", OrdersCsvView.as_view()),
    path("api/v1/export/stock.csv", StockCsvView.as_view()),
    path("admin/", admin.site.urls),
    path("api/v1/auth/login", LoginView.as_view()),
    path("api/v1/auth/google", GoogleLoginView.as_view()),
    path("api/v1/auth/me", MeView.as_view()),
    path("api/v1/dashboard", DashboardView.as_view()),
    path("api/v1/dashboard/overview", OverviewView.as_view()),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/channels/", include("marketplaces.urls")),
    path("api/v1/orders", include("orders.urls")),
    path("api/v1/", include("catalog.urls")),
]


# --- health check (Sentinel) ---
from django.http import JsonResponse
from django.urls import path as _health_path


def health(request):
    return JsonResponse({"ok": True})


urlpatterns = [_health_path("health", health), _health_path("health/", health)] + list(urlpatterns)
