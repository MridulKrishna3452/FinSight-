# FinSight

**FinSight** is an AI-powered personal finance and fraud-risk platform — a portfolio
project demonstrating a production-shaped full-stack application. It is an
**educational/demo product only**: it uses synthetic or user-uploaded data, is
**not connected to any real bank**, and **does not provide financial advice**.
Fraud-risk alerts are statistical risk indicators from a local machine
learning model, never confirmed fraud determinations.

Users can register, import transaction CSVs, view categorized spending, set
budgets, see a 30-day expense forecast, and get suspicious-transaction alerts
backed by a scikit-learn Isolation Forest model trained on synthetic data.

> Screenshots: see [`docs/screenshots/`](docs/screenshots/) — add your own
> captures there (dashboard, transactions, budgets, insights, alerts) once
> you have the app running locally; none are checked in yet.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui-style components, TanStack Query, React Hook Form + Zod, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2, Pydantic v2, Alembic |
| Database | PostgreSQL 16 |
| Async jobs | Celery + Redis |
| Auth | JWT access tokens (in-memory) + httpOnly refresh-token cookie, bcrypt password hashing |
| ML | pandas, scikit-learn (Isolation Forest), joblib |
| Tests | pytest (backend), Playwright (E2E) |
| Infra | Docker Compose, GitHub Actions CI |

See [`docs/architecture.md`](docs/architecture.md) for how the pieces fit
together, and [`docs/api.md`](docs/api.md) for the full REST API reference.

## Quickstart (Docker Compose)

Requires Docker and Docker Compose.

```bash
cp .env.example .env
make up          # builds and starts postgres, redis, api, worker, web
make migrate      # applies database migrations
make train-model  # trains the anomaly-detection model (writes a .joblib artifact)
make seed         # seeds the demo account with 6+ months of synthetic data
```

- Web: http://localhost:3000
- API: http://localhost:8000 (interactive docs at `/docs`)

Stop everything with `make down`. Tail logs with `make logs`.

### Demo credentials

```
Email:    demo@finsight.app
Password: Demo@12345
```

Log in with these to see a fully populated account: 1,000+ transactions
across 6+ months, 6 category budgets, recurring subscriptions, and several
transactions already flagged as suspicious.

## Running without Docker (local dev)

**Backend**
```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
cp .env.example ../../.env   # or hand-write apps/api/.env — see .env.example at repo root
alembic upgrade head
python -m app.ml.train_anomaly_model
python -m app.seed.seed_demo_data
uvicorn app.main:app --reload
```
You'll also need Postgres and Redis running locally (matching `DATABASE_URL` /
`REDIS_URL`), and a Celery worker for CSV imports to process:
```bash
celery -A app.workers.celery_app worker --loglevel=info   # add --pool=solo on Windows
```

**Frontend**
```bash
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

## Testing

```bash
# Backend: unit + integration tests (pytest), against a running Postgres
cd apps/api
pytest -q

# Backend: lint + types
ruff check .
mypy app

# Frontend: lint, types, production build
cd apps/web
npm run lint
npm run typecheck
npm run build

# End-to-end (Playwright) — needs the full stack running (web, api, postgres,
# redis, a celery worker) with demo data already seeded
cd apps/web
npx playwright install chromium   # first time only
npm run test:e2e
```

The backend test suite covers: auth (register/login/refresh/logout, password
hashing), transaction ownership isolation, categorization rules, budget
progress/threshold math, anomaly-score behavior, and the full CSV import flow
(preview, column-alias detection, async processing, dedup). The Playwright
test covers the primary user journey: log in → import CSV → view dashboard →
create a budget → view a suspicious-transaction alert.

## Repository layout

```
apps/web/    Next.js frontend
apps/api/    FastAPI backend (services, models, ML, Celery workers, tests)
data/        Synthetic CSV generator + a ready-made sample CSV for the import demo
docs/        Architecture notes, API reference, implementation plan, screenshots
```

See [`docs/architecture.md`](docs/architecture.md) for the full breakdown of
`apps/api/app/` and `apps/web/`.

## Feature notes

- **Categorization**: a merchant-keyword rule table (Swiggy → Dining, Uber →
  Transport, etc.) checked first, then a description-keyword fallback, else
  `Other`. Manual overrides are tracked separately and never overwritten by
  re-categorization. See `apps/api/app/services/categorization_service.py`.
- **Anomaly detection**: a global Isolation Forest (`apps/api/app/ml/`)
  trained offline on synthetic data with injected outliers, scoring each new
  expense on 7 features (amount, time, category/merchant frequency, and two
  deviation z-scores) built identically at training and inference time.
  `anomaly_score` is normalized 0–1; `is_suspicious` triggers at ≥ 0.7
  (`ANOMALY_THRESHOLD`). Explanations are rule-based, not model-derived.
- **Forecast**: a simple linear regression over historical daily expense
  totals, always labeled as an estimate.
- **"AI" insights**: fully deterministic, computed from your own transaction
  analytics (month-over-month deltas, budget pace, subscription totals,
  savings-rate trend) — **no LLM API key required**. An `LLMProvider`
  interface exists for optionally plugging one in later.
- **Currency**: formatting defaults to Indian Rupee (₹) via
  `Intl.NumberFormat`, parameterized by currency code so more currencies can
  be added without touching every component.

## Known limitations / intentionally deferred

- No real bank integration (Plaid, etc.) — by design, this is a synthetic/CSV
  demo.
- Only INR formatting is wired up today; the utility functions are
  currency-parameterized for future extension, but no currency picker exists
  in Settings.
- Editing a user's profile (name/email/currency) is not implemented — the
  Settings page shows account info read-only, since there's no `PATCH
  /users/me` endpoint. Documented directly in the UI.
- The anomaly model is a single global model, not retrained per user;
  retraining is a manual, reproducible script (`make train-model`), not an
  automated pipeline.
- Alerts are in-app only — no email/push delivery.
- CSV import supports one file at a time; no bulk/multi-file upload.

## Contributing / extending

- New categorization rules: `apps/api/app/services/categorization_service.py`.
- New insight cards: `apps/api/app/services/insight_service.py::generate_insight_cards`.
- New ML features: `apps/api/app/ml/features.py`, then retrain with `make train-model`.
- New DB fields: add a SQLAlchemy model field, then
  `alembic revision --autogenerate -m "..."` against a running Postgres
  instance, and review the generated migration before applying it.

## License

[MIT](LICENSE)
