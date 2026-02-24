.PHONY: install test lint run clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

run:
	streamlit run src/app.py

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache *.egg-info dist build
	find . -type d -name "__pycache__" -exec rm -rf {} +
