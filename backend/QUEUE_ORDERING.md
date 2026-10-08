# Ticket queue ordering

The staff ticket queue defaults to **Dynamic urgency**. It follows Sections V-VI
of `ICATC_Paper (1).pdf`, equations (1)-(3), using the repository's accompanying
`paper/experiments/policy_bakeoff.py` for the conditional-table estimator.

## Scoring

1. Preserve full, uncalibrated intent, priority and sentiment model distributions.
2. Form `chain[k] = sum_i P(intent=i) P(priority=k | intent=i)`.
3. Normalize `sqrt((head[k] + 1e-12) * (chain[k] + 1e-12))` over Low/Medium/High.
4. Compute expected severity with class values `0, 0.5, 1`.
5. `S = 0.80 * expected_severity + 0.10 * P(negative) + 0.10 * kappa(top_intent)`.
6. `U = S * (1 + 16 * waiting_minutes / SLA_minutes)`.

The paper's assumed response windows are High=30, Medium=120, Low=480 minutes.
The pooled argmax selects the window. These are research assumptions, not measured
or contractually established bank SLAs. The UI refreshes aging/order every 30 seconds.
Ties use oldest arrival, then ticket ID. Responded, resolved and closed tickets
receive zero dispatch urgency and appear after active tickets in this sort.
Waiting time uses original arrival, including reopened tickets, as in the paper.

## Explicit operational adaptations

- `S` has a 0.01 floor: the paper's literal `S=0` case cannot age under multiplication.
  This ensures positive aging for every waiting ticket; it is not a guarantee of
  bounded delays under arbitrary overload.
- The application's additional **critical** tier uses severity 1 and a 30-minute
  window. Its existing keyword override remains effective. It is not a permanent
  pin above every aged ticket; dynamic scores still determine order.
- A staff-reviewed priority is authoritative and bypasses the priority log pool.
  Reviewed intent/sentiment are treated as point-mass decisions.
- Legacy predictions, OCR-only outputs and rule fallbacks may have no complete
  distribution. A stored priority label supplies its severity; a missing label
  uses the training base rate. No probability vector is invented from the top-label
  confidence. The API exposes `label_fallback` and the UI marks it **estimated**.
  A complete priority posterior with no complete intent posterior uses `priority_head`.
- An unseen intent uses the training priority base rate/criticality. Incomplete
  Gradio top-k distributions are retained as labels, not normalized into false certainty.

## Provenance

`app/domain/queue_priors.json` contains aggregate statistics only, no customer text.
Rebuild with `python backend/scripts/build_queue_priors.py` from the repository root.
It uses frozen manifest `e7b5934392cd`, train+dev only (49,990 language rows,
9,998 underlying tickets), using the paper's existing estimator. Test rows are
never read. Current local CSVs reproduce all but one archived kappa exactly;
`transfer_not_received_by_recipient` differs by 0.000171. The exported values
are reproducible from the recorded current inputs rather than silently mixing
an older criticality artifact with a newly estimated conditional table.
The conditional table uses one base-rate
pseudo-observation per intent; kappa is the empirical unsmoothed High fraction.
Input hashes and split membership provenance are recorded in the exported artifact.

## API and deployment

Run `alembic upgrade head` in the backend environment before starting the new API.
Migration `0008_prediction_probabilities` adds a nullable JSON column; existing
rows remain usable through the explicit fallback. They are not silently reclassified
or sent to external inference. New submissions and attachment processing save the
probabilities when available.

The configured hosted Space `shazan18/Swift-Support-Demo` was updated with user
approval on 2026-10-02 in commit `29f55af1708c2b9e55745593c4c6c62fc4c512f0`.
Its intent output now uses `num_top_classes=None` to return all 77 probabilities.
Gradio's previous top-five setting truncated both the visible labels and API
result. The one-line patch is retained in `deployment/space-full-probabilities.patch`;
`scripts/enable_space_posteriors.py` applies it idempotently with a parent-commit
check. Verify the live model and scoring path with
`python scripts/verify_space_posteriors.py` from the backend directory.
If the service ever returns truncated outputs, new tickets use `priority_head` mode. Completeness checks
require 77/3/2 classes for the intent/priority/sentiment model outputs, even when
a truncated top-k response happens to sum to 1 after rounding.

`GET /api/v1/tickets?sort=urgency` ranks all matching tickets before pagination for
staff, using one evaluation time. Customer scope and newest-first ordering remain
unchanged. Urgency components are returned only in staff responses.
The current frontend fetches all pages in stable newest order, then filters and
sorts the full backlog locally, allowing waiting-time updates without repeated model
calls. Server urgency ordering currently scores matching tickets in memory; very
large backlogs should move to persisted score components and database ordering.

The paper's Table V establishes log pooling as its best probability combination
(log loss 0.2683, macro-F1 0.8983). Its conclusion explicitly says dynamic dispatch
is specified, not validated under load. Implementation tests verify the formula and
behavior; they do not establish optimal scheduling or operational SLA improvements.
