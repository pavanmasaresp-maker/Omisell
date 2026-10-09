from django.urls import path
from . import views

urlpatterns = [
    path("", views.BalanceListView.as_view()),
    path("adjust", views.AdjustView.as_view()),
    path("ledger", views.LedgerListView.as_view()),
]
