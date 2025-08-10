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
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m integration

test-cov:
	pytest tests/ -v --cov=pawvision --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 pawvision/ tests/
	mypy pawvision/ --ignore-missing-imports
	bandit -r pawvision/ -c pyproject.toml

format:
	black pawvision/ tests/
	isort pawvision/ tests/

# Security
security:
	bandit -r pawvision/ -c pyproject.toml
	safety check

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
	python -m build

# Development setup
pre-commit:
	pre-commit install

# Development server
dev:
	python main.py

# Check everything before commit
check: format lint test
	@echo "All checks passed! ✅"
