from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/token/', obtain_auth_token, name='api-token-auth'),
    path('api/v1/', include('apps.merchants.urls')),
    path('api/v1/', include('apps.payouts.urls')),
    path('api/v1/', include('apps.ledger.urls')),
]
