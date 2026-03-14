PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
UVICORN := .venv/bin/uvicorn

.PHONY: setup install test lint qdrant-up qdrant-down ollama-pull run

setup:
	/opt/homebrew/bin/python3.12 -m venv .venv
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
