# Development Makefile for OVH DynDNS Client

.PHONY: help build up down shell test lint format clean logs

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build the development Docker image"
	@echo "  up        - Start the development container"
	@echo "  down      - Stop the development container"
	@echo "  shell     - Open a shell in the development container"
	@echo "  test      - Run tests in the development container"
	@echo "  lint      - Run linting checks"
	@echo "  format    - Format code with black"
	@echo "  clean     - Clean up containers and images"
	@echo "  logs      - Show container logs"

# Build the development image
build:
	docker-compose build

# Start the development container
up:
	docker-compose up -d

# Stop the development container
down:
	docker-compose down

# Open a shell in the development container
shell:
	docker-compose exec ovh-dyndns-dev /bin/sh

# Run tests
test:
	docker-compose exec ovh-dyndns-dev python -m pytest /app/test/ -v

# Run tests with coverage
test-cov:
	docker-compose exec ovh-dyndns-dev python -m pytest /app/test/ --cov=/app/src --cov-report=html

# Run linting
lint:
	docker-compose exec ovh-dyndns-dev flake8 /app/src
	docker-compose exec ovh-dyndns-dev mypy /app/src

# Format code
format:
	docker-compose exec ovh-dyndns-dev black /app/src

# Clean up
clean:
	docker-compose down -v
	docker rmi ovh_dyndns:dev 2>/dev/null || true

# Show logs
logs:
	docker-compose logs -f ovh-dyndns-dev

# Run the application in development mode
run:
	docker-compose exec ovh-dyndns-dev python /app/main.py
