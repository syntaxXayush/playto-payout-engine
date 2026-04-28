from rest_framework import serializers
from .models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    amount_inr = serializers.SerializerMethodField()
    bank_account_display = serializers.SerializerMethodField()

    class Meta:
        model = Payout
        fields = [
            'id', 'amount_paise', 'amount_inr', 'status',
            'bank_account', 'bank_account_display',
            'retry_count', 'failure_reason',
            'created_at', 'processing_started_at', 'completed_at', 'failed_at',
        ]

    def get_amount_inr(self, obj):
        return obj.amount_paise / 100

    def get_bank_account_display(self, obj):
        ba = obj.bank_account
        return f"{ba.bank_name} •••• {ba.account_number[-4:]}"


class PayoutCreateSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=100)  # min 1 INR
    bank_account_id = serializers.UUIDField()
