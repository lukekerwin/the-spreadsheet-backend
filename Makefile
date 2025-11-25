.PHONY: help install dev run test clean migration upgrade downgrade lint format

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server with auto-reload"
	@echo "  make run          - Run production server"
	@echo "  make test         - Run tests"
	@echo "  make migration    - Create a new migration (use MSG='message')"
	@echo "  make upgrade      - Apply database migrations"
	@echo "  make downgrade    - Rollback last migration"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Remove Python cache files"

install:
	pip install -e .

dev:
	lsof -ti:8000 | xargs kill -9 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test:
	pytest tests/ -v

migration:
	alembic revision --autogenerate -m "$(MSG)"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

lint:
	ruff check app/

format:
	ruff format app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
