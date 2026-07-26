# Swift

Trilingual (Sinhala / English / Tamil), multimodal AI support-ticket triage system for banking and fintech. Incoming tickets — text, voice, or image (bank slips, receipts, error screenshots) — are transcribed/OCR'd, classified by category, priority, and sentiment, and routed: routine questions get a RAG-grounded drafted reply, fraud/urgent/negative-sentiment tickets escalate to a human agent.

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

The dataset-engineering work (`datasets/`) turns [BANKING77](https://huggingface.co/datasets/PolyAI/banking77) (13,083 English support queries, 77 intents) into a labeled, trilingual, multi-script benchmark for the classifier bake-off.

**Pipeline:**
1. **Source** — BANKING77 `train.csv` / `test.csv` (`datasets/original-dataset/`), English text + intent only — no category/sentiment/priority ground truth exists upstream.
2. **Labeling** — sentiment, priority, and (planned) category are LLM-derived, not scraped. `datasets/translation/prompts/` holds iterative prompt versions (v1 → v5); each version was validated against a hand-annotated gold benchmark subset before being trusted to label the full set (per-language folders directly under `datasets/`, e.g. `datasets/english/`, incl. mismatch-analysis CSVs and a Label Studio config for manual review). v5 is the current production prompt.
3. **Translation** — English rows are machine-translated to Sinhala, then **hand-corrected by category** into colloquial, code-mixed Sinhala (not literal MT output) — tracked in a progress CSV, style rules documented in `datasets/translation/SINHALA_STYLE.md`.
4. **Romanization (Singlish)** — a rule-based transliterator (`romanize.py`, `singlishify.py`, `singlish_overrides.py`) generates romanized Sinhala from the corrected native-script text, preserving English loanword spelling per the Script Sensitivity finding above. Edits happen in the romanized (Singlish) CSV, since that's what's human-readable, and get **backported into the Sinhala source** via diff/update scripts (`singlish_diff.py`, `update_sinhala.py`) rather than maintained in two places by hand.
5. **Auditing** — `audit_sentiment.py` / `apply_bulk_sentiment_fix.py` catch and bulk-correct systematic labeling errors after review; `datasets/localization/` runs a similar review pass over category localization.
6. **Analysis** — `notebooks/dataset_characteristics_english.ipynb` (class balance, text length, vocabulary) and `notebooks/prompt_benchmark_findings.ipynb` (prompt-version accuracy comparison against gold labels) document the dataset and prompt-selection evidence.

Working rule for this pipeline: a dataset's own heuristic labels are never trusted as ground truth for tuning a labeling prompt — every prompt version is checked against a freshly hand-annotated gold set first.

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
