from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


class LedgerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = request.user.merchant
        entries = LedgerEntry.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        serializer = LedgerEntrySerializer(entries, many=True)
        return Response(serializer.data)
