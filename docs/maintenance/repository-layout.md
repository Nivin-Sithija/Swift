# Repository organization

Cleanup performed on 9 October 2026. The root holds the project entry points (`README.md`, `RESULTS.md`, `CITATION.cff`), Compose configuration, and domain directories. Local agent notes stay ignored.

## Changes

| Previous location | Current location |
| --- | --- |
| `Testing/` | `docs/testing/` for the current master report and evidence; `docs/templates/testing/` for reference material |
| Root `ICATC_Paper/` | `docs/publications/icatc/` — current reviewer-response manuscript |
| `paper/ICATC_Paper/` | `docs/publications/archive/icatc/` — distinct earlier manuscript |
| Root final-report template | `docs/templates/final_report_template.docx` |
| `output/` slide decks | `docs/presentations/` |
| `docs/project-*.pdf` | `docs/project/` |
| Contribution summary | `docs/final_report/` |
| `backend/RAG.md`, `backend/TESTING.md` | `docs/guides/rag.md`, `docs/guides/testing.md` |

Architecture diagram filenames now use underscores instead of spaces; their LaTeX references were updated. Test-evidence utilities and Cypress configuration resolve the new locations; the Word report builder no longer embeds a machine-specific Windows path. The Markdown master test report uses current paths. Submitted Word/PDF reports retain their original text.

## Removed

- Empty tracked credential placeholders: `Gemini key`, `Groq key`, and `Hugging Face token`.
- Unreferenced root `kaggle_script.py`: a configured job snapshot; job generation belongs to `ml/kaggle/runner.py` and `ml/kaggle/kernels/`.
- Unreferenced root `test_api.py`: an old direct HF-inference probe; the application uses its inference router and retains `backend/scripts/test_router.py`.
- Earlier master test report Markdown/Word editions, superseded by the retained v3 report.
- Office lock files, `:memory:.ses` artifacts, macOS metadata, and regenerable Python/lint/type-check caches.
- Empty root `storage/` directory. Service data and storage configuration remain intact; the tracked `pgvector` submodule entry is retained.

Ignore rules cover credential scratch files, environment files, local memory, caches, session artifacts, and Office lock files. Local environments and credentials are also excluded from backend Docker build contexts.

## Kept deliberately

Datasets, translation/labeling tools, frozen splits, shared model configuration, predictions, metric records, checkpoints, annotation evidence, test evidence, and reproducibility scripts stay with their owning workflows. Historical experiment results remain useful evidence even when their models have been superseded. The manuscripts contain different content and are not interchangeable.

New formal documents and operating guides belong in `docs/`; manuals needed beside a dataset or experiment package may remain beside that code. Add documents to [the index](../README.md). Keep filenames free of spaces and keep the root results reference at `RESULTS.md`.
