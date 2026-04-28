from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import MerchantDashboardSerializer


class MerchantDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = request.user.merchant
        serializer = MerchantDashboardSerializer(merchant)
        return Response(serializer.data)


class MerchantListView(APIView):
    """Returns all merchants — used by frontend merchant switcher."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import Merchant
        merchants = Merchant.objects.all()
        serializer = MerchantDashboardSerializer(merchants, many=True)
        return Response(serializer.data)
