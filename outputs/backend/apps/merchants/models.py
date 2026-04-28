import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q


class Merchant(models.Model):
    """
    A merchant on the Playto Pay platform.
    Balance is NEVER stored as a column — it is always derived
    from credits minus debits in the LedgerEntry table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='merchant')
    business_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'merchants'

    def __str__(self):
        return self.business_name

    def get_balance_paise(self):
        """
        DB-level balance calculation. Never do Python arithmetic on fetched rows.
        sum(credits) - sum(debits) = available balance
        """
        from apps.ledger.models import LedgerEntry
        result = LedgerEntry.objects.filter(merchant=self).aggregate(
            total_credits=Sum('amount_paise', filter=Q(entry_type='credit')),
            total_debits=Sum('amount_paise', filter=Q(entry_type='debit')),
        )
        credits = result['total_credits'] or 0
        debits = result['total_debits'] or 0
        return credits - debits

    def get_held_balance_paise(self):
        """
        Held balance = sum of all pending/processing payouts.
        These are already debited in ledger but not yet settled.
        """
        from apps.payouts.models import Payout
        result = Payout.objects.filter(
            merchant=self,
            status__in=['pending', 'processing']
        ).aggregate(held=Sum('amount_paise'))
        return result['held'] or 0

    def get_available_balance_paise(self):
        """
        Available = ledger balance (already excludes held since holds = debits)
        """
        return self.get_balance_paise()


class BankAccount(models.Model):
    """
    Indian bank account for a merchant to receive payouts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='bank_accounts')
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_accounts'

    def __str__(self):
        return f"{self.bank_name} - {self.account_number[-4:].zfill(4)}"
