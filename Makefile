.PHONY: up down logs migrate seed test lint build

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.seed.seed_demo_data

train-model:
	docker compose exec api python -m app.ml.train_anomaly_model

test:
	docker compose exec api python -m pytest -q
	cd apps/web && npm run typecheck

test-e2e:
	cd apps/web && npx playwright test

lint:
	docker compose exec api ruff check .
	docker compose exec api mypy app
	cd apps/web && npm run lint

build:
	docker compose build
