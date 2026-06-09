# RecordChat — project management via Docker Compose.
# Run `make` or `make help` to list available targets.

COMPOSE     ?= docker compose
BACKEND_URL ?= http://127.0.0.1:8000

.DEFAULT_GOAL := help
.PHONY: help env up down restart rebuild build ps logs backend-logs \
        frontend-logs sh-backend ingest test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if it does not exist
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

up: ## Start all services in the background (builds images on first run)
	$(COMPOSE) up -d
	@echo "backend  -> http://localhost:8000"
	@echo "frontend -> http://localhost:3000"
	@echo "Next: run 'make ingest' once the backend is up."

down: ## Stop and remove the service containers
	$(COMPOSE) down

restart: down up ## Restart all services

rebuild: ## Rebuild images and (re)start in the background
	$(COMPOSE) up -d --build

build: ## Build all images without starting them
	$(COMPOSE) build

ps: ## Show service status
	$(COMPOSE) ps

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

backend-logs: ## Tail backend logs
	$(COMPOSE) logs -f backend

frontend-logs: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

sh-backend: ## Open a shell in the backend container
	$(COMPOSE) exec backend sh

ingest: ## Trigger ingestion / rebuild the Qdrant collection (waits for backend)
	curl -fsS --retry 10 --retry-delay 3 --retry-connrefused -X POST $(BACKEND_URL)/ingest
	@echo "\nIngest complete."

test: ## Run the backend test suite
	cd backend && uv run pytest -q

clean: ## Stop services AND delete volumes (wipes Qdrant data)
	$(COMPOSE) down -v
