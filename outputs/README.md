# Playto Payout Engine

> Minimal but production-grade payout engine for Indian merchants collecting international payments. Built for the Playto Pay Founding Engineer Challenge.

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Django 5.1 + DRF |
| Database | PostgreSQL 16 |
| Workers | Celery 5 + Redis 7 |
| Scheduler | Celery Beat + django-celery-beat |
| Frontend | React 18 + Tailwind CSS + Framer Motion |
| Auth | DRF Token Authentication |

---

## Running with Docker (Recommended — 1 command)

### Prerequisites
- Docker Desktop installed and running
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/playto-payout-engine.git
cd playto-payout-engine

# 2. Start everything (DB + Redis + Django + Celery Worker + Celery Beat + React)
docker compose up --build

# 3. Open the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/v1/
# Django Admin: http://localhost:8000/admin/
```

Docker will automatically:
- Run migrations
- Seed 3 merchants with credit history
- Start the Celery worker (processes payouts)
- Start Celery Beat (schedules periodic tasks every 10s)

### Demo Accounts (all password: `playto@123`)
| Username | Business | Starting Balance |
|---|---|---|
| `designhive` | DesignHive Studio | ~₹3,50,000 |
| `devcraft` | DevCraft Labs | ~₹4,20,000 |
| `contentwave` | ContentWave Agency | ~₹2,80,000 |

---

## Running Locally (without Docker)

### Prerequisites
- Python 3.12+
- PostgreSQL 16 running locally
- Redis running locally (`redis-server`)
- Node.js 20+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your DB credentials

# Run migrations
python manage.py migrate

# Seed merchants
python manage.py seed_merchants

# Start Django dev server
python manage.py runserver
```

### Celery Workers (open 2 separate terminals)

```bash
# Terminal 1 — Worker (processes tasks)
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info

# Terminal 2 — Beat (schedules periodic tasks)
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# Start dev server
npm run dev
# Open http://localhost:5173
```

---

## Environment Variables

### Backend `.env`

```env
SECRET_KEY=your-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# PostgreSQL
DB_NAME=playto_payout
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOW_ALL_ORIGINS=True
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## API Reference

All endpoints require `Authorization: Token <token>` header.

### Auth
```
POST /api/v1/auth/token/
Body: { "username": "designhive", "password": "playto@123" }
Returns: { "token": "abc123..." }
```

### Merchant Dashboard
```
GET /api/v1/merchants/me/
Returns: balance, held_balance, bank_accounts
```

### Ledger
```
GET /api/v1/ledger/
Returns: last 50 credit/debit entries
```

### Payouts
```
GET  /api/v1/payouts/           — list all payouts
POST /api/v1/payouts/           — create payout request
  Headers: Idempotency-Key: <uuid-v4>
  Body: { "amount_paise": 50000, "bank_account_id": "<uuid>" }

GET  /api/v1/payouts/<id>/      — get single payout
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest apps/payouts/tests.py -v

# Or run all tests
pytest -v
```

### Test Coverage
- **Concurrency test** — two simultaneous 60 INR requests on 100 INR balance → exactly one succeeds
- **Idempotency test (×2)** — same key → same response, no duplicate payout
- **State machine test** — all valid/invalid transitions verified
- **Ledger invariant test** — sum(credits) − sum(debits) == balance

---

## Payout Lifecycle

```
POST /api/v1/payouts/
       │
       ▼
   [pending]  ←── funds held (debit in ledger)
       │
       ▼  (Celery Beat picks up every 10s)
  [processing]
       │
    ┌──┴──────────────┐
    │                 │
    ▼ (70%)          ▼ (20%)        10% → stuck → retried after 30s
[completed]       [failed]
                     │
                     ▼
              funds refunded (credit in ledger, atomic)
```

---

## Project Structure

```
playto-payout-engine/
├── docker-compose.yml
├── .env.example
├── README.md
├── EXPLAINER.md
│
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── apps/
│   │   ├── merchants/     — Merchant, BankAccount models + dashboard API
│   │   ├── ledger/        — LedgerEntry model + ledger API
│   │   └── payouts/       — Payout, IdempotencyKey models + tasks + tests
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/
    └── src/
        ├── components/    — BalanceCard, PayoutForm, PayoutTable, LedgerFeed, Header
        ├── pages/         — Dashboard, Login
        └── lib/api.js     — Axios client
```
