from django.urls import path
from .views import MerchantDashboardView, MerchantListView

urlpatterns = [
    path('merchants/me/', MerchantDashboardView.as_view(), name='merchant-dashboard'),
    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
]
