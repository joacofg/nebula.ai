PYTHON_BOOTSTRAP ?= python3.12
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
UVICORN := .venv/bin/uvicorn

.PHONY: setup install test lint qdrant-up qdrant-down ollama-pull run smoke-openrouter smoke-fallback benchmark benchmark-demo metric-corpus metric-label metric-judge metric-report selfhost-up selfhost-down selfhost-logs migrate migrate-create console-install console-dev console-test console-e2e

setup:
	$(PYTHON_BOOTSTRAP) -m venv .venv
	$(PIP) install -e '.[dev]'
	cp -n .env.example .env || true

install:
	$(PIP) install -e '.[dev]'

test:
	$(PYTEST)

lint:
	$(RUFF) check .

qdrant-up:
	docker compose up -d qdrant

qdrant-down:
	docker compose down

ollama-pull:
	ollama pull llama3.2:3b
	ollama pull nomic-embed-text

run:
	$(UVICORN) nebula.main:app --reload

smoke-openrouter:
	PORT=8000 ./scripts/smoke_openrouter.sh

smoke-fallback:
	PORT=8002 MODE=fallback ./scripts/smoke_openrouter.sh

benchmark:
	$(PYTHON) -m nebula.benchmarking.run

benchmark-demo:
	$(PYTHON) -m nebula.benchmarking.run --dataset benchmarks/v1/demo-scenarios.jsonl

# Metric-validation study (v4.0 Phase 1, T1). PREMIUM_B is the second
# premium model that anchors the noise floor; it has no default because the
# ceiling it measures depends entirely on which model it is.
metric-corpus:
	$(PYTHON) -m scripts.metric_validation.build_pilot_corpus --premium-b-model $(PREMIUM_B)

metric-label:
	$(PYTHON) -m scripts.metric_validation.label --rater $(RATER) $(if $(INFORMATIVE),--only-informative,)

metric-judge:
	$(PYTHON) -m scripts.metric_validation.run_judge --model $(JUDGE_MODEL)

metric-report:
	$(PYTHON) -m scripts.metric_validation.analyse --reference-rater $(RATER)

migrate:
	./.venv/bin/alembic upgrade head

migrate-create:
	./.venv/bin/alembic revision --autogenerate -m "$(MSG)"

selfhost-up:
	docker compose -f docker-compose.selfhosted.yml up -d

selfhost-down:
	docker compose -f docker-compose.selfhosted.yml down

selfhost-logs:
	docker compose -f docker-compose.selfhosted.yml logs -f nebula

console-install:
	npm --prefix console install

console-dev:
	npm --prefix console run dev

console-test:
	npm --prefix console run test -- --run

console-e2e:
	npm --prefix console run e2e
