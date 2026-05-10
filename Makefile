.PHONY: dev setup test migrate lint clean

# ── Setup ────────────────────────────────────────────────────────────

setup:  ## Initialize project for development
	cp -n backend/.env.example backend/.env || true
	@echo "✓ .env created (edit it with your API keys)"
	cd backend && pip install -e ".[dev]"
	@echo "✓ Dependencies installed"
	@echo "→ Run 'make migrate' to initialize the database"

# ── Development ──────────────────────────────────────────────────────

dev:  ## Start all services in dev mode
	docker compose up --build -d
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "MinIO Console: http://localhost:9001"

dev-logs:  ## Tail logs from all services
	docker compose logs -f

dev-down:  ## Stop all services
	docker compose down

dev-shell:  ## Open a shell in the API container
	docker compose exec api bash

# ── Database ─────────────────────────────────────────────────────────

migrate-init:  ## Create initial Alembic migration
	@cd backend && alembic revision --autogenerate -m "initial"

migrate:  ## Apply pending migrations
	@cd backend && alembic upgrade head

migrate-rollback:  ## Rollback last migration
	@cd backend && alembic downgrade -1

# ── Testing ──────────────────────────────────────────────────────────

test:  ## Run all tests with coverage
	@cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing 2>/dev/null || \
		python -m pytest tests/ -v

test-quick:  ## Run tests without coverage
	@cd backend && python -m pytest tests/ -v -x

# ── Quality ──────────────────────────────────────────────────────────

lint:  ## Run ruff linter
	@cd backend && ruff check app/

format:  ## Format code with ruff
	@cd backend && ruff format app/

typecheck:  ## Run mypy type checker
	@cd backend && mypy app/

# ── Build ────────────────────────────────────────────────────────────

build:  ## Build production images
	docker compose -f docker-compose.yml build

# ── Cleanup ──────────────────────────────────────────────────────────

clean:  ## Remove all docker volumes (data loss!)
	docker compose down -v
	rm -rf backend/.venv
	rm -rf .pytest_cache
	rm -rf **/__pycache__

# ── Help ─────────────────────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'