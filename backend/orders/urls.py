from django.urls import path
from .views import OrderViewSet, ReturnViewSet

order_list = OrderViewSet.as_view({"get": "list", "post": "create"})
order_detail = OrderViewSet.as_view({"get": "retrieve"})
order_confirm = OrderViewSet.as_view({"post": "confirm"})
order_pack = OrderViewSet.as_view({"post": "pack"})
order_ship = OrderViewSet.as_view({"post": "ship"})
order_deliver = OrderViewSet.as_view({"post": "deliver"})
order_cancel = OrderViewSet.as_view({"post": "cancel"})

return_list = ReturnViewSet.as_view({"get": "list", "post": "create"})
return_decide = ReturnViewSet.as_view({"post": "decide"})

# No DRF router here on purpose: a router's empty-prefix ("") list/create route
# needs a trailing slash to match, but the rest of this project (and the
# mobile app) consistently calls endpoints WITHOUT a trailing slash
# (APPEND_SLASH=False, DefaultRouter(trailing_slash=False) everywhere else).
# Explicit paths below avoid that empty-prefix ambiguity entirely.
urlpatterns = [
    path("/returns", return_list),
    path("/returns/<uuid:pk>/decide", return_decide),
    path("", order_list),
    path("/<uuid:pk>", order_detail),
    path("/<uuid:pk>/confirm", order_confirm),
    path("/<uuid:pk>/pack", order_pack),
    path("/<uuid:pk>/ship", order_ship),
    path("/<uuid:pk>/deliver", order_deliver),
    path("/<uuid:pk>/cancel", order_cancel),
]
