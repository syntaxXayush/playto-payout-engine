"""
Two critical tests:
1. Concurrency: two simultaneous 60 INR requests from a 100 INR merchant → exactly one succeeds
2. Idempotency: two requests with the same key → same response, no duplicate payout
"""
import uuid
import threading
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.merchants.models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry
from apps.payouts.models import Payout, IdempotencyKey


def make_merchant(username='testmerchant', balance_paise=10000):
    """Helper: create merchant with given balance."""
    user = User.objects.create_user(username=username, password='test123')
    token = Token.objects.create(user=user)
    merchant = Merchant.objects.create(
        user=user, business_name='Test Co', email=f'{username}@test.com'
    )
    bank = BankAccount.objects.create(
        merchant=merchant,
        account_holder_name='Test User',
        account_number='1234567890',
        ifsc_code='HDFC0001234',
        bank_name='HDFC Bank',
        is_primary=True,
    )
    if balance_paise > 0:
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type='credit',
            amount_paise=balance_paise,
            reference_type='customer_payment',
            description='Test credit',
        )
    return merchant, bank, token.key


class ConcurrencyTest(TransactionTestCase):
    """
    TransactionTestCase (not TestCase) is required because:
    - select_for_update() only works inside a real transaction
    - TestCase wraps everything in a single transaction, making locks invisible
    - TransactionTestCase commits each transaction, making locks real
    """

    def test_two_concurrent_payouts_exactly_one_succeeds(self):
        """
        Merchant has ₹100 (10000 paise).
        Two threads simultaneously request ₹60 (6000 paise) payouts.
        Exactly ONE should succeed. The other must be rejected.
        """
        merchant, bank, token = make_merchant('concurrent_test', balance_paise=10000)

        results = []
        errors = []

        def make_payout():
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
            response = client.post(
                '/api/v1/payouts/',
                data={'amount_paise': 6000, 'bank_account_id': str(bank.id)},
                headers={'Idempotency-Key': str(uuid.uuid4())},
                format='json',
            )
            results.append(response.status_code)

        t1 = threading.Thread(target=make_payout)
        t2 = threading.Thread(target=make_payout)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one 201, one 402
        self.assertEqual(len(results), 2)
        success_count = results.count(201)
        failure_count = results.count(402)
        self.assertEqual(success_count, 1, f"Expected 1 success, got {results}")
        self.assertEqual(failure_count, 1, f"Expected 1 failure, got {results}")

        # Verify ledger invariant: balance = credits - debits
        final_balance = merchant.get_balance_paise()
        payout_count = Payout.objects.filter(merchant=merchant).count()
        self.assertEqual(payout_count, 1)
        self.assertEqual(final_balance, 10000 - 6000)  # 4000 paise held


class IdempotencyTest(TestCase):

    def test_same_idempotency_key_returns_same_response(self):
        """
        Two requests with the same Idempotency-Key:
        - Must return the exact same response body and status code
        - Must NOT create a duplicate payout
        """
        merchant, bank, token = make_merchant('idempotency_test', balance_paise=10000)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        idem_key = str(uuid.uuid4())

        resp1 = client.post(
            '/api/v1/payouts/',
            data={'amount_paise': 5000, 'bank_account_id': str(bank.id)},
            HTTP_IDEMPOTENCY_KEY=idem_key,
            format='json',
        )
        resp2 = client.post(
            '/api/v1/payouts/',
            data={'amount_paise': 5000, 'bank_account_id': str(bank.id)},
            HTTP_IDEMPOTENCY_KEY=idem_key,
            format='json',
        )

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp1.data['id'], resp2.data['id'])  # same payout ID
        self.assertEqual(
            Payout.objects.filter(merchant=merchant).count(), 1
        )  # only ONE payout created

    def test_different_keys_create_different_payouts(self):
        merchant, bank, token = make_merchant('idempotency_test2', balance_paise=20000)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp1 = client.post(
            '/api/v1/payouts/',
            data={'amount_paise': 5000, 'bank_account_id': str(bank.id)},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            format='json',
        )
        resp2 = client.post(
            '/api/v1/payouts/',
            data={'amount_paise': 5000, 'bank_account_id': str(bank.id)},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            format='json',
        )

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertNotEqual(resp1.data['id'], resp2.data['id'])
        self.assertEqual(Payout.objects.filter(merchant=merchant).count(), 2)


class StateMachineTest(TestCase):

    def test_invalid_transition_raises(self):
        from apps.payouts.models import is_valid_transition
        # Legal transitions
        self.assertTrue(is_valid_transition('pending', 'processing'))
        self.assertTrue(is_valid_transition('processing', 'completed'))
        self.assertTrue(is_valid_transition('processing', 'failed'))
        # Illegal transitions
        self.assertFalse(is_valid_transition('completed', 'pending'))
        self.assertFalse(is_valid_transition('failed', 'completed'))
        self.assertFalse(is_valid_transition('completed', 'failed'))
        self.assertFalse(is_valid_transition('pending', 'completed'))

    def test_ledger_invariant(self):
        """sum(credits) - sum(debits) == displayed balance, always."""
        merchant, bank, token = make_merchant('invariant_test', balance_paise=50000)
        # The balance should be exactly 50000
        self.assertEqual(merchant.get_balance_paise(), 50000)
        # Add another credit
        LedgerEntry.objects.create(
            merchant=merchant, entry_type='credit',
            amount_paise=10000, reference_type='customer_payment',
            description='Second payment'
        )
        self.assertEqual(merchant.get_balance_paise(), 60000)
