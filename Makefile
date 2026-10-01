.PHONY: setup data features train report api web test lint ci clean

setup:
	pip install -e ".[dev,geo]" && pre-commit install && cd web && npm ci

data:
	python -m jpi.data.ingest && python -m jpi.data.clean && python -m jpi.data.validate

features:
	python -m jpi.geo.osm_build && python -m jpi.features.build

train:
	python -m jpi.models.train

report:
	python -m jpi.report

api:
	uvicorn api.main:app --reload --port 8000

web:
	cd web && npm run dev

test:
	pytest -q --cov=src --cov=api

lint:
	ruff check . && ruff format --check .

ci:
	$(MAKE) lint
	$(MAKE) test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
