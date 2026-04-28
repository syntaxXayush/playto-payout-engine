from django.urls import path
from .views import LedgerListView

urlpatterns = [
    path('ledger/', LedgerListView.as_view(), name='ledger-list'),
]
