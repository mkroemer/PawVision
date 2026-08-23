# PawVision Development Makefile

.PHONY: help install install-dev test test-unit test-integration lint format clean build

# Default target
help:
	@echo "PawVision Development Commands:"
	@echo ""
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  lint          Run linting (flake8, mypy, bandit)"
	@echo "  format        Format code (black, isort)"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build package"
	@echo "  pre-commit    Install pre-commit hooks"
	@echo ""

# Installation
install:
	uv sync --locked --no-dev

install-dev:
	uv sync --locked --group dev

# Testing
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/ -v -m "not integration"

test-integration:
	uv run pytest tests/ -v -m integration

test-cov:
	uv run pytest tests/ -v --cov=pawvision --cov-report=html --cov-report=term-missing

# Code quality
lint:
	uv run flake8 pawvision/ tests/
	uv run mypy pawvision/ --ignore-missing-imports
	uv run bandit -r pawvision/ -c pyproject.toml

format:
	uv run black pawvision/ tests/
	uv run isort pawvision/ tests/

# Security
security:
	uv run bandit -r pawvision/ -c pyproject.toml
	uv run safety check

# Build and packaging
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

# Development setup
pre-commit:
	uv run pre-commit install

# Development server
dev:
	uv run python main.py

# Check everything before commit
check: format lint test
	@echo "All checks passed! ✅"
