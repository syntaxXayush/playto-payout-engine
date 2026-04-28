from rest_framework import serializers
from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    amount_inr = serializers.SerializerMethodField()
    signed_amount_paise = serializers.SerializerMethodField()

    class Meta:
        model = LedgerEntry
        fields = [
            'id', 'entry_type', 'amount_paise', 'amount_inr',
            'signed_amount_paise', 'reference_type', 'reference_id',
            'description', 'created_at',
        ]

    def get_amount_inr(self, obj):
        return obj.amount_paise / 100

    def get_signed_amount_paise(self, obj):
        return obj.amount_paise if obj.entry_type == 'credit' else -obj.amount_paise
