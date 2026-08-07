# Swift backend

FastAPI modular-monolith backend for the Swift multilingual ticket prototype. It provides secure session rotation, role-based ticket access, persistent PostgreSQL storage, attachments, advisory classification, review/audit workflows, deterministic multilingual response templates, and a Redis worker boundary. RAG, vector search, LLMs, bank-core access, and real notification delivery are intentionally excluded.

## Run

From the repository root:

```bash
docker compose up --build
```

The API is at `http://localhost:8000`, Swagger UI at `/docs`, and frontend at `http://localhost:8080`. The API container runs `alembic upgrade head` and the idempotent seed before startup.

Demo passwords are `password123`: `customer@swift.demo`, `agent@swift.demo`, and `admin@swift.demo`. These are development accounts only.

Set `VITE_USE_MOCK_API=false` when building the frontend to use the REST service. Mock mode remains the default. Copy `.env.example` to `.env` for non-Compose backend development and replace the secret.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
python -m app.seed.seed
uvicorn app.main:app --reload
pytest
ruff check .
mypy app
```

Attachments use local storage in development and are served only after authorization. The inference layer currently labels its deterministic rule implementations as development fallbacks; it never represents them as XLM-R. Tesseract/OCR and trained transformer weights are not required for startup. Responses are safe templates requiring agent approval before customer visibility.
