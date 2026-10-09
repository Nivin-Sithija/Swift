<h1 align="center">
  <img src="frontend/public/logo.png" alt="" width="44" height="44" align="center" />
  &nbsp;Swift
</h1>

<p align="center"><strong>Banking support, across languages and scripts.</strong><br />
Sinhala · English · Tamil · Singlish · Tamilish</p>

<p align="center">
  <a href="#run-locally">Run locally</a> ·
  <a href="RESULTS.md"><strong>Results</strong></a> ·
  <a href="docs/README.md">Documentation</a> ·
  <a href="ml/README.md">Research harness</a>
</p>

Swift turns customer messages and ticket images into structured banking support tickets: intent, sentiment, priority, and a reviewable response. It pairs a multilingual classifier benchmark with a working React + FastAPI prototype, backed by PostgreSQL, pgvector, and Redis.

### From message to resolution

- **Understand the ticket.** Classify 77 banking intents across native and romanized scripts; extract text from image attachments with OCR.
- **Give agents context.** Review predictions, correct labels, track ticket state, and retain an audit trail.
- **Ground the response.** Retrieve approved banking sources, attach citations, and route sensitive cases through safety checks and human review.
- **Make the evidence inspectable.** Compare classical models, multilingual encoders, and decoder models with recorded splits, label versions, and per-language scores.

The application is a research prototype. Speech input is part of the broader design; the current implementation covers text and images. Real bank integrations and payment execution are outside its scope.

### Run locally

Requires Docker Compose and access to the private corpus. The current backend image expects `datasets/english/train_labeled.csv`; restore that file before building. Model setup and inference configuration are covered in the [local development guide](docs/guides/local-development.md).

```bash
cp backend/.env.example backend/.env
# Set SWIFT_SECRET_KEY to a random secret in backend/.env.
docker compose up --build
```

Open the app at **http://localhost:8080** and the API explorer at **http://localhost:8000/docs**. For separate backend/frontend development, environment setup, and asset requirements, see the [setup guide](docs/guides/local-development.md).

### Research you can trace

The corpus extends BANKING77 into **five aligned language tracks**. Every translation shares its source ticket's `id`; the common CSV schema is `id, text_en, text, category, sentiment, priority`. Intent uses BANKING77 labels. Sentiment and priority are derived labels, with prompt versions recorded separately.

**[RESULTS.md](RESULTS.md)** stays at the repository root as the score-only reference. [Detailed interpretation](ml/reports/RESULTS.md) explains provenance, label versions, split differences, and missing measurements. Compare sentiment with Negative-class F1; compare intent and priority with macro-F1. Scores from different label sets or splits need separate comparisons.

Start experiments with the [shared harness](ml/README.md), [modeling notebooks](notebooks/modeling/), or [Kaggle runner](ml/kaggle/README.md). The [OCR evaluation](ml/OCR/README.md) measures extraction separately. Its [synthetic screenshot dataset](datasets/synthetic_ticket_dataset/README.md) lives under `datasets/`. Corpus rows and large checkpoints are provisioned separately from the code repository.

### Find your way

| Path | What lives here |
| --- | --- |
| [`frontend/`](frontend/) · [`backend/`](backend/README.md) | Agent/customer interface, REST API, inference, and workers |
| [`docs/`](docs/README.md) | Setup guides, specifications, reports, manuscripts, and test evidence |
| [`ml/`](ml/README.md) · [`notebooks/`](notebooks/) | Training harness, experiment configs, evaluations, and recorded runs |
| [`datasets/`](datasets/) | Corpus preparation, translation, romanization, and labeling tools |
| [`paper/`](paper/) · [`research/`](research/README.md) | Reproducibility scripts, analysis artifacts, and research references |
| [`scripts/`](scripts/) | Repository utilities |

For contributions, keep changes scoped and run the relevant [checks](docs/guides/testing.md). Dataset edits must preserve IDs, the six-column schema, and cross-language alignment; modeling changes must preserve the frozen split.

If you use the corpus or models, cite [CITATION.cff](CITATION.cff). It records dataset attribution; the repository does not currently include a standalone code license.
