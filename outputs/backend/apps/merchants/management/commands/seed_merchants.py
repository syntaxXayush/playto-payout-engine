import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.merchants.models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry

MERCHANTS_DATA = [
    {
        'username': 'designhive',
        'email': 'studio@designhive.in',
        'business_name': 'DesignHive Studio',
        'bank': {
            'account_holder_name': 'Arjun Mehta',
            'account_number': '9876543210001',
            'ifsc_code': 'HDFC0001234',
            'bank_name': 'HDFC Bank',
        },
    },
    {
        'username': 'devcraft',
        'email': 'hello@devcraft.io',
        'business_name': 'DevCraft Labs',
        'bank': {
            'account_holder_name': 'Priya Sharma',
            'account_number': '1234567890002',
            'ifsc_code': 'ICIC0005678',
            'bank_name': 'ICICI Bank',
        },
    },
    {
        'username': 'contentwave',
        'email': 'ops@contentwave.co',
        'business_name': 'ContentWave Agency',
        'bank': {
            'account_holder_name': 'Rahul Gupta',
            'account_number': '5555666677770',
            'ifsc_code': 'SBIN0009012',
            'bank_name': 'State Bank of India',
        },
    },
]

CREDIT_DESCRIPTIONS = [
    'Payment from US client – Figma redesign',
    'Retainer invoice – Q1 2025',
    'Website redesign milestone payment',
    'API integration project – final invoice',
    'SEO campaign – monthly retainer',
    'Content writing batch – 20 articles',
    'UI/UX consultation – 10 hours',
    'Mobile app prototype payment',
    'Brand identity project – 50% advance',
]

class Command(BaseCommand):
    help = 'Seed 3 merchants with realistic credit history'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding merchants...\n')
        for data in MERCHANTS_DATA:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'email': data['email']}
            )
            if created:
                user.set_password('playto@123')
                user.save()

            token, _ = Token.objects.get_or_create(user=user)

            merchant, _ = Merchant.objects.get_or_create(
                email=data['email'],
                defaults={'user': user, 'business_name': data['business_name']}
            )

            BankAccount.objects.get_or_create(
                merchant=merchant,
                account_number=data['bank']['account_number'],
                defaults={**data['bank'], 'is_primary': True}
            )

            # Only seed credits if none exist
            if not LedgerEntry.objects.filter(merchant=merchant).exists():
                for _ in range(random.randint(5, 8)):
                    amount_usd = random.choice([500, 750, 1000, 1500, 2000, 3000])
                    amount_paise = amount_usd * 8400
                    LedgerEntry.objects.create(
                        merchant=merchant,
                        entry_type='credit',
                        amount_paise=amount_paise,
                        reference_type='customer_payment',
                        description=random.choice(CREDIT_DESCRIPTIONS),
                    )

            balance = merchant.get_balance_paise()
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✅ {merchant.business_name}\n'
                    f'     Token : {token.key}\n'
                    f'     Balance: ₹{balance/100:,.2f}\n'
                )
            )
        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete! Password for all: playto@123\n'))
