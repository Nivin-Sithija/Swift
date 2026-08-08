# Project Documentation

Formal project documents and interface specifications. Working notes and the
living product spec stay in `context/` (local-only); primary research papers stay
in `research/`.

## Reports

| Document | Source | Output |
| --- | --- | --- |
| Software Requirements Specification (IEEE 830-1998, doc id `G21-SRS-001`) | [srs/srs.tex](srs/srs.tex) | [srs/srs.pdf](srs/srs.pdf) |
| Architecture and design report (use case, class, activity, sequence, deployment, component, package, ER diagrams) | [architecture/architecture.tex](architecture/architecture.tex) | [architecture/architecture.pdf](architecture/architecture.pdf) |
| Feasibility study (financial, technical, resource/time, risk, social/legal) | [feasibility-study/feasibility-study.tex](feasibility-study/feasibility-study.tex) | [feasibility-study/feasibility-study.pdf](feasibility-study/feasibility-study.pdf) |
| Project overview | — | [project-overview.pdf](project-overview.pdf) |
| Original project proposal | — | [project-proposal.pdf](project-proposal.pdf) |

Diagram images for the architecture report live in
[architecture/images/](architecture/images/) and are referenced relatively from
`architecture.tex`, so the report compiles from inside its own directory:

```bash
cd docs/architecture && latexmk -pdf architecture.tex
```

Build artifacts (`.aux`, `.fls`, `.log`, `.out`, `.toc`, `.synctex.gz`,
`.fdb_latexmk`) are gitignored. Both the `.tex` source and the built `.pdf` are
committed.

## Interface specifications

| Spec | File |
| --- | --- |
| REST API contract (OpenAPI 3.0.3) for the implemented backend | [api/api_contract.yaml](api/api_contract.yaml) |
| PostgreSQL schema (DBML) | [database/schema.dbml](database/schema.dbml) |
| dbdiagram.io canvas for the same schema | [database/schema.dbdiagram](database/schema.dbdiagram) |
| System architecture diagram | [architecture/swift-system-architecture.png](architecture/swift-system-architecture.png) |

The running FastAPI app serves `/openapi.json`, which is the executable schema —
`api_contract.yaml` is the reviewed, human-facing contract.
