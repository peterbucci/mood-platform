.PHONY: verify verify-env check db-up db-down db-reset migrate migrate-sql revision

PYTHON ?= python
ALEMBIC_CONFIG ?= apps/backend/alembic.ini
ALEMBIC_CMD = $(PYTHON) -m alembic -c $(ALEMBIC_CONFIG)

verify:
	@python scripts/verify.py

verify-env:
	@python scripts/verify.py --skip-style --skip-api --skip-db

check:
	@pre-commit run --all-files

db-up:
	@echo "Starting PostgreSQL container..."
	@docker compose up -d postgres

db-down:
	@echo "Stopping docker compose services..."
	@docker compose down

db-reset:
	@echo "Resetting database volumes and starting PostgreSQL..."
	@docker compose down -v
	@docker compose up -d postgres

migrate:
	@echo "Applying Alembic migrations to head..."
	@$(ALEMBIC_CMD) upgrade head

migrate-sql:
	@echo "Rendering Alembic migration SQL for upgrade head..."
	@$(ALEMBIC_CMD) upgrade head --sql

revision:
	@$(PYTHON) -c "msg='$(MSG)'.strip(); import sys; sys.exit(0 if msg else 'ERROR: MSG is required. Usage: make revision MSG=\"add migration\"')"
	@echo "Creating Alembic revision: $(MSG)"
	@$(ALEMBIC_CMD) revision --autogenerate -m "$(MSG)"
