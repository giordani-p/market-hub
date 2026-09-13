.PHONY: install lint format test run db-up db-down migrate revision seed close-inactive jobs-up enqueue-reconcile worker

install:
	uv sync --extra dev

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest

run:
	uv run uvicorn app.main:app --reload

db-up:
	docker compose up -d --wait postgres
	docker compose exec -T postgres sh -c 'createdb -U "$$POSTGRES_USER" "$$POSTGRES_DB"_test || true'

seed:
	uv run python -m app.catalog.seed

db-down:
	docker compose down

migrate:
	uv run alembic upgrade head

# Uso: make revision m="create catalog tables"
revision:
	uv run alembic revision --autogenerate -m "$(m)"

close-inactive:
	uv run python -m app.communication.close_inactive

jobs-up:
	docker compose up -d --wait postgres localstack worker

enqueue-reconcile:
	uv run python -m app.jobs.enqueue

worker:
	uv run python -m app.jobs.worker
