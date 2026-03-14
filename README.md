# Nebula

Semantic AI Gateway para optimizar costo, latencia y resiliencia en flujos con LLMs.

## Stack base

- Python 3.12+
- FastAPI
- Pydantic v2
- Qdrant
- Ollama
- Prometheus

## Estructura

```text
.
├── docker-compose.yml
├── pyproject.toml
├── src/
│   └── nebula/
│       ├── api/
│       │   └── routes/
│       ├── core/
│       ├── models/
│       ├── observability/
│       ├── providers/
│       └── services/
└── tests/
```

## Desarrollo local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
docker compose up -d qdrant
uvicorn nebula.main:app --reload
```

Instalá Ollama y descargá los modelos recomendados:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Endpoints

`POST /v1/chat/completions`

Compatible con el contrato base de OpenAI para requests y responses streaming y no streaming.

`GET /health`

`GET /metrics`

## Configuración recomendada del MVP

- `llama3.2:3b` como modelo local principal
- `nomic-embed-text` para embeddings
- `mock` como provider premium por defecto para no gastar dinero
- `openai_compatible` como opción cuando quieras conectar OpenAI u OpenRouter
