# Consumer banking RAG

The RAG subsystem is isolated under `app/rag`. It creates drafts for authenticated support staff;
it never approves or sends responses. Existing ticket classification, OCR/attachment handling, and
response approval remain unchanged.

## Flow

`original text/OCR/ASR -> existing intent, sentiment, priority -> safety router -> escalation or RAG`

The RAG path conservatively normalizes the query while retaining the original, performs BGE-M3
dense and PostgreSQL full-text retrieval over approved/current sources, combines rankings with RRF,
uses FlashRank, expands selected chunks by one neighbor, computes evidence confidence, calls Groq
with Gemini fallback, validates grounding/citations, and returns an agent-approval-required draft.

Bank-specific retrieval must include `institution`. When it is omitted and candidates contain more
than one bank, the request is escalated as ambiguous. CBSL material is marked separately from bank
policy. Only `approved` sources within the configured review age are eligible.
The manifest checksum is verified against the immutable raw capture (matching the existing cleaner's
contract); chunks are built only from its corresponding cleaned Markdown.

## Setup and run

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,rag]'
alembic upgrade head
swift-ingest-kb --manifest ../docs/rag_sources/rag_source_manifest.csv --root ../docs/rag_sources
uvicorn app.main:app --reload
```

Or run `docker compose up --build`, then execute ingestion inside the API container. The API is
`POST /api/v1/consumer-assistance/drafts` and requires an agent/administrator bearer token.

Required generation configuration (never commit values):

```dotenv
SWIFT_GROQ_API_KEY=
SWIFT_GROQ_MODEL=llama-3.3-70b-versatile
SWIFT_GEMINI_API_KEY=
SWIFT_GEMINI_MODEL=gemini-2.5-flash
```

For hosted BGE-M3 embeddings without local PyTorch:

```dotenv
SWIFT_RAG_EMBEDDING_PROVIDER=huggingface
SWIFT_HUGGINGFACE_TOKEN=
SWIFT_HUGGINGFACE_PROVIDER=hf-inference
SWIFT_RAG_EMBEDDING_MODEL=BAAI/bge-m3
```

The token needs Inference Providers permission. Set `SWIFT_HUGGINGFACE_ENDPOINT_URL` only when
using a dedicated endpoint URL. For local BGE-M3 instead, set the provider to `local` and install
`pip install -e '.[rag-local]'`; that optional extra includes the PyTorch-backed FlagEmbedding stack.

`SWIFT_GEMINI_API_KEY` is optional, but without it provider failure escalates instead of falling back.
Retrieval tuning is controlled by `SWIFT_RAG_EMBEDDING_MODEL`,
`SWIFT_RAG_EMBEDDING_DIMENSIONS`, `SWIFT_RAG_CANDIDATE_LIMIT`, `SWIFT_RAG_FINAL_LIMIT`,
`SWIFT_RAG_MIN_CONFIDENCE`, and `SWIFT_RAG_REVIEW_MAX_AGE_DAYS`.

## Evaluation

`evaluation/multilingual_cases.jsonl` seeds English, Sinhala, Tamil, Singlish, and Tamilish cases.
`app.rag.evaluation` computes retrieval, answer, citation, language, safety, and latency metrics and
can summarize by language/category. Faithfulness, relevance, citation correctness, and language
correctness are explicit evaluator inputs so deployments can plug in reviewed human labels or a
separately governed judge; the production answer model is never used as its own confidence signal.
