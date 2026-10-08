# Swift backend

FastAPI modular-monolith backend for the Swift multilingual ticket prototype. It provides secure session rotation, role-based ticket access, persistent PostgreSQL storage, attachments, advisory classification, review/audit workflows, deterministic multilingual response templates, a safety-routed consumer banking RAG drafting subsystem, and a Redis worker boundary. Bank-core access and real notification delivery remain excluded. See [RAG.md](RAG.md).

## Run

From the repository root:

```bash
docker compose up --build
```

The API is at `http://localhost:8000`, Swagger UI at `/docs`, and frontend at `http://localhost:8080`. The API container applies database migrations before startup. The frontend always uses the REST API configured by `VITE_API_BASE_URL` or the runtime `API_BASE_URL`. Copy `.env.example` to `.env` for non-Compose backend development and replace the secret.

## Development

Run these commands from the `backend` directory. On macOS/Linux:

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

On Windows PowerShell, use the virtual environment's Python explicitly so that
installation and startup use the same dependencies:

```powershell
python -m venv .venv  # First-time setup only
.\.venv\Scripts\python.exe -m pip install -e ".[dev,rag]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

For subsequent launches, run only the final command. If a bare `uvicorn` command
fails with `ModuleNotFoundError: No module named 'logfire'`, it may be using a
global Python installation. Logfire is a required dependency in `pyproject.toml`;
use the virtual environment command above, and rerun its install command if
dependencies are missing.

Attachments use local storage in development and are served only after authorization. The inference layer currently labels its deterministic rule implementations as development fallbacks; it never represents them as XLM-R. Tesseract/OCR and trained transformer weights are not required for startup. Responses are safe templates requiring agent approval before customer visibility.
