.PHONY: install test lint format demo clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/

demo:
	python examples/sample_pipeline.py

clean:
	rm -rf .pytest_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -exec rm -rf {} +
