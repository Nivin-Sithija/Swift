# Swift

Trilingual (Sinhala / English / Tamil), multimodal AI support-ticket triage system for banking and fintech. Incoming tickets — text, voice, or image (bank slips, receipts, error screenshots) — are transcribed/OCR'd, classified by category, priority, and sentiment, and routed: routine questions get a RAG-grounded drafted reply, fraud/urgent/negative-sentiment tickets escalate to a human agent.

## Frontend prototype

This repository now includes a complete Vite + React frontend demonstrating the customer and support-agent workflows with local mock data. It does not connect to a bank, authentication provider, model, OCR system, or backend. All names, identifiers, transactions, predictions, and images are fictional.

### Features

- Customer login, validated multilingual ticket submission, optional image preview, simulated processing, confirmation, history, and customer-safe ticket detail
- Agent dashboard, sortable/filterable queues, high-priority/escalated/resolved views, prediction review and correction, OCR evidence, internal notes, assignment and lifecycle actions
- Editable AI response drafts with prominent safety notice and mandatory confirmation before mock approval
- English, Sinhala, Tamil, Singlish, Tanglish, and mixed-script sample messages
- Dark theme by default plus persistent Light, Dark, and System preferences
- Persistent English, සිංහල, and தமிழ் interface-language preference
- Role-protected routes, responsive navigation, mobile ticket cards, accessible controls, reduced-motion support, loading/error/empty states
- Typed mock service boundary designed for later REST replacement

### Technology

React 19, TypeScript strict mode, Vite, React Router, Tailwind CSS, React Hook Form, Zod, Lucide React, Vitest, React Testing Library, ESLint, and Prettier.

### Setup

Node.js 20.19+ or 22.12+ is recommended.

```bash
npm install
npm run dev
npm run lint
npm run test
npm run build
```

The development server prints its local URL, normally `http://localhost:5173`.

### Demo credentials

| Role | Email | Password |
|---|---|---|
| Customer | `customer@swift.demo` | `password123` |
| Support agent | `agent@swift.demo` | `password123` |

Use the role selector on the login screen. “Use demo account” fills the relevant credentials.

### Routes

- `/login`
- `/customer/submit`
- `/customer/tickets`
- `/customer/tickets/:ticketId`
- `/agent/dashboard`
- `/agent/tickets`
- `/agent/tickets/:ticketId`
- `/agent/high-priority`
- `/agent/escalated`
- `/agent/resolved`
- `/agent/reports` and `/agent/settings` (planned-feature views)
- `/not-found`

### Mock data and UI states

Fifteen realistic fictional tickets live in `src/mocks/tickets.ts`; runtime mutations are held only in memory. Refreshing restores the original mock dataset. Add `?state=error` to `/customer/tickets` to demonstrate a controlled service-error state. Authentication is simulated in browser storage and must not be treated as production security.

### Theme behavior

The first visit explicitly defaults to Dark, regardless of operating-system preference. The inline script in `index.html` applies the stored selection before React renders to prevent a theme flash. System mode listens for operating-system changes. The preference is stored under `swift-theme`.

### Future API integration

Set the eventual REST origin from `.env.example`:

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Replace `mockTicketService` in `src/services/ticketService.ts` with a REST implementation of the same `TicketService` interface. Pages and reusable components consume promises and typed domain objects, so no view-level mock arrays need to be rewritten.

### Frontend structure

```text
src/
  app/providers/       Theme, language and mock authentication
  app/router/          Routes and role guards
  components/agent/    Prediction, evidence, notes and response panels
  components/common/   Shared controls and dialogs
  components/layout/   Customer and agent application shells
  components/tickets/  Tables, filters, cards, badges and timeline
  mocks/               Central fictional ticket dataset
  pages/               Login, customer, agent and utility pages
  services/            Replaceable asynchronous service interface
  test/                Behavioral Vitest/Testing Library tests
  types/               Strict domain models
```

### Testing

`npm run test` covers theme defaults and persistence, validation, access control, agent metrics, ticket filtering, confidence thresholds, image validation, processing states, and unmodified multilingual strings. `npm run lint` checks TypeScript and React rules. `npm run build` performs strict compilation and a production Vite build.

### Known limitations

- All operations are browser-only mock interactions and are reset on refresh.
- OCR, model predictions, draft generation, notifications, search, and uploads are simulated.
- Reports and Settings intentionally show planned-feature pages.
- The compact localisation dictionary demonstrates architecture rather than translating every sentence.
- The synthetic receipt is illustrative and contains no actual financial data.

### Screenshots

Screenshots can be added under `docs/screenshots/` for the login, customer submission, agent dashboard, and agent ticket review views.

## Docker Development and Deployment

The frontend includes separate Docker workflows for live development and a minimal production Nginx server. Docker Engine with Docker Compose v2 and available ports `5173` and `8080` are required.

### Environment setup

Create a local environment file from the public example:

```bash
cp .env.example .env
```

All `VITE_*` and `API_BASE_URL` values are delivered to browser code and are therefore public. Never put passwords, API tokens, private keys, or other secrets in these variables.

| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Development/build-time REST fallback | `http://localhost:8000/api/v1` |
| `API_BASE_URL` | Production container runtime REST URL | `http://backend:8000/api/v1` |
| `VITE_APP_NAME` | Public application name | `Swift` |
| `VITE_DEFAULT_THEME` | Documented public theme default | `dark` |
| `FRONTEND_DEV_PORT` | Host development port | `5173` |
| `FRONTEND_PROD_PORT` | Host production port | `8080` |
| `CHOKIDAR_USEPOLLING` | Reliable bind-mount watching on Docker Desktop | `true` |

The theme provider still explicitly defaults first-time visitors to Dark. Light, Dark, and System preferences continue to persist in `localStorage`.

### Development with hot reload

Validate and start the development stack:

```bash
docker compose config
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). Source files are bind-mounted into `/app`; Vite listens on `0.0.0.0` and polling makes hot reload reliable on Linux, macOS, and Windows Docker Desktop. A named volume protects the container's Linux `node_modules` from the host bind mount.

View logs or stop the environment with:

```bash
docker compose logs -f frontend
docker compose down
```

When `package.json` or `package-lock.json` changes, rebuild dependencies:

```bash
docker compose down -v
docker compose up --build
```

The `-v` option removes the development dependency volume; it does not delete repository files.

### Production Nginx container

Validate, build, and start production:

```bash
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml ps
```

Open [http://localhost:8080](http://localhost:8080). Follow logs and stop the container with:

```bash
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml down
```

Check container health directly:

```bash
curl http://localhost:8080/health
docker compose -f docker-compose.prod.yml ps
```

The multi-stage production build uses Node 22 Alpine only to compile the application. The final pinned Nginx Alpine image contains only `dist`, Nginx configuration, and a small runtime configuration bootstrap. It listens on unprivileged port `8080`, runs as the `nginx` user, drops Linux capabilities, uses `no-new-privileges`, and runs with a read-only root filesystem plus a constrained `/tmp`.

Nginx provides React Router fallback for application routes, immutable caching for hashed `/assets/`, no-cache handling for HTML and runtime configuration, gzip, baseline security headers, and a lightweight `/health` response. Missing files beneath `/assets/` return `404` instead of the SPA shell.

### Runtime API configuration

Vite normally embeds variables during compilation. The production entrypoint instead writes the public `API_BASE_URL` into `/tmp/runtime-config.js`:

```js
window.__APP_CONFIG__ = { API_BASE_URL: "http://backend:8000/api/v1" };
```

The typed helper in `src/lib/config.ts` checks runtime configuration first, then `VITE_API_BASE_URL`, and finally a localhost development default. This allows the same built image to target another future API without rebuilding:

```bash
API_BASE_URL=https://support-api.example.com/api/v1 \
  docker compose -f docker-compose.prod.yml up -d
```

A future backend can join the `swift-production` network and use the hostname `backend`. The commented `/api/` proxy example in `nginx/default.conf.template` can be enabled later, but the frontend currently has no hard dependency on a backend container.

### Convenience scripts

```bash
npm run docker:dev
npm run docker:dev:down
npm run docker:prod
npm run docker:prod:down
npm run docker:logs
```

Equivalent VS Code tasks are available through “Tasks: Run Task”.

### Troubleshooting and cleanup

- If hot reload does not detect changes, keep `CHOKIDAR_USEPOLLING=true` and recreate the development container.
- If dependencies appear stale, run `docker compose down -v` and rebuild.
- If a port is occupied, override `FRONTEND_DEV_PORT` or `FRONTEND_PROD_PORT` in `.env`.
- Inspect resolved settings with `docker compose config` before starting a stack.
- Inspect startup failures with `docker compose logs frontend`.
- Remove stopped containers and dependency volumes with `docker compose down -v`. Add `--rmi local` only when you also intend to remove locally built images.

Full product framing (pages, user flows, features in/out of scope, success criteria) lives in [`context/project-overview.md`](context/project-overview.md). System design and stack are in [`context/architecture.md`](context/architecture.md).

The project has two tracks that are both mid-flight: a **research + dataset track** (this repo's current focus) and a **planned application build** (Next.js + FastAPI, specced but not yet implemented — see `context/build-plan.md`).

---

## Research

`research/` is a working bibliography of primary-source papers backing every non-obvious modeling decision — not background reading, but load-bearing evidence for choices like model architecture, dataset scale, and how to handle romanized/code-mixed Sinhala. [`research/README.md`](research/README.md) is the index: each paper is summarized, cited by section, and linked to the decision it grounds in `context/model-research.md`.

Findings that shaped the build:
- **Fine-tuned beats zero-shot LLM, consistently** — across every paper in the library (banking-domain XLM-R+lexicon 88.4% vs. GPT-4o zero-shot 81.5%; SinLlama fine-tuned F1 72.5 vs. unfine-tuned 22.7) — the basis for the project's "ML models classify, LLM only replies" division of labor.
- **Romanized Sinhala breaks tokenizers, not just models** — median perplexity is 312× worse than native script on the same LLMs (Rajapakse & Weerasinghe, 2026), traced to subword fragmentation. Directly motivated preserving English loanword spelling in the Singlish generator (`card`, not `kad`) and keeping reverse-transliteration in the classifier bake-off rather than dropping it.
- **Neural models need data volume Sinhala datasets rarely have** — classical ML/CRF beat every neural architecture at ~2k–7.5k rows (Smith & Thayasivam, 2020); the pattern flips only past roughly a hundred thousand balanced rows (Arya, 2026). This calibrated the project's own dataset-scale targets and kept the classifier bake-off (never assume the transformer wins) in the plan.
- **Plain oversampling beats SMOTE for code-mixed/low-resource text** in every paper that tried both — adopted as the default class-balancing method.

---

## Data Science

The dataset-engineering work (`datasets/`) turns [BANKING77](https://huggingface.co/datasets/PolyAI/banking77) (13,083 English support queries, 77 intents) into a labeled, trilingual, multi-script benchmark for the classifier bake-off — five language/script folders: `english/`, `sinhala/`, `singlish/` (romanized Sinhala), `tamil/`, `tamilish/` (romanized Tamil).

**Every `train_labeled.csv`/`test_labeled.csv` shares one schema**: `id, text_en, text, category, sentiment, priority`. `id` is the 0-based row index into `original-dataset/train.csv`/`test.csv` (the alignment key across all five folders); `text_en` is always the original English ticket text; `text` is that folder's own-language text. sentiment/priority are identical across all five for the same row — they're translations of the same ticket, labeled once in English and carried over, never re-labeled per language.

**Pipeline:**
1. **Source** — BANKING77 `train.csv` / `test.csv` (`datasets/original-dataset/`), English text + intent only — no category/sentiment/priority ground truth exists upstream.
2. **Labeling** — sentiment and priority are LLM-derived (category comes from BANKING77's own intent field), not scraped. `datasets/translation/prompts/` holds iterative prompt versions (v1 → v5); each version was validated against a hand-annotated gold benchmark subset before being trusted to label the full set (`datasets/english/`, incl. mismatch-analysis CSVs and a Label Studio config for manual review). v5 is the current production prompt, and its labels are the only source of truth — including for Tamil, whose translation arrived with its own (older, non-v5) sentiment/priority pass that was overwritten to stay in sync with the rest.
3. **Translation** — English rows are machine-translated to Sinhala, then **hand-corrected by category** into colloquial, code-mixed Sinhala (not literal MT output) — tracked in a progress CSV, style rules documented in `datasets/translation/SINHALA_STYLE.md`. Tamil is machine-translated (Gemini) without a hand-correction pass yet.
4. **Romanization** — Singlish is a rule-based transliterator (`romanize.py`, `singlishify.py`, `singlish_overrides.py`) generating romanized Sinhala from the corrected native-script text, preserving English loanword spelling per the Script Sensitivity finding above. Edits happen in the romanized (Singlish) CSV, since that's what's human-readable, and get **backported into the Sinhala source** via diff/update scripts (`singlish_diff.py`, `update_sinhala.py`) rather than maintained in two places by hand. Tamilish (romanized Tamil) was generated directly by the same translation pass as Tamil, not a separate rule-based step.
5. **Auditing** — `audit_sentiment.py` / `apply_bulk_sentiment_fix.py` catch and bulk-correct systematic labeling errors after review; `datasets/localization/` runs a similar review pass over category localization.
6. **Analysis** — `notebooks/data_preparation/dataset_characteristics_english.ipynb` (class balance, text length, vocabulary) and `notebooks/data_preparation/prompt_benchmark_findings.ipynb` (prompt-version accuracy comparison against gold labels) document the dataset and prompt-selection evidence.

Working rule for this pipeline: a dataset's own heuristic labels are never trusted as ground truth for tuning a labeling prompt — every prompt version is checked against a freshly hand-annotated gold set first.

**Status**: English/Sinhala/Singlish have both train and test sets fully v5-labeled. Tamil/Tamilish have the train set done but no test set yet (only a small preview sample) — generating their full test set is the next open item.

---

## Software Engineering

The planned application (`context/architecture.md`) is a two-service system:

| Layer | Stack |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript strict, Tailwind + shadcn/ui |
| Backend | FastAPI (Python 3.11+, typed/mypy) |
| Data | PostgreSQL 16 + pgvector (tickets, messages, KB articles, embeddings) |
| Classification | XLM-RoBERTa backbone + per-language LoRA experts (category / priority / sentiment) |
| Language ID | Unicode script detection + per-pair CRF/XGBoost for code-mixed Si-En / Ta-En |
| Multimodal | Whisper/MMS (ASR), Tesseract `sin+tam+eng` (OCR), Coqui/Indic-TTS (speech reply) |
| RAG | BGE-M3/e5 embeddings in pgvector, Gemini (prod) / Ollama (dev) generation |
| Channels | Web widget, Telegram, WhatsApp (Twilio/Meta) |
| Analytics | PostHog |

Engineering decisions worth noting:
- **Pluggable banking data access** — `BankingProvider` is a Protocol with a stable `AccountRecord`/`TransactionRecord` schema; `MockBankingProvider` is the only implementation built (no real bank partner), but a real integration is a single adapter, not a pipeline rewrite.
- **Classification never touches the LLM** — category/priority/sentiment are served by trained discriminative models (target <100ms, ONNX/quantized, kept warm as singletons); the LLM is reply-generation only. Keeps latency and cost predictable and avoids hallucinated labels.
- **Scope is explicitly split** — `context/project-overview.md` marks which features match the formally submitted project proposal (multimodal ingestion, trilingual classification, agent dashboard with label correction) versus the applied extension built on top (RAG replies, TTS, Telegram/WhatsApp, auto-reply workflow), so the two aren't conflated when evaluated against the proposal.
- **Status**: application code (`web/`, `api/`) has not been scaffolded yet — `context/build-plan.md` and `context/progress-tracker.md` track phase planning and what's actually shipped.

---

## Repository Layout

```
context/       Product spec, architecture, model research, coding standards, build/progress tracking
research/      Primary-source papers + bibliography backing modeling decisions
datasets/      BANKING77-derived trilingual dataset pipeline (translation, romanization, labeling, audits)
notebooks/     Dataset characteristics and prompt-benchmark analysis
```
