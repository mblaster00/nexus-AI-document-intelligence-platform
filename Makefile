SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

.PHONY: up
up: ## Start all application services
	docker compose up --build -d
	@echo "Ingestion API: http://localhost:8000/docs"

.PHONY: down
down: ## Stop all application services
	docker compose down

.PHONY: logs
logs: ## Tail logs for a service — usage: make logs svc=ingestion-api
	docker compose logs -f $(svc)

.PHONY: health
health: ## Check health of all services
	@curl -sf http://localhost:8000/health | python3 -m json.tool

.PHONY: db-shell
db-shell: ## Open a PostgreSQL shell
	docker compose exec postgres psql -U nexus -d nexus

.PHONY: clean
clean: ## Remove all containers and volumes
	docker compose down -v

.PHONY: seed
seed: ## Upload sample PDFs from data/samples/
	python3 scripts/seed_documents.py

.PHONY: fix
fix: ## Auto-fix ruff issues
	ruff check app/ --fix

.PHONY: observability-up
observability-up: ## Start the observability stack
	docker network create nexus-network 2>/dev/null || true
	docker compose -f docker-compose.observability.yml up -d
	@echo "Grafana:    http://localhost:3000  (admin / admin)"
	@echo "Prometheus: http://localhost:9090"

.PHONY: observability-down
observability-down: ## Stop the observability stack
	docker compose -f docker-compose.observability.yml down