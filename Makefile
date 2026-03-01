.PHONY: help install format lint test clean

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install    Install dependencies including test/dev ones"
	@echo "  format     Format code using black"
	@echo "  lint       Lint code using ruff"
	@echo "  test       Run tests using pytest"
	@echo "  clean      Remove build and cache artifacts"

install:
	pip install -e ".[test]"
	pre-commit install

format:
	black .

lint:
	ruff check .

test:
	pytest tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
