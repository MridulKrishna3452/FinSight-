# FinSight API Reference

Base URL: `http://localhost:8000/api/v1` (local dev, per `.env` / `NEXT_PUBLIC_API_URL`)

All request/response bodies are JSON unless noted (file uploads use
`multipart/form-data`). Interactive OpenAPI docs are also available at
`http://localhost:8000/docs` while the API is running.

## Conventions

- **Auth**: every endpoint except `/auth/register`, `/auth/login`,
  `/auth/refresh`, and `/auth/logout` requires `Authorization: Bearer <access_token>`.
  A 401 response means the access token is missing/expired — the frontend
  automatically retries once after calling `/auth/refresh`.
- **IDs**: all resource IDs are UUIDv4 strings.
- **Money**: amounts are decimal strings (e.g. `"450.00"`), always positive;
  `transaction_type` (`income`/`expense`) carries the sign.
- **Dates**: ISO-8601 (`YYYY-MM-DD` for dates, RFC 3339 for timestamps).
- **Errors**: `{"detail": "<message>"}` for most errors; validation failures
  return `{"detail": "Validation error", "errors": [...]}` (FastAPI/Pydantic
  error list) with status `422`.
- **Pagination**: paginated list endpoints return
  `{"items": [...], "total": N, "page": N, "page_size": N, "total_pages": N}`.

---

## Auth — `/auth`

### `POST /auth/register`
Creates a user and immediately logs them in.

Request:
```json
{ "email": "user@example.com", "password": "StrongPass123!", "full_name": "Jane Doe" }
```
Response `201`: `TokenPair` (see below) + sets the `finsight_refresh_token` httpOnly cookie.
Errors: `409` if the email is already registered.

### `POST /auth/login`
Request: `{ "email": "...", "password": "..." }`
Response `200`: `TokenPair`, refresh cookie set.
Errors: `401` on bad credentials, `403` if the account is disabled.

**`TokenPair`**:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "full_name": "...", "currency": "INR", "is_active": true }
}
```

### `POST /auth/refresh`
No body — reads the refresh cookie. Rotates the refresh token (old one is
revoked) and returns a new `TokenPair`. `401` if the cookie is missing,
expired, or already revoked.

### `POST /auth/logout`
No body. Revokes the current refresh token and clears the cookie. Always
`200`.

Auth endpoints are rate-limited (`RATE_LIMIT_AUTH`, default `10/minute` per IP).

---

## Users — `/users`

### `GET /users/me`
Returns the authenticated user's profile (`UserRead`).

---

## Transactions — `/transactions`

### `GET /transactions`
Query params (all optional): `search`, `category`, `transaction_type`
(`income`|`expense`), `is_suspicious` (bool), `date_from`, `date_to`,
`sort_by` (`transaction_date`|`amount`|`merchant_name`|`category`|`created_at`),
`sort_dir` (`asc`|`desc`), `page` (default 1), `page_size` (default 25, max 200).

Response `200`: `Page<TransactionRead>`.

### `GET /transactions/export`
Same filters as above (no pagination). Returns `text/csv` as an attachment.

### `POST /transactions`
```json
{
  "transaction_date": "2026-01-15",
  "merchant_name": "Swiggy",
  "description": "SWIGGY ORDER",
  "amount": "450.00",
  "transaction_type": "expense",
  "category": null,
  "payment_method": "UPI",
  "is_recurring": false
}
```
`category` is optional — omit it to let the categorization engine assign one
(recorded as `rule` or `fallback`); an explicit value is recorded as
`user_override`. Expense transactions are scored for anomaly risk
synchronously on create. Response `201`: `TransactionRead`.

### `GET /transactions/{id}` / `PATCH /transactions/{id}` / `DELETE /transactions/{id}`
Standard CRUD, scoped to the authenticated user. `404` if the transaction
doesn't exist **or belongs to another user** (ownership is never leaked via a
`403`). `PATCH` accepts any subset of the create fields.

**`TransactionRead`**:
```json
{
  "id": "...", "transaction_date": "2026-01-15", "merchant_name": "Swiggy",
  "description": "SWIGGY ORDER", "amount": "450.00", "transaction_type": "expense",
  "category": "Dining", "categorization_source": "rule", "payment_method": "UPI",
  "is_recurring": false, "anomaly_score": "0.120", "is_suspicious": false,
  "anomaly_explanation": null, "created_at": "2026-01-15T10:00:00Z"
}
```

---

## Budgets — `/budgets`

### `GET /budgets?month=9&year=2026`
Returns `list[BudgetProgress]` for the given month/year (both optional; omit
to get all budgets). Each item includes computed `spent`, `remaining`,
`percent_consumed`, and `status` (`green` <70%, `yellow` 70-89%, `red` ≥90%).

### `POST /budgets`
```json
{ "name": "Groceries Budget", "category": "Groceries", "monthly_limit": "8000.00", "month": 9, "year": 2026 }
```
`category: null` creates an overall monthly budget (not category-scoped).
`409` if a budget already exists for that user/category/month/year.

### `PATCH /budgets/{id}` / `DELETE /budgets/{id}`
`PATCH` accepts `name` and/or `monthly_limit`. Both scoped to the
authenticated user (`404` otherwise).

Creating/updating a transaction re-evaluates budgets for its category+month
and creates a `budget_threshold` alert the first time spend crosses 80%, 90%,
or 100% (deduplicated per threshold tier).

---

## CSV Import — `/imports`

### `POST /imports/csv/preview` (`multipart/form-data`, field `file`)
Parses the CSV without saving anything, returning up to 10 preview rows plus
detected column mapping. `400` for a non-CSV file, oversized file (>
`CSV_MAX_SIZE_MB`, default 5MB), or missing required columns
(`date`/`description`/`amount` or a recognized alias).

Response: `ImportPreviewResponse`:
```json
{
  "filename": "statement.csv",
  "total_rows": 42,
  "preview_rows": [{ "row_number": 1, "date": "...", "description": "...", "amount": "...", "type": "...", "merchant": "...", "payment_method": "...", "valid": true, "errors": [] }],
  "detected_columns": { "date": "txn_date", "amount": "value", ... }
}
```

### `POST /imports/csv` (`multipart/form-data`, field `file`)
Same validation as preview, but persists an `ImportJob` (`status=queued`) and
enqueues a Celery task to process it asynchronously. Response `202`:
`ImportJobRead` with `status: "queued"`.

### `GET /imports/{job_id}`
Poll this to track progress. `status` moves `queued` → `processing` →
`completed`|`failed`. On completion, `imported_rows`, `duplicate_rows`,
`failed_rows`, `suspicious_rows`, and `result_summary` are populated.
`404` if the job doesn't belong to the caller.

---

## Insights — `/insights`

All endpoints are scoped to the authenticated user and computed from their
own transactions.

| Endpoint | Description |
|---|---|
| `GET /insights/dashboard` | Combined payload for the dashboard: current-month summary, category breakdown, and deterministic insight cards. |
| `GET /insights/spending-by-category?year=&month=` | Category totals/percentages for a given month (omit both for all-time). |
| `GET /insights/monthly-summary?months=6` | Income/expense per month for the last N months. |
| `GET /insights/daily-spending?days=30` | Daily expense totals for the last N days. |
| `GET /insights/top-merchants?limit=10` | Highest-spend merchants by total. |
| `GET /insights/recurring-expenses` | Transactions flagged `is_recurring`, grouped by merchant. |
| `GET /insights/forecast` | 30-day expense forecast (linear regression over daily history) with a disclaimer string. |

`InsightsDashboardResponse`:
```json
{
  "summary": { "balance": "...", "monthly_income": "...", "monthly_expense": "...", "savings_rate": 28.2, "transaction_count": 1138 },
  "spending_by_category": [{ "category": "Shopping", "total": "13586.00", "percent": 25.9, "transaction_count": 29 }],
  "recent_transactions_count": 1138,
  "insight_cards": [{ "id": "category-trend-Shopping", "severity": "warning", "title": "Shopping spending higher", "message": "Shopping spending is 61% higher than last month." }]
}
```
`insight_cards[].severity` is one of `info` | `warning` | `positive`.

`ForecastResponse`:
```json
{
  "method": "linear_regression",
  "disclaimer": "This is an estimate based on your historical imported transaction data...",
  "historical_daily_average": "2019.00",
  "points": [{ "date": "2026-09-21", "predicted_amount": "1850.32" }]
}
```

---

## Alerts — `/alerts`

### `GET /alerts?unread_only=false`
Returns `list[AlertRead]`, newest first. `alert_type` is
`suspicious_transaction` or `budget_threshold`; `severity` is `info` |
`warning` | `critical`.

### `PATCH /alerts/{id}/read`
Marks an alert read. `404` if it doesn't belong to the caller.

---

## Health

### `GET /health` (unversioned, no auth)
`{"status": "ok"}` — used for container/orchestration health checks.
