# Local development

Run commands from the repository root unless a block changes directory. The application uses React/Vite, FastAPI, PostgreSQL with pgvector, and Redis.

## Assets and credentials

1. Copy `backend/.env.example` to `backend/.env`. Set `SWIFT_SECRET_KEY` to a random secret, and configure `SWIFT_AGENT_REGISTRATION_CODE` if you need staff registration. Generate a secret with `python -c 'import secrets; print(secrets.token_urlsafe(48))'`.
2. Restore `datasets/english/train_labeled.csv` from the private Swift corpus with authorized access. The current backend Dockerfile copies this file into the image, so a fresh public checkout cannot build without it. Full experiments need all five tracks.
3. Follow the [model artifact guide](../../ml/models/README.md) for checkpoint provisioning. Remote LaBSE inference is configured through the Hugging Face settings in `backend/.env`; OCR uses local SVM artifacts under `ml/models/`. Missing providers or models can trigger low-confidence/development fallbacks.
4. Configure optional OCR and RAG providers in `backend/.env`. See [RAG setup](rag.md) for source ingestion and provider settings. Keep real credentials out of documentation and source files.

The corpus's canonical location is recorded in [CITATION.cff](../../CITATION.cff). Access to private data is separate from access to this repository.

## Docker Compose

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and provision the corpus before building.
docker compose up --build
```

| Service | Address |
| --- | --- |
| Frontend | http://localhost:8080 |
| REST API | http://localhost:8000/api/v1 |
| API explorer | http://localhost:8000/docs |

Compose starts PostgreSQL, Redis, the API, a worker, and the frontend. The API applies migrations on startup. The committed `compose.override.yaml` adds a host PostgreSQL mapping on port 5433 for local tooling; inspect effective mappings with `docker compose config`. Containers reach PostgreSQL on port 5432.

## Separate services

Use Python 3.12 and Node.js 22 to match the current service images. For host-side backend development, set `SWIFT_DATABASE_URL`, `SWIFT_REDIS_URL`, and `SWIFT_STORAGE_ROOT` in `backend/.env` to reachable host addresses and a writable local directory. Compose defaults use container hostnames and `/data/attachments`.

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,rag]'
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite serves on http://localhost:5173. Its API configuration is documented in `frontend/.env.example`; the default points to the backend on port 8000.

See [testing](testing.md) for offline checks.
