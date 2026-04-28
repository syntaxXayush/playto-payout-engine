import uuid
from datetime import timedelta

from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.merchants.models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry
from .models import Payout, IdempotencyKey
from .serializers import PayoutSerializer, PayoutCreateSerializer
from django.conf import settings


class PayoutListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = request.user.merchant
        payouts = Payout.objects.filter(merchant=merchant).select_related('bank_account')
        serializer = PayoutSerializer(payouts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        POST /api/v1/payouts

        Critical path:
        1. Check idempotency key first (fast path for duplicates)
        2. Validate input
        3. Lock merchant's ledger with SELECT FOR UPDATE
        4. Check sufficient balance at DB level
        5. Create payout + ledger debit in ONE transaction
        6. Store idempotency key response

        The SELECT FOR UPDATE on step 3 prevents two simultaneous requests
        from both passing the balance check and both creating payouts.
        """
        merchant = request.user.merchant
        idempotency_key = request.headers.get('Idempotency-Key', '')

        # ── Step 1: Idempotency check ──────────────────────────────────────
        if idempotency_key:
            try:
                existing = IdempotencyKey.objects.get(
                    merchant=merchant,
                    key=idempotency_key,
                )
                if not existing.is_expired():
                    # Return exact same response as the first call
                    return Response(
                        existing.response_body,
                        status=existing.response_status
                    )
            except IdempotencyKey.DoesNotExist:
                pass  # first time we see this key

        # ── Step 2: Validate input ─────────────────────────────────────────
        serializer = PayoutCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount_paise = serializer.validated_data['amount_paise']
        bank_account_id = serializer.validated_data['bank_account_id']

        try:
            bank_account = BankAccount.objects.get(
                id=bank_account_id, merchant=merchant
            )
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Bank account not found or does not belong to this merchant'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ── Step 3-5: Atomic transaction with row-level lock ───────────────
        try:
            with transaction.atomic():
                # SELECT FOR UPDATE locks the merchant's ledger rows.
                # This is the database primitive that prevents overdraw.
                # Two concurrent requests will queue here. The second one
                # will see the updated balance AFTER the first commits.
                #
                # NOTE: We lock the Merchant row itself (not ledger rows)
                # to get a single, predictable lock point.
                locked_merchant = Merchant.objects.select_for_update().get(
                    pk=merchant.pk
                )

                # Balance computed at DB level — not Python arithmetic on fetched rows
                balance_data = LedgerEntry.objects.filter(
                    merchant=locked_merchant
                ).aggregate(
                    total_credits=Sum('amount_paise', filter=Q(entry_type='credit')),
                    total_debits=Sum('amount_paise', filter=Q(entry_type='debit')),
                )
                available = (balance_data['total_credits'] or 0) - (balance_data['total_debits'] or 0)

                if available < amount_paise:
                    error_response = {
                        'error': 'Insufficient balance',
                        'available_paise': available,
                        'requested_paise': amount_paise,
                    }
                    _store_idempotency_key(merchant, idempotency_key, 402, error_response)
                    return Response(error_response, status=status.HTTP_402_PAYMENT_REQUIRED)

                # Create the payout
                payout = Payout.objects.create(
                    merchant=locked_merchant,
                    bank_account=bank_account,
                    amount_paise=amount_paise,
                    status='pending',
                    idempotency_key=idempotency_key or str(uuid.uuid4()),
                )

                # Record the hold as a ledger debit (atomically)
                LedgerEntry.objects.create(
                    merchant=locked_merchant,
                    entry_type='debit',
                    amount_paise=amount_paise,
                    reference_type='payout_hold',
                    reference_id=payout.id,
                    description=f'Hold for payout {payout.id}',
                )

            # ── Step 6: Store idempotency response ─────────────────────────
            response_body = PayoutSerializer(payout).data
            # Convert UUIDs/datetimes to serializable form
            import json
            from rest_framework.renderers import JSONRenderer
            response_body = json.loads(JSONRenderer().render(response_body))
            _store_idempotency_key(merchant, idempotency_key, 201, response_body)

            return Response(response_body, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            # This catches the unique_together violation on IdempotencyKey
            # if two requests with the same key race to insert
            if idempotency_key:
                try:
                    existing = IdempotencyKey.objects.get(
                        merchant=merchant, key=idempotency_key
                    )
                    return Response(
                        existing.response_body,
                        status=existing.response_status
                    )
                except IdempotencyKey.DoesNotExist:
                    pass
            return Response(
                {'error': 'Conflict. Please retry.'},
                status=status.HTTP_409_CONFLICT
            )


def _store_idempotency_key(merchant, key: str, http_status: int, body: dict):
    if not key:
        return
    expiry_hours = getattr(settings, 'IDEMPOTENCY_KEY_EXPIRY_HOURS', 24)
    IdempotencyKey.objects.get_or_create(
        merchant=merchant,
        key=key,
        defaults={
            'response_status': http_status,
            'response_body': body,
            'expires_at': timezone.now() + timedelta(hours=expiry_hours),
        }
    )


class PayoutDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payout_id):
        try:
            payout = Payout.objects.get(id=payout_id, merchant=request.user.merchant)
            return Response(PayoutSerializer(payout).data)
        except Payout.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
