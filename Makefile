.PHONY: help setup install dev test lint format clean docker-up docker-down docker-logs docker-build docker-hadolint docker-trivy docker-health db-upgrade db-migrate create-admin

help:
	@echo "Wishlist API - Makefile commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup        - Initial project setup (venv + deps + .env)"
	@echo "  make install      - Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services in Docker"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-logs  - Show logs"
	@echo "  make docker-test  - Run tests in Docker"
	@echo ""
	@echo "Database:"
	@echo "  make db-upgrade   - Apply migrations"
	@echo "  make db-migrate   - Create new migration"
	@echo "  make create-admin - Create admin user"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Clean temporary files"

setup:
	@echo "🚀 Setting up project..."
	python -m venv .venv
	@echo "✅ Virtual environment created"
	@echo "Run: source .venv/bin/activate"
	@echo "Then: make install"

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install
	@echo "✅ Dependencies installed"

env:
	@echo "⚙️  Creating .env file..."
	chmod +x setup_env.sh
	./setup_env.sh

dev:
	@echo "🔨 Starting development server..."
	uvicorn app.main:app --reload

test:
	@echo "🧪 Running tests..."
	pytest

lint:
	@echo "🔍 Running linters..."
	ruff check .
	black --check .
	isort --check-only .
	bandit -q -r app

format:
	@echo "✨ Formatting code..."
	ruff check --fix .
	black .
	isort .

docker-up:
	@echo "🐳 Starting Docker services..."
	docker compose up --build

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker compose logs -f

docker-build:
	@echo "🏗️  Building production image..."
	docker build --target runtime -t wishlist-api:local .

docker-hadolint:
	@echo "🔍 Running Hadolint..."
	docker run --rm -i hadolint/hadolint:2.12.0 < Dockerfile

docker-trivy: docker-build
	@echo "🛡️  Running Trivy scan..."
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $$(pwd)/.trivy-cache:/root/.cache/ \
		aquasec/trivy:0.53.0 image --exit-code 1 --severity HIGH,CRITICAL wishlist-api:local

docker-health:
	@echo "🩺 Checking container health..."
	docker compose ps

docker-test:
	@echo "🧪 Running tests in Docker..."
	docker compose -f docker-compose.test.yaml up --build

db-upgrade:
	@echo "🗄️  Applying database migrations..."
	alembic upgrade head

db-migrate:
	@echo "🗄️  Creating new migration..."
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

create-admin:
	@echo "👤 Creating admin user..."
	python create_admin.py

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/
	@echo "✅ Cleaned"
