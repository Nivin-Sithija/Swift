# Testing

Every tool here is free and open source. Nothing needs a paid account, and the
whole suite runs without Postgres, Redis, or network access — the fixtures use
in-memory SQLite and stub every external call.

## Quick start

```bash
cd backend
pip install -e '.[dev,rag,security]'
pytest -q                     # 162 passed, 23 xfailed, 2 skipped
```

## The UIs

| Layer | Command | Where it opens |
|---|---|---|
| Backend test report | `pytest --html=reports/report.html --self-contained-html` | `backend/reports/report.html` |
| Backend coverage | `pytest --cov=app --cov-report=html:reports/htmlcov` | `backend/reports/htmlcov/index.html` |
| Frontend test runner | `npm run test:ui` (in `frontend/`) | <http://localhost:51204/__vitest__/> |
| Frontend coverage | `npm run test:coverage` | `frontend/reports/coverage/index.html` |
| Traces and spans | already instrumented | your Logfire project dashboard |

Open a generated report with `open backend/reports/report.html` on macOS.

**pytest-html** is a static, self-contained page: a sortable results table with
filters for passed / failed / xfailed, per-test duration, and captured output
inline. It is one file, so it can be attached to a CI run or emailed.

**Vitest UI** is a live server, not a report. It watches files, re-runs on save,
and shows the module graph and per-test output in the browser. It needs
`--watch`, which the `test:ui` script already passes — without a TTY Vitest
otherwise runs once and exits.

**Logfire** is the runtime UI rather than a test UI: `app/main.py` calls
`logfire.configure(..., send_to_logfire="if-token-present")`, so with
`SWIFT_LOGFIRE_TOKEN` set the traces land in the hosted dashboard, and without
one it silently no-ops and everything still runs. `tests/observability/` asserts
the instrumentation is live and that spans carry no passwords, bearer tokens, or
card numbers.

## Layout

```
tests/
  conftest.py               ASGI app + in-memory SQLite + seeded users
  security/
    test_authz.py           authentication, roles, IDOR
    test_rate_limiting.py   abuse resistance          (6 known gaps)
    test_prompt_injection.py guardrail bypass corpus  (16 known gaps)
    test_input_validation.py payloads, uploads, CORS
  database/test_integrity.py constraints, transactions, SQL injection, migrations
  contract/test_openapi.py   published contract vs. served routes
  observability/test_logfire.py tracing and PII hygiene
```

Run one group with a marker:

```bash
pytest -m security
pytest -m "database or contract"
pytest -m "not slow"
```

## About the `xfail` tests

23 tests are marked `xfail(strict=True)`. They assert the behaviour the system
*should* have and record that it does not hold yet, which keeps the suite green
while the gap is visible in every run. Because they are strict, implementing the
missing behaviour makes them **fail** — that is the signal to delete the marker,
not a regression.

They cover two gaps:

* **Rate limiting** (6) — there is none. `/auth/login` accepts unlimited failed
  password attempts; `/tickets/{id}/assistance` bills a Groq or Gemini call per
  request with no per-customer budget.
* **Prompt injection** (17) — `app/rag/guardrails.py` matches substrings, so it
  catches 3 of 18 corpus variants. Spacing, Unicode, base64, roleplay and
  Sinhala/Tamil paraphrases all pass. One is structural: `route_guardrails`
  inspects `original_query` only, while `ticket_context` goes into the prompt
  unscanned.

## Gates

These are what `.github/workflows/ci.yml` runs. All pass on `main` as of
2026-09-05:

```bash
ruff check app tests      # lint
mypy app                  # strict types, 35 files
bandit -q -r app -ll      # SAST, medium severity and above
pip-audit                 # dependency advisories
pytest -q --cov=app
```

Frontend:

```bash
npm run lint
npm run typecheck
npm run test:coverage
npm audit --audit-level=high
```

## Reviewed static-analysis findings

Bandit reports `B608` (string-built SQL) twice in `app/rag/retrieval.py`. Both
are false positives: the only value interpolated is the module-local `filters`
constant and every caller value is a bound parameter. They carry `# nosec B608`
with that justification, and
`tests/database/test_integrity.py::test_retrieval_sql_interpolates_no_caller_data`
fails if anyone later interpolates a variable there — so the dismissal cannot go
stale.

## Notes

* `backend/reports/` and `frontend/reports/` are gitignored; regenerate them with
  the commands above.
* mypy is configured for Python 3.12 to match the local venv, but
  `backend/Dockerfile` ships `python:3.11-slim`. Align one of them.
