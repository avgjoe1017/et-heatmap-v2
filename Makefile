# Makefile for ET Heatmap
# Quick commands for local development and deployment

.PHONY: help build up down logs clean test deploy

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "ET Heatmap - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Development Commands
# ============================================================================

build: ## Build Docker images for development
	docker-compose build

up: ## Start all services in development mode
	docker-compose up -d
	@echo "✓ Services started"
	@echo "Backend API: http://localhost:8000"
	@echo "Frontend: http://localhost:80"
	@echo "Postgres: localhost:5432"

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U et_heatmap -d et_heatmap

# ============================================================================
# Database Commands
# ============================================================================

db-migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

db-rollback: ## Rollback last migration
	docker-compose exec backend alembic downgrade -1

db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	docker-compose exec backend python scripts/setup.py

db-backup: ## Create database backup
	docker-compose exec backend python scripts/backup_database.py --action backup

db-restore: ## Restore database from backup (set BACKUP_FILE env var)
	docker-compose exec backend python scripts/backup_database.py --action restore --backup-file $(BACKUP_FILE)

# ============================================================================
# Pipeline Commands
# ============================================================================

pipeline-run: ## Run the daily pipeline
	docker-compose exec backend python scripts/run_pipeline.py

pipeline-test: ## Test pipeline with small dataset
	docker-compose exec backend python scripts/test_pipeline.py

# ============================================================================
# Testing Commands
# ============================================================================

test: ## Run all tests
	docker-compose exec backend pytest tests/ -v

test-coverage: ## Run tests with coverage report
	docker-compose exec backend pytest tests/ --cov=src --cov-report=html

lint: ## Run code linting
	docker-compose exec backend black --check src/
	docker-compose exec backend ruff check src/

format: ## Format code with Black
	docker-compose exec backend black src/

# ============================================================================
# Production Commands
# ============================================================================

prod-build: ## Build production Docker images
	docker-compose -f docker-compose.prod.yml build --no-cache

prod-up: ## Start production services
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✓ Production services started"

prod-down: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## View production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-deploy: ## Deploy to production (runs deployment script)
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh

# ============================================================================
# Cleanup Commands
# ============================================================================

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Remove everything including images
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

# ============================================================================
# Setup Commands
# ============================================================================

setup: ## Initial setup - create .env, install dependencies
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "✓ Please edit .env with your credentials"; \
	fi
	docker-compose build
	docker-compose up -d postgres
	sleep 10
	docker-compose exec backend python scripts/setup.py
	@echo "✓ Setup complete!"

install-dev: ## Install development dependencies locally (not in Docker)
	pip install -e .
	pip install pytest pytest-asyncio pytest-mock black ruff mypy

# ============================================================================
# Monitoring Commands
# ============================================================================

status: ## Show status of all services
	docker-compose ps

health: ## Check health of all services
	@echo "Checking backend health..."
	@curl -f http://localhost:8000/health && echo "✓ Backend healthy" || echo "✗ Backend unhealthy"
	@echo "Checking frontend health..."
	@curl -f http://localhost/health && echo "✓ Frontend healthy" || echo "✗ Frontend unhealthy"

quota: ## Check YouTube API quota status
	docker-compose exec backend python -c "from src.common.youtube_quota import get_quota_tracker; print(get_quota_tracker().get_status())"
