# FinSight Implementation Plan

FinSight is an educational/demo AI-powered personal finance and fraud-risk platform. No real bank
connections, no real financial advice, synthetic/user-uploaded data only.

## Phases

1. **Scaffold** — repo structure, git init, docs skeleton (this phase).
2. **Backend foundation** — FastAPI app skeleton, config, security (JWT + bcrypt), DB session,
   SQLAlchemy 2 models (users, transactions, budgets, alerts, import_jobs, refresh_tokens),
   Alembic migration setup, Pydantic schemas.
3. **Backend services & API v1** — auth (register/login/refresh/logout), users, transactions
   (CRUD, filters, pagination, CSV export), budgets (CRUD + progress calc), categorization
   service (rule engine + keyword fallback + override tracking), imports (async via Celery),
   alerts, insights (dashboard summary, category breakdown, monthly summary, forecast,
   recurring expenses).
4. **ML** — synthetic transaction generator, Isolation Forest anomaly training script
   (`train_anomaly_model.py`), model registry (joblib load/cache), anomaly scoring service used
   at transaction create/import time, rule-based human-readable explanations.
5. **Background jobs** — Celery app + worker tasks for CSV import parsing, dedup, categorization,
   anomaly scoring, and budget-threshold alert generation.
6. **Seed/demo data** — demo user, 6+ months of synthetic Indian transactions (1000+), budgets,
   recurring subscriptions, suspicious transactions.
7. **Backend tests** — pytest unit tests (auth, ownership isolation, categorization rules, budget
   math, anomaly scoring) + integration tests (register/login, protected routes, CSV import,
   transaction filters).
8. **Frontend foundation** — Next.js 15 App Router + TS + Tailwind + shadcn/ui primitives,
   TanStack Query client, Zod schemas, RHF forms, auth/session handling, API client with
   refresh-token retry, currency/date formatting utils (INR default).
9. **Frontend pages** — auth (login/register), dashboard, transactions (table, filters, CRUD,
   export), budgets (CRUD + progress visualization), insights (charts + forecast + recurring),
   alerts, CSV import (drag-drop, preview, async job polling), settings.
10. **Infra & DX** — docker-compose (web, api, postgres, redis, celery worker), Dockerfiles,
    `.env.example`, Makefile, GitHub Actions CI (frontend lint/build, backend lint/mypy/tests).
11. **E2E** — Playwright flow: register → load demo data → dashboard → create budget → view
    suspicious alert.
12. **Docs & polish** — `docs/architecture.md`, `docs/api.md`, README with setup/run/demo
    credentials/test instructions, final verification pass (build, lint, tests).

## Key technical decisions

- **Auth**: JWT access token (15 min) returned in JSON body for the SPA to hold in memory;
  refresh token (7 days) issued as an httpOnly, `SameSite=Lax`, `Secure`-in-prod cookie, and also
  tracked server-side in a `refresh_tokens` table (hashed) so logout/rotation can revoke it.
  Documented tradeoff in `docs/architecture.md`.
- **IDs**: UUID primary keys for all public-facing entities.
- **Categorization**: ordered rule table (merchant keyword → category) checked first, then a
  fallback keyword scan over the description, else `Other`. `categorization_source` enum
  (`rule`, `user_override`, `fallback`) stored per transaction; user overrides are never
  overwritten by re-categorization.
- **Anomaly detection**: per-user Isolation Forest is impractical with sparse demo data, so a
  single global Isolation Forest is trained on engineered features (amount, hour, day-of-week,
  category frequency, merchant frequency, z-score deviation from the user's category mean, z-score
  deviation from the user's overall mean amount) from synthetic data with injected outliers.
  `anomaly_score` normalized 0–1 via min-max over the forest's raw score; `is_suspicious` threshold
  documented at 0.7. Explanations are generated from the same feature deviations, not the model
  internals, since Isolation Forest doesn't give per-feature attribution.
- **Forecasting**: 30-day expense forecast via simple linear regression on daily aggregated
  historical expense totals (documented as an estimate, not a guarantee).
- **AI insights**: deterministic, rule-based insight generator over the analytics service output
  (month-over-month deltas, budget pace, subscription totals, savings rate trend). An
  `LLMProvider` interface exists in `app/services/insight_service.py` with a no-op default
  implementation so a real LLM can be swapped in later without an API key being required.

## Out of scope / explicitly deferred

- Real bank aggregation (Plaid/etc.) — synthetic/CSV only, by design.
- Multi-currency support — INR only now; formatting utilities are currency-parameterized for
  future extension.
- Per-user model retraining — a single global model is trained offline via a reproducible script.
- Email delivery for alerts — alerts are in-app only.
