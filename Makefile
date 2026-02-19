.PHONY: help install install-dev test test-unit test-integration test-cov lint format clean build docs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:  ## Run all tests
	python -m pytest

test-unit:  ## Run unit tests only
	python -m pytest tests/unit/

test-integration:  ## Run integration tests only
	python -m pytest tests/integration/

test-cov:  ## Run tests with coverage report
	python -m pytest --cov=Core --cov-report=html --cov-report=term-missing

lint:  ## Run linters
	flake8 Core/ tests/
	pylint Core/
	mypy Core/

format:  ## Format code with black and isort
	black Core/ tests/
	isort Core/ tests/

clean:  ## Clean build artifacts and cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

build:  ## Build distribution packages
	python setup.py sdist bdist_wheel

docs:  ## Generate documentation (placeholder for future Sphinx setup)
	@echo "Documentation generation not yet implemented"
	@echo "Documentation files are in docs/ and *.md files"

verify:  ## Run all quality checks (tests, lint, format check)
	@echo "Running tests..."
	python -m pytest
	@echo "Running linters..."
	flake8 Core/ tests/ || true
	pylint Core/ || true
	@echo "Checking formatting..."
	black --check Core/ tests/ || true
	isort --check-only Core/ tests/ || true
	@echo "Type checking..."
	mypy Core/ || true
