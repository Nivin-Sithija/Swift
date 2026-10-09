# Swift backend

FastAPI modular-monolith backend for the Swift multilingual ticket prototype. It provides secure session rotation, role-based ticket access, persistent PostgreSQL storage, attachments, advisory classification, review/audit workflows, deterministic multilingual response templates, a safety-routed consumer banking RAG drafting subsystem, and a Redis worker boundary. Bank-core access and real notification delivery remain excluded. See [RAG guide](../docs/guides/rag.md).

## Run

From the repository root, copy `backend/.env.example` to `backend/.env` and replace
`SWIFT_SECRET_KEY` with a random secret. Keep credentials in environment variables.
The current Dockerfile also requires `datasets/english/train_labeled.csv`; restore it
from the private corpus with authorized access before building. See the
[local setup guide](../docs/guides/local-development.md).

From the repository root:

```bash
docker compose up --build
```

The API is at `http://localhost:8000`, Swagger UI at `/docs`, and frontend at `http://localhost:8080`. The API container applies database migrations before startup. The frontend always uses the REST API configured by `VITE_API_BASE_URL` or the runtime `API_BASE_URL`. The [testing guide](../docs/guides/testing.md) covers local checks and reports.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,rag]'
alembic upgrade head
uvicorn app.main:app --reload
pytest
ruff check .
mypy app
```

Attachments use local storage in development and are served only after authorization. The inference layer currently labels its deterministic rule implementations as development fallbacks; it never represents them as XLM-R. Tesseract/OCR and trained transformer weights are not required for startup. Responses are safe templates requiring agent approval before customer visibility.
