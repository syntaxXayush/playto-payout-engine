import random
import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.ledger.models import LedgerEntry

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def process_pending_payouts(self):
    """
    Picks up ALL pending payouts and dispatches each to its own task.
    Runs every 10 seconds via Celery Beat.
    """
    from .models import Payout
    pending = Payout.objects.filter(status='pending').values_list('id', flat=True)
    count = 0
    for payout_id in pending:
        process_single_payout.delay(str(payout_id))
        count += 1
    if count:
        logger.info(f"Dispatched {count} pending payouts")
    return count


@shared_task(bind=True)
def process_single_payout(self, payout_id: str):
    """
    Processes a single payout through the state machine.
    70% success, 20% failure, 10% hung (do nothing, let retry_stuck_payouts handle it).
    """
    from .models import Payout

    try:
        with transaction.atomic():
            # Lock the payout row to prevent concurrent processing
            payout = Payout.objects.select_for_update(nowait=True).get(id=payout_id)

            if payout.status != 'pending':
                logger.info(f"Payout {payout_id} is already {payout.status}, skipping")
                return

            # Transition: pending → processing
            payout.transition_to('processing')
            payout.save()

        # Simulate bank settlement (outside the lock — this is the "network call")
        outcome = _simulate_bank_settlement()
        logger.info(f"Payout {payout_id}: bank outcome = {outcome}")

        if outcome == 'hung':
            # Do nothing. retry_stuck_payouts will handle this after 30s.
            return

        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)

            if payout.status != 'processing':
                logger.warning(f"Payout {payout_id} status changed during settlement, skipping")
                return

            if outcome == 'success':
                payout.transition_to('completed')
                payout.save()
                logger.info(f"Payout {payout_id} completed")

            elif outcome == 'failure':
                _fail_and_refund(payout, reason='Bank declined the transfer')

    except Payout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
    except Exception as exc:
        logger.error(f"Error processing payout {payout_id}: {exc}", exc_info=True)


@shared_task(bind=True)
def retry_stuck_payouts(self):
    """
    Finds payouts stuck in 'processing' for > PAYOUT_STUCK_THRESHOLD_SECONDS.
    Retries up to PAYOUT_MAX_RETRY_ATTEMPTS times with exponential backoff.
    After max retries: marks as failed and refunds funds atomically.
    """
    from .models import Payout

    threshold = getattr(settings, 'PAYOUT_STUCK_THRESHOLD_SECONDS', 30)
    max_retries = getattr(settings, 'PAYOUT_MAX_RETRY_ATTEMPTS', 3)

    cutoff = timezone.now() - timedelta(seconds=threshold)
    stuck = Payout.objects.filter(
        status='processing',
        processing_started_at__lte=cutoff,
    )

    for payout in stuck:
        if payout.retry_count >= max_retries:
            with transaction.atomic():
                p = Payout.objects.select_for_update().get(pk=payout.pk)
                if p.status == 'processing':
                    _fail_and_refund(p, reason=f'Exceeded max retries ({max_retries})')
            logger.warning(f"Payout {payout.id} permanently failed after {max_retries} retries")
        else:
            with transaction.atomic():
                p = Payout.objects.select_for_update().get(pk=payout.pk)
                if p.status == 'processing':
                    p.retry_count += 1
                    p.status = 'pending'  # reset to pending for re-pickup
                    p.processing_started_at = None
                    p.save()
            # Exponential backoff: 2^retry_count seconds
            backoff = 2 ** payout.retry_count
            logger.info(f"Payout {payout.id} retry {payout.retry_count + 1}, backoff {backoff}s")


@shared_task
def cleanup_expired_idempotency_keys():
    """Purges idempotency keys older than 24 hours. Runs nightly."""
    from .models import IdempotencyKey
    deleted_count, _ = IdempotencyKey.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()
    logger.info(f"Cleaned up {deleted_count} expired idempotency keys")
    return deleted_count


def _simulate_bank_settlement() -> str:
    """
    Simulates bank response:
    70% → success
    20% → failure
    10% → hung (no response)
    """
    roll = random.random()
    if roll < 0.70:
        return 'success'
    elif roll < 0.90:
        return 'failure'
    else:
        return 'hung'


def _fail_and_refund(payout, reason: str):
    """
    ATOMIC: transitions payout to failed AND creates a credit LedgerEntry
    to restore the merchant's held funds.

    This MUST be called inside a transaction.atomic() block with the payout
    already locked via select_for_update().
    """
    payout.transition_to('failed', reason=reason)
    payout.save()

    # Restore funds — atomic with the status transition
    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type='credit',
        amount_paise=payout.amount_paise,
        reference_type='payout_refund',
        reference_id=payout.id,
        description=f'Refund for failed payout {payout.id}: {reason}',
    )
    logger.info(f"Payout {payout.id} failed and {payout.amount_paise} paise refunded")
