import uuid
from django.db import models
from django.utils import timezone


# ─── State machine definition ────────────────────────────────────────────────
VALID_TRANSITIONS = {
    'pending':    ['processing'],
    'processing': ['completed', 'failed'],
    # Terminal states: no transitions allowed
    'completed':  [],
    'failed':     [],
}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, [])


class Payout(models.Model):
    """
    Represents a merchant's withdrawal request.

    State machine: pending → processing → completed
                                        → failed

    Any other transition raises InvalidStateTransition.
    The hold is recorded as a LedgerEntry debit at creation time.
    On failure, a credit LedgerEntry is atomically created alongside
    the status change (inside a transaction).
    """
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    bank_account = models.ForeignKey(
        'merchants.BankAccount',
        on_delete=models.PROTECT,
        related_name='payouts'
    )
    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField(default=0)
    idempotency_key = models.CharField(max_length=100, db_index=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payouts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'status']),
            models.Index(fields=['status', 'processing_started_at']),
        ]

    def __str__(self):
        return f"Payout {self.id} | ₹{self.amount_paise/100:.2f} | {self.status}"

    def transition_to(self, new_status: str, reason: str = ''):
        """
        The ONLY way to change payout status. Enforces the state machine.
        Raises ValueError on illegal transitions.
        """
        if not is_valid_transition(self.status, new_status):
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status}. "
                f"Allowed from '{self.status}': {VALID_TRANSITIONS.get(self.status, [])}"
            )
        self.status = new_status
        if new_status == 'processing':
            self.processing_started_at = timezone.now()
        elif new_status == 'completed':
            self.completed_at = timezone.now()
        elif new_status == 'failed':
            self.failed_at = timezone.now()
            self.failure_reason = reason


class IdempotencyKey(models.Model):
    """
    Stores idempotency keys scoped per merchant.

    DB-level unique constraint on (merchant_id, key) ensures that even
    if two requests arrive simultaneously, only ONE can insert the row.
    The loser gets an IntegrityError which we catch and return the stored response.

    Keys expire after 24 hours and are purged by a nightly Celery Beat task.
    """
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.CASCADE,
        related_name='idempotency_keys'
    )
    key = models.CharField(max_length=100)
    response_status = models.IntegerField()        # HTTP status code (e.g. 201, 400)
    response_body = models.JSONField()             # exact response body
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'idempotency_keys'
        # THE critical constraint: prevents duplicate keys per merchant at DB level
        unique_together = [('merchant', 'key')]
        indexes = [
            models.Index(fields=['expires_at']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"IdempotencyKey {self.key[:8]}... for merchant {self.merchant_id}"
