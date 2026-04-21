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