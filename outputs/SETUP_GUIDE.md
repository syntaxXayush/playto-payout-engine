# Complete Setup Guide — Step by Step

## OPTION A: Docker (Easiest — do this first)

### Step 1 — Install Docker Desktop
Download from: https://www.docker.com/products/docker-desktop/
Make sure it's running (whale icon in taskbar/menubar)

### Step 2 — Clone and create .env files

```bash
git clone https://github.com/YOUR_USERNAME/playto-payout-engine.git
cd playto-payout-engine
```

Create backend .env:
```bash
cat > backend/.env << 'ENVEOF'
SECRET_KEY=3xGh9@kL2mPqRs7vWxYz1bCdEfJnOuTw
DEBUG=True
ALLOWED_HOSTS=*
DB_NAME=playto_payout
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CORS_ALLOW_ALL_ORIGINS=True
ENVEOF
```

Create frontend .env:
```bash
cat > frontend/.env << 'ENVEOF'
VITE_API_URL=http://localhost:8000/api/v1
ENVEOF
```

### Step 3 — Start everything
```bash
docker compose up --build
```

Wait ~60 seconds for first build. You'll see:
- `✅ DesignHive Studio` — seeded
- `✅ DevCraft Labs` — seeded
- `✅ ContentWave Agency` — seeded
- `celery_beat` saying "beat: Starting..."

### Step 4 — Open the app
- Frontend: http://localhost:5173
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/ (create superuser below)

### Create Django superuser (optional, for admin panel)
```bash
docker compose exec backend python manage.py createsuperuser
```

### Stop everything
```bash
docker compose down          # stop containers
docker compose down -v       # stop + delete database (fresh start)
```

---

## OPTION B: Local Setup (no Docker)

### Prerequisites to install:
1. Python 3.12 — https://www.python.org/downloads/
2. PostgreSQL 16 — https://www.postgresql.org/download/
3. Redis — https://redis.io/docs/getting-started/installation/
4. Node.js 20 — https://nodejs.org/

### Step 1 — PostgreSQL setup
```sql
-- Open psql and run:
CREATE DATABASE playto_payout;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE playto_payout TO postgres;
```

### Step 2 — Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Create .env
cat > .env << 'ENVEOF'
SECRET_KEY=3xGh9@kL2mPqRs7vWxYz1bCdEfJnOuTw
DEBUG=True
ALLOWED_HOSTS=*
DB_NAME=playto_payout
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
CORS_ALLOW_ALL_ORIGINS=True
ENVEOF

python manage.py migrate
python manage.py seed_merchants
python manage.py runserver
```

### Step 3 — Celery Worker (new terminal)
```bash
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info
```

### Step 4 — Celery Beat (new terminal)
```bash
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Step 5 — Frontend (new terminal)
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
npm run dev
# Open http://localhost:5173
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest apps/payouts/tests.py -v --tb=short
```

Expected output:
```
PASSED apps/payouts/tests.py::ConcurrencyTest::test_two_concurrent_payouts_exactly_one_succeeds
PASSED apps/payouts/tests.py::IdempotencyTest::test_same_idempotency_key_returns_same_response
PASSED apps/payouts/tests.py::IdempotencyTest::test_different_keys_create_different_payouts
PASSED apps/payouts/tests.py::StateMachineTest::test_invalid_transition_raises
PASSED apps/payouts/tests.py::StateMachineTest::test_ledger_invariant
```

---

## What each .env variable does

| Variable | What it does | Example value |
|---|---|---|
| `SECRET_KEY` | Django signing key — make this random in prod | `3xGh9@kL2m...` |
| `DEBUG` | Shows error details. Set `False` in production | `True` |
| `ALLOWED_HOSTS` | Which domains can access the API | `*` for dev, `yourdomain.com` for prod |
| `DB_NAME` | PostgreSQL database name | `playto_payout` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `postgres` |
| `DB_HOST` | DB server address. Use `db` in Docker, `localhost` locally | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection. Celery uses this as message broker | `redis://localhost:6379/0` |
| `CORS_ALLOW_ALL_ORIGINS` | Allow React frontend to call the API | `True` |
| `VITE_API_URL` | (Frontend) Where the React app sends API calls | `http://localhost:8000/api/v1` |

---

## Deployment to Railway (free)

### Backend + PostgreSQL + Redis + Celery

1. Go to https://railway.app → New Project → Deploy from GitHub
2. Select your repo → select `/backend` as root directory
3. Railway auto-detects Python. Add these environment variables in Railway dashboard:
   ```
   SECRET_KEY=<generate a random 50-char string>
   DEBUG=False
   ALLOWED_HOSTS=<your-railway-domain>.railway.app
   DB_HOST=<railway postgres internal host>
   DB_PORT=5432
   DB_NAME=railway
   DB_USER=postgres
   DB_PASSWORD=<from railway postgres>
   REDIS_URL=<from railway redis>
   CORS_ALLOW_ALL_ORIGINS=True
   ```
4. Add start command: `python manage.py migrate && python manage.py seed_merchants && gunicorn config.wsgi`
5. Add PostgreSQL plugin → Railway gives you `DATABASE_URL`
6. Add Redis plugin → Railway gives you `REDIS_URL`
7. Add a second service from same repo for Celery Worker:
   - Start command: `celery -A config worker --loglevel=info`
8. Add a third service for Celery Beat:
   - Start command: `celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

### Frontend → Vercel
1. Go to https://vercel.com → New Project → Import from GitHub
2. Select your repo → set Root Directory to `frontend`
3. Add env variable: `VITE_API_URL=https://<your-railway-backend>.railway.app/api/v1`
4. Deploy → done

