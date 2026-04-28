from rest_framework import serializers
from .models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['id', 'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'is_primary']


class MerchantDashboardSerializer(serializers.ModelSerializer):
    available_balance_paise = serializers.SerializerMethodField()
    available_balance_inr = serializers.SerializerMethodField()
    held_balance_paise = serializers.SerializerMethodField()
    held_balance_inr = serializers.SerializerMethodField()
    total_credits_paise = serializers.SerializerMethodField()
    total_debits_paise = serializers.SerializerMethodField()
    bank_accounts = BankAccountSerializer(many=True, read_only=True)

    class Meta:
        model = Merchant
        fields = [
            'id', 'business_name', 'email',
            'available_balance_paise', 'available_balance_inr',
            'held_balance_paise', 'held_balance_inr',
            'total_credits_paise', 'total_debits_paise',
            'bank_accounts',
        ]

    def get_available_balance_paise(self, obj):
        return obj.get_available_balance_paise()

    def get_available_balance_inr(self, obj):
        return obj.get_available_balance_paise() / 100

    def get_held_balance_paise(self, obj):
        return obj.get_held_balance_paise()

    def get_held_balance_inr(self, obj):
        return obj.get_held_balance_paise() / 100

    def get_total_credits_paise(self, obj):
        from django.db.models import Sum, Q
        result = obj.ledger_entries.aggregate(
            total=Sum('amount_paise', filter=Q(entry_type='credit'))
        )
        return result['total'] or 0

    def get_total_debits_paise(self, obj):
        from django.db.models import Sum, Q
        result = obj.ledger_entries.aggregate(
            total=Sum('amount_paise', filter=Q(entry_type='debit'))
        )
        return result['total'] or 0
