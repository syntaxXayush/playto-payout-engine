import uuid
from django.db import models


class LedgerEntry(models.Model):
    """
    Immutable double-entry ledger. Every money movement creates a row here.
    Credits = money coming in (customer payments).
    Debits  = money going out (payout holds, fees).

    INVARIANT: sum(credits) - sum(debits) == merchant balance (always).

    We use BigIntegerField for paise. Never FloatField. Never DecimalField.
    Integer arithmetic on paise is exact. Floats are not.
    """
    ENTRY_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    REFERENCE_TYPE_CHOICES = [
        ('customer_payment', 'Customer Payment'),
        ('payout_hold', 'Payout Hold'),
        ('payout_refund', 'Payout Refund'),
        ('fee', 'Fee'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount_paise = models.BigIntegerField()  # ALWAYS in paise, ALWAYS positive
    reference_type = models.CharField(max_length=30, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.UUIDField(null=True, blank=True)  # e.g. payout UUID
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ledger_entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'entry_type']),
            models.Index(fields=['merchant', 'created_at']),
        ]

    def __str__(self):
        sign = '+' if self.entry_type == 'credit' else '-'
        return f"{sign}₹{self.amount_paise / 100:.2f} ({self.reference_type})"

    def save(self, *args, **kwargs):
        if self.amount_paise <= 0:
            raise ValueError("LedgerEntry amount_paise must be a positive integer")
        super().save(*args, **kwargs)
