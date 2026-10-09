# Swift documentation

Start with [local development](guides/local-development.md), the [API contract](api/api_contract.yaml), or the root [results](../RESULTS.md).

## Operating guides

| Guide | Covers |
| --- | --- |
| [Local development](guides/local-development.md) | Environment, assets, Docker Compose, and separate services |
| [Banking RAG](guides/rag.md) | Retrieval, source ingestion, providers, guardrails, and evaluation |
| [Testing](guides/testing.md) | Test commands, coverage, security checks, and report generation |

## Design and project reports

| Document | Read | Source |
| --- | --- | --- |
| Requirements | [PDF](srs/srs.pdf) | [LaTeX](srs/srs.tex) |
| Architecture | [PDF](architecture/architecture.pdf) | [LaTeX](architecture/architecture.tex) |
| Feasibility study | [PDF](feasibility-study/feasibility-study.pdf) | [LaTeX](feasibility-study/feasibility-study.tex) |
| Project overview | [PDF](project/project-overview.pdf) | — |
| Original proposal | [PDF](project/project-proposal.pdf) | — |
| Final report | [Word](final_report/123_Swift_Trilingual_Multimodal_Financial_Support_Ticket_Management_System.docx) | — |
| Individual contributions | [Word](final_report/individual_contribution_summary.docx) | — |
| Master test report | [Markdown](testing/master_test_report.md) · [PDF](testing/master_test_report.pdf) · [Word](testing/master_test_report.docx) | [Evidence](testing/evidence/) |

Proposals and formal reports describe their respective submission snapshots. Use the code and operating guides for current behavior. The Markdown master test report uses the reorganized paths; its Word/PDF editions retain the original submission paths.

## Interfaces and evidence

- [OpenAPI contract](api/api_contract.yaml); the running API also exposes `/openapi.json`.
- Database schema: [DBML](database/schema.dbml) and [dbdiagram canvas](database/schema.dbdiagram).
- [System diagram](architecture/swift-system-architecture.png) and [architecture images](architecture/images/).
- RAG [source manifest](rag_sources/rag_source_manifest.csv), [source validation](rag_sources/source_validation_report.md), and [error analysis](rag_error_analysis/findings.md).
- [Synthetic screenshot dataset](../datasets/synthetic_ticket_dataset/README.md): generator, image labels, and validation.
- [Score tables](../RESULTS.md), [results interpretation](../ml/reports/RESULTS.md), and [method audit](../paper/results/RESEARCH_METHOD_AUDIT.md).

## Publications and reusable material

- Current ICATC manuscript: [PDF](publications/icatc/ICATC_Paper.pdf), [Word](publications/icatc/ICATC_Paper.docx), [LaTeX](publications/icatc/main.tex).
- [Earlier ICATC manuscript](publications/archive/icatc/main.tex) retains distinct wording and references for provenance.
- [Research presentations](presentations/): two-slide and three-slide results decks.
- [Templates](templates/): final report and [test-plan reference material](templates/testing/).

Compile reports from their source directories so relative figures and section inputs resolve:

```bash
cd docs/architecture
latexmk -pdf architecture.tex
```

Experiment-specific manuals stay beside their code in `ml/`, `datasets/`, and `paper/`. Local agent notes remain in the ignored `context/` directory. See the [repository organization record](maintenance/repository-layout.md) for the cleanup decisions.
