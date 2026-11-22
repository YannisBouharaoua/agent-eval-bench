.PHONY: install test lint demo

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

demo:
	evalbench run -c bench.demo.toml --fail-on never
