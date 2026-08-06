<h1 align="center">
  <img src="frontend/public/logo.png" alt="" width="44" height="44" align="center" />
  &nbsp;Swift
</h1>

Trilingual (Sinhala / English / Tamil), multimodal AI support-ticket triage for banking and fintech. Incoming tickets — text, voice, or image (bank slips, receipts, error screenshots) — are transcribed/OCR'd, classified by intent, priority, and sentiment, and routed: routine questions get a RAG-grounded drafted reply, while fraud, urgent, and negative-sentiment tickets escalate to a human agent.

| Track | Status |
|---|---|
| Research library |  indexed in [`research/README.md`](research/README.md) |
| Trilingual dataset |  5 language/script folders, 9,998 train / 3,079 test, id-aligned |
| Classifier bake-off |  harness built; intent, sentiment and priority baselines measured on dev; encoder runs pending |
| Application | Frontend prototype plus FastAPI/PostgreSQL backend scaffold and REST integration |

---

## Frontend prototype

`frontend/` is a Vite + React + TypeScript prototype of the customer and agent workflows, running entirely on local mock data. It connects to no bank, model, or backend — all names, identifiers, transactions, and predictions are fictional.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Docker alternatives (copy `.env.example` to `.env` first): `npm run docker:dev` for hot reload, or `npm run docker:prod` for the production nginx container on port 8080.

| Role | Email | Password |
|---|---|---|
| Customer | `customer@swift.demo` | `password123` |
| Support agent | `agent@swift.demo` | `password123` |

It covers ticket submission in all six language forms with optional image evidence, the agent queue and dashboard, prediction review and correction, and mandatory human approval of AI-drafted replies. `npm run test`, `npm run lint`, and `npm run build` gate changes. Runtime state is in-memory and resets on refresh; `mockTicketService` implements a typed `TicketService` interface designed for later REST replacement.

---

## Research

`research/` is a working bibliography of primary sources backing every non-obvious modeling decision — not background reading, but load-bearing evidence for choices like model architecture, dataset scale, and how to handle romanized code-mixed Sinhala. [`research/README.md`](research/README.md) indexes each paper against the decision it grounds in `context/model-research.md`.

Findings that shaped the build:

- **Fine-tuned beats zero-shot LLM, consistently** — across every paper in the library (banking-domain XLM-R+lexicon 88.4% vs. GPT-4o zero-shot 81.5%; SinLlama fine-tuned F1 72.5 vs. unfine-tuned 22.7). This is the basis for the project's "ML models classify, LLM only replies" division of labor.
- **Romanized Sinhala breaks tokenizers, not just models** — median perplexity is 312× worse than native script on the same LLMs (Rajapakse & Weerasinghe, 2026), traced to subword fragmentation. Directly motivated preserving English loanword spelling in the Singlish generator (`card`, not `kad`).
- **Neural models need data volume Sinhala datasets rarely have** — classical ML/CRF beat every neural architecture at ~2k–7.5k rows (Smith & Thayasivam, 2020); the pattern flips only past roughly a hundred thousand balanced rows (Arya, 2026). This calibrated dataset-scale targets and kept the bake-off honest: never assume the transformer wins.
- **Plain oversampling beats SMOTE** for code-mixed and low-resource text in every paper that tried both — adopted as the default class-balancing method.

---

## Data Science

`datasets/` turns [BANKING77](https://huggingface.co/datasets/PolyAI/banking77) (13,083 English support queries, 77 intents) into a labeled, trilingual, multi-script benchmark across five folders: `english/`, `sinhala/`, `singlish/` (romanized Sinhala), `tamil/`, and `tamilish/` (romanized Tamil).

**Every `train_labeled.csv` / `test_labeled.csv` shares one schema**: `id, text_en, text, category, sentiment, priority`. `category` holds BANKING77's 77-way intent label — "intent" is the task name, `category` is the column name. `id` is the 0-based row index into `original-dataset/` — the alignment key across all five folders. `text_en` is always the original English; `text` is that folder's own-language text. Sentiment and priority are identical across all five for a given `id`: they are translations of one ticket, labeled once in English and carried over, never re-labeled per language.

**Pipeline:**

1. **Source** — BANKING77 train/test, English text and intent only. No sentiment or priority ground truth exists upstream.
2. **Labeling** — sentiment and priority are LLM-derived; intent comes from BANKING77 itself. `datasets/translation/prompts/` holds prompt versions v1 → v5, each validated against a hand-annotated gold set before being trusted on the full corpus. v5 is frozen and is the only source of truth.
3. **Translation** — English is machine-translated to Sinhala, then hand-corrected category by category into colloquial, code-mixed Sinhala rather than literal MT output (style rules in `datasets/translation/SINHALA_STYLE.md`). Tamil is Gemini-translated with no hand-correction pass yet.
4. **Romanization** — Singlish is rule-generated from the corrected native-script text, preserving English loanword spelling per the tokenizer finding above. Edits are made in the romanized file (the human-readable one) and backported into the Sinhala source via diff/update scripts rather than maintained in two places.
5. **Auditing** — cross-language dedup and audit passes resolve label conflicts, true duplicates versus translation collisions, and untranslated rows. Audits never mutate source CSVs; they emit review files for a human pass to apply.

Working rule: a dataset's own heuristic labels are never trusted as ground truth when tuning a labeling prompt — every prompt version is checked against a freshly hand-annotated gold set first.

**Bake-off** ([`ml/`](ml/README.md), driven from `notebooks/modeling/`) runs on a frozen split — 8,500 train / 1,498 dev / 3,079 test, drawn once on `id` and fanned out to all five languages, never regenerated. Splitting on rows instead of `id` would put a ticket's English copy in train and its Sinhala copy in dev. Model selection happens on dev; test is touched once at the end by winners only.

Three measured floors shape how results are reported:

| task | floor | result |
|---|---|---|
| Sentiment | always answer `Neutral` | 95.5% accuracy, **0.000** Negative-F1 — so Negative-F1 is reported, never accuracy |
| Priority | predicted intent → majority-priority lookup (`intent-chained`) | macro-F1 0.892–0.904 — the honest bar |
| Priority | **gold** intent → lookup | macro-F1 0.9147 — an *oracle*, not a target; gold intent doesn't exist at serving time |

On dev, a direct TF-IDF priority classifier beats `intent-chained` in all five languages (+0.7 to +1.9pp macro-F1), so priority earns its own head rather than hanging off the intent model. For sentiment, the highest-*accuracy* arm is the worst model: unbalanced training scores 0.962 accuracy at 0.357 Negative-F1, while `class_weight` scores 0.955 accuracy at 0.580.

---

## Software Engineering

The planned application (`context/architecture.md`) is a two-service system:

| Layer | Stack |
|---|---|
| Frontend | React 19 + TypeScript strict + Tailwind (Vite; see note below) |
| Backend | FastAPI (Python 3.11+, typed/mypy) |
| Data | PostgreSQL 16 + pgvector (tickets, messages, KB articles, embeddings) |
| Classification | XLM-RoBERTa backbone + per-language LoRA experts |
| Language ID | Unicode script detection + per-pair CRF/XGBoost for code-mixed Si-En / Ta-En |
| Multimodal | Whisper/MMS (ASR), Tesseract `sin+tam+eng` (OCR), Coqui/Indic-TTS |
| RAG | BGE-M3/e5 embeddings in pgvector, Gemini (prod) / Ollama (dev) |
| Channels | Web widget, Telegram, WhatsApp (Twilio/Meta) |

Decisions worth noting:

- **Pluggable banking data access** — `BankingProvider` is a Protocol with a stable record schema. `MockBankingProvider` is the only implementation (no real bank partner), but a real integration is one adapter, not a pipeline rewrite.
- **Classification never touches the LLM** — intent, priority, and sentiment are served by trained discriminative models (target <100ms, kept warm as singletons); the LLM generates replies only. Keeps latency and cost predictable and avoids hallucinated labels.
- **Scope is explicitly split** — `context/project-overview.md` marks which features match the submitted proposal (multimodal ingestion, trilingual classification, agent dashboard with label correction) versus the applied extension on top (RAG replies, TTS, Telegram/WhatsApp).
- **Frontend stack is unresolved** — `architecture.md` specifies Next.js 16 App Router, but the prototype was built on Vite + React Router, which suits a static nginx deployment against a separate FastAPI backend. The spec has not been reconciled.

---

## Repository Layout

```text
backend/                     FastAPI API, PostgreSQL models/migrations, auth and workers
frontend/                    Vite + React + TypeScript support-ticket triage prototype
context/                     Product spec, architecture, model research, standards, progress
research/                    Primary-source papers backing modeling decisions
datasets/                    BANKING77-derived trilingual pipeline (translation, romanization, labeling)
ml/                          Everything that trains or evaluates a model — see ml/README.md
  swiftbench/                Shared harness: frozen split, metrics, baselines, result format
  scripts/                   Standalone CLI training runs (intent only)
  configs/ splits/           Recorded experiment configs; the frozen split manifest
  models/ predictions/ reports/   Run artifacts
notebooks/modeling/          Experiment notebooks driving swiftbench (intent, sentiment, priority)
notebooks/baselines/         TF-IDF feature-pipeline walkthrough
notebooks/data_preparation/  Dataset characteristics, cleaning and prompt-benchmark analysis
docs/                        API, database and RAG-source documentation
srs/                         Software requirements specification (LaTeX)
feasibility report/          Feasibility study (LaTeX)
scripts/                     Standalone data-cleaning utilities
synthetic_ticket_dataset/    Synthetic multimodal (image) ticket samples
```
