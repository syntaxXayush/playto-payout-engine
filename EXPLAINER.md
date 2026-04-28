# EXPLAINER.md — Playto Payout Engine

---

## 1. The Ledger

**Balance calculation query:**

```python
# apps/merchants/models.py — Merchant.get_balance_paise()

from django.db.models import Sum, Q

result = LedgerEntry.objects.filter(merchant=self).aggregate(
    total_credits=Sum('amount_paise', filter=Q(entry_type='credit')),
    total_debits=Sum('amount_paise', filter=Q(entry_type='debit')),
)
credits = result['total_credits'] or 0
debits  = result['total_debits']  or 0
return credits - debits
```

**Why credits and debits as separate rows, not a balance column?**

A stored balance column is dangerous in a payment system because it can silently drift. If a bug, a failed transaction, or a direct DB edit changes the column without a corresponding ledger entry, the balance lies and you have no audit trail to recover from. By modelling every money movement as an immutable ledger row (credit or debit), the balance is always a *derived* fact — it can be recomputed from scratch at any time and must always match. This is the same pattern used by banks, Stripe, and every serious payment system. The invariant `sum(credits) − sum(debits) == displayed balance` becomes checkable and enforceable.

We store amounts as `BigIntegerField` in **paise** (integer), never `FloatField` or `DecimalField`. Integer arithmetic on paise is exact. Floats introduce rounding errors (0.1 + 0.2 ≠ 0.3 in IEEE 754), which is unacceptable for money. Integers have no such issue.

---

## 2. The Lock

**Code that prevents two concurrent payouts from overdrawing a balance:**

```python
# apps/payouts/views.py — PayoutListCreateView.post()

with transaction.atomic():
    # SELECT FOR UPDATE locks the Merchant row at the database level.
    # Any second transaction that tries to lock the same row will BLOCK here
    # and wait until the first transaction commits or rolls back.
    # This means the second request sees the UPDATED balance after the first
    # transaction has already created the debit entry — not the stale balance
    # from before. This eliminates the check-then-deduct race condition.
    locked_merchant = Merchant.objects.select_for_update().get(pk=merchant.pk)

    # Balance computed at DB level inside the lock — never Python arithmetic
    # on pre-fetched rows
    balance_data = LedgerEntry.objects.filter(merchant=locked_merchant).aggregate(
        total_credits=Sum('amount_paise', filter=Q(entry_type='credit')),
        total_debits=Sum('amount_paise', filter=Q(entry_type='debit')),
    )
    available = (balance_data['total_credits'] or 0) - (balance_data['total_debits'] or 0)

    if available < amount_paise:
        return Response({'error': 'Insufficient balance'}, status=402)

    # Create payout + debit entry inside the same transaction
    payout = Payout.objects.create(...)
    LedgerEntry.objects.create(entry_type='debit', ...)
```

**What database primitive does this rely on?**

`SELECT FOR UPDATE` is a PostgreSQL row-level exclusive lock. When transaction A acquires it on the Merchant row, transaction B's `SELECT FOR UPDATE` on the same row blocks at the database level — not at the Python/Django level — until A commits. This is critical: Python-level checks (`if balance >= amount`) followed by a separate write are not atomic and will race. The database lock makes the check-then-deduct a single atomic unit. This correctly handles the scenario: merchant with ₹100 submits two simultaneous ₹60 requests — exactly one succeeds, the other sees ₹40 remaining and is rejected.

---

## 3. The Idempotency

**How the system knows it has seen a key before:**

```python
# apps/payouts/models.py — IdempotencyKey model

class IdempotencyKey(models.Model):
    merchant   = models.ForeignKey(Merchant, ...)
    key        = models.CharField(max_length=100)
    response_status = models.IntegerField()   # exact HTTP status code
    response_body   = models.JSONField()      # exact response body
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = [('merchant', 'key')]  # DB-level uniqueness constraint
```

```python
# apps/payouts/views.py — lookup before doing any work

existing = IdempotencyKey.objects.get(merchant=merchant, key=idempotency_key)
if not existing.is_expired():
    return Response(existing.response_body, status=existing.response_status)
```

**What happens if the first request is still in-flight when the second arrives?**

The `unique_together` constraint creates a unique index in PostgreSQL on `(merchant_id, key)`. If two requests arrive simultaneously and both try to INSERT a new `IdempotencyKey` row, PostgreSQL guarantees that exactly one INSERT succeeds and the other raises an `IntegrityError`. We catch that `IntegrityError` in the view and immediately do a GET on the same key to return the stored response. This means we never need a Python-level mutex or Redis lock — the database itself is the serialisation point. Keys are scoped per merchant (so the same UUID from two different merchants does not conflict) and expire after 24 hours via a nightly Celery Beat cleanup task.

---

## 4. The State Machine

**Where is `failed → completed` (and every other illegal transition) blocked?**

```python
# apps/payouts/models.py

VALID_TRANSITIONS = {
    'pending':    ['processing'],
    'processing': ['completed', 'failed'],
    'completed':  [],   # terminal — no transitions allowed
    'failed':     [],   # terminal — no transitions allowed
}

def is_valid_transition(current_status: str, new_status: str) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, [])


class Payout(models.Model):
    ...
    def transition_to(self, new_status: str, reason: str = ''):
        # THIS LINE blocks every illegal transition:
        if not is_valid_transition(self.status, new_status):
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status}. "
                f"Allowed from '{self.status}': {VALID_TRANSITIONS.get(self.status, [])}"
            )
        self.status = new_status
        ...
```

`transition_to()` is the **only** method that modifies `status`. Direct assignment `payout.status = 'completed'` is never used anywhere in the codebase — all status changes go through this guard. A failed payout returning funds does so atomically: `_fail_and_refund()` calls `transition_to('failed')` and creates the credit `LedgerEntry` inside a single `transaction.atomic()` block — either both happen or neither does.

---

## 5. The AI Audit

**What AI originally suggested:**

When I asked an AI assistant to write the balance check and payout creation logic, it produced this:

```python
# ❌ AI-generated code — WRONG (race condition)
def post(self, request):
    merchant = request.user.merchant
    balance = merchant.get_balance_paise()  # fetch balance in Python

    if balance < amount_paise:              # Python-level check
        return Response({'error': 'Insufficient balance'}, status=400)

    # RACE WINDOW: between the check above and the write below,
    # another request can pass the same check with the same stale balance.
    Payout.objects.create(merchant=merchant, amount_paise=amount_paise, ...)
    LedgerEntry.objects.create(entry_type='debit', ...)
```

**Why it was wrong:**

This is a classic check-then-act race condition (TOCTOU — Time Of Check, Time Of Use). Two requests arriving within milliseconds both call `get_balance_paise()`, both see ₹100, both pass the `< 60` check, and both proceed to create a payout. The merchant ends up with −₹20 balance and two debits totalling ₹120 on a ₹100 balance. No Python-level lock fixes this — the check and the write must be atomic at the **database** level.

**What I replaced it with:**

```python
# ✅ Correct — SELECT FOR UPDATE makes check + deduct atomic
with transaction.atomic():
    locked_merchant = Merchant.objects.select_for_update().get(pk=merchant.pk)

    balance_data = LedgerEntry.objects.filter(merchant=locked_merchant).aggregate(
        total_credits=Sum('amount_paise', filter=Q(entry_type='credit')),
        total_debits=Sum('amount_paise', filter=Q(entry_type='debit')),
    )
    available = (balance_data['total_credits'] or 0) - (balance_data['total_debits'] or 0)

    if available < amount_paise:
        return Response({'error': 'Insufficient balance'}, status=402)

    payout = Payout.objects.create(...)
    LedgerEntry.objects.create(entry_type='debit', ...)
    # Transaction commits here — lock released — second request now unblocks
    # and sees the updated (reduced) balance
```

The `SELECT FOR UPDATE` acquires a row-level exclusive lock on the Merchant row at the database level. The second concurrent request blocks at that line — it cannot proceed until the first transaction commits. When it does unblock, it recomputes the balance from the now-updated ledger rows and correctly sees insufficient funds.
