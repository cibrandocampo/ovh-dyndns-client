# Development Makefile for OVH DynDNS Client

.PHONY: help build up down shell test test-cov lint lint-fix format clean logs run

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build the development Docker image"
	@echo "  up        - Start the development container"
	@echo "  down      - Stop the development container"
	@echo "  shell     - Open a shell in the development container"
	@echo "  test      - Run tests in the development container"
	@echo "  test-cov  - Run tests with coverage report"
	@echo "  lint      - Run linting checks (ruff)"
	@echo "  lint-fix  - Run linting and auto-fix issues (ruff)"
	@echo "  format    - Format code (ruff)"
	@echo "  clean     - Clean up containers and images"
	@echo "  logs      - Show container logs"
	@echo "  run       - Run the application in dev mode"

# Build the development image
build:
	docker compose -f docker-compose.yaml build

# Start the development container
up:
	docker compose -f docker-compose.yaml up -d

# Stop the development container
down:
	docker compose -f docker-compose.yaml down

# Open a shell in the development container
shell:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev bash

# Run tests
test:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v

# Run tests with coverage
test-cov:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing

# Run linting
lint:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev ruff check .

# Run linting and auto-fix
lint-fix:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev ruff check --fix .

# Format code
format:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev ruff format .

# Clean up
clean:
	docker compose -f docker-compose.yaml down -v
	docker rmi ovh_dyndns:dev 2>/dev/null || true

# Show logs
logs:
	docker compose -f docker-compose.yaml logs -f ovh_dyndns_dev

# Run the application in development mode
run:
	docker compose -f docker-compose.yaml exec ovh_dyndns_dev python main.py
