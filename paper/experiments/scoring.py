"""The Ticket Urgency Score (TUS) -- the paper's system contribution.

    U(t, tau) = S(t) * (1 + alpha * age(t, tau))

    S(t) = w_P * E[sev | t] + w_S * P(Negative | t) + w_I * kappa(intent(t))

Design rationale lives in `paper/SYSTEM_PLAN.md` section 2. The three points that
matter most when reading this code:

**Expected severity, not the argmax.** `E[sev|t] = sum_k p_k * sev_k`. Collapsing
the posterior to a tier throws away confidence, and confidence is the whole reason
a scoring function beats tiered FIFO. D3 found priority errors concentrate on the
Low/Medium boundary -- exactly where the argmax discards the most.

**kappa is derived, not hand-written.** `kappa(i) = P(High | intent=i)` estimated on
train+dev. It is a prior that backstops the priority head when the text is degraded,
which is the romanized-track case, and it is the only place a human-labelled signal
(BANKING77 intent) enters the ordering.

**Aging is multiplicative.** Additive aging lets any stale ticket overtake any fresh
one once `alpha * age > 1`, including a fresh High. Multiplicative aging amplifies
the urgency a ticket already had, so a stale Low still climbs more slowly than a
stale High. `alpha = 0` recovers a pure static-priority queue as a nested case.

The weights live on the simplex (w >= 0, sum w = 1) so they read as proportions of
the score and so the fit is identifiable. They are fitted on **dev** and the fitted
vector is applied unchanged to test.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
POSTERIORS = REPO / "paper" / "results" / "posteriors"

# Severity is the cost of leaving a ticket of that class unhandled, on [0, 1].
# Linear in the tier because nothing in the data justifies a curve, and a convex
# choice here would silently do some of the scoring function's work for it.
SEVERITY = {"Low": 0.0, "Medium": 0.5, "High": 1.0}

# First-response SLA per class, in minutes. The paper's stated assumption, not a
# measurement from a real desk -- see SYSTEM_PLAN section 4.
#
# Chosen so that *both* failure modes bind somewhere in the load sweep. An earlier
# draft used 60/240/1440 and every policy scored a 0.0 breach rate at every load,
# which measures the thresholds, not the policies. At 30/120/480 the FIFO baseline
# breaches on High under load and an un-aged urgency score breaches on Low -- which
# is the trade-off the aging term exists to manage, and it has to be visible.
SLA_MINUTES = {"High": 30.0, "Medium": 120.0, "Low": 480.0}


@dataclass(frozen=True)
class Weights:
    """A point on the 3-simplex plus the aging coefficient."""
    w_priority: float
    w_sentiment: float
    w_intent: float
    alpha: float = 0.0

    def __post_init__(self) -> None:
        total = self.w_priority + self.w_sentiment + self.w_intent
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1, got {total}")
        if min(self.w_priority, self.w_sentiment, self.w_intent) < 0 or self.alpha < 0:
            raise ValueError("weights and alpha must be non-negative")

    def as_dict(self) -> dict[str, float]:
        return {"w_priority": self.w_priority, "w_sentiment": self.w_sentiment,
                "w_intent": self.w_intent, "alpha": self.alpha}


def load_posteriors(task: str, model: str, portion: str) -> pd.DataFrame:
    path = POSTERIORS / f"{task}__{model}__{portion}.csv"
    return pd.read_csv(path, comment="#")


@functools.lru_cache(maxsize=1)
def load_criticality() -> pd.Series:
    crit = pd.read_csv(POSTERIORS / "intent_criticality.csv", comment="#",
                       index_col="category")
    return crit["kappa"]


def expected_severity(priority_posterior: pd.DataFrame) -> np.ndarray:
    """sum_k p_k * sev_k over whatever priority columns are present."""
    cols = [c for c in priority_posterior.columns if c.startswith("p_")]
    missing = set(SEVERITY) - {c[2:] for c in cols}
    if missing:
        raise ValueError(f"priority posterior is missing columns for {sorted(missing)}")
    return sum(priority_posterior[f"p_{name}"].to_numpy() * sev
               for name, sev in SEVERITY.items())


def build_signal_frame(priority_model: str, sentiment_model: str,
                       intent_model: str, portion: str) -> pd.DataFrame:
    """One row per (ticket, language) with the three score components and the gold labels.

    Joined on (id, language) rather than on row order. The three posterior files
    are written by separate fits and a positional join would be silently wrong the
    first time any of them is regenerated in a different order.
    """
    pri = load_posteriors("priority", priority_model, portion)
    sen = load_posteriors("sentiment", sentiment_model, portion)
    itn = load_posteriors("intent", intent_model, portion)
    kappa = load_criticality()

    if not (len(pri) == len(sen) == len(itn)):
        raise ValueError(f"posterior files disagree on length: "
                         f"priority {len(pri)} sentiment {len(sen)} intent {len(itn)}")

    frame = pd.DataFrame({
        "id": pri["id"], "language": pri["language"],
        "gold_priority": pri["y_true"],
        "sev_hat": expected_severity(pri),
        "pred_priority": pri["y_pred"],
    })
    sen_idx = sen.set_index(["id", "language"])
    itn_idx = itn.set_index(["id", "language"])
    key = pd.MultiIndex.from_arrays([frame["id"], frame["language"]])

    frame["p_negative"] = sen_idx["p_Negative"].reindex(key).to_numpy()
    frame["gold_sentiment"] = sen_idx["y_true"].reindex(key).to_numpy()
    frame["pred_intent"] = itn_idx["y_pred"].reindex(key).to_numpy()
    frame["gold_intent"] = itn_idx["y_true"].reindex(key).to_numpy()

    if frame.isna().any().any():
        bad = frame.columns[frame.isna().any()].tolist()
        raise ValueError(f"join on (id, language) left gaps in {bad} -- the posterior "
                         f"files do not cover the same tickets")

    # An intent seen only in test has no kappa estimate. Fall back to the train+dev
    # base rate rather than to 0, which would assert "definitely not urgent" about a
    # category we simply have no evidence on.
    frame["kappa"] = frame["pred_intent"].map(kappa).fillna(kappa.mean())
    frame["gold_sev"] = frame["gold_priority"].map(SEVERITY)
    return frame


def content_score(frame: pd.DataFrame, w: Weights) -> np.ndarray:
    """S(t) -- the time-independent part of the score."""
    return (w.w_priority * frame["sev_hat"].to_numpy()
            + w.w_sentiment * frame["p_negative"].to_numpy()
            + w.w_intent * frame["kappa"].to_numpy())


def urgency(content: np.ndarray, age_minutes: np.ndarray, w: Weights,
            sla_window: float = 240.0) -> np.ndarray:
    """U(t, tau) -- content score amplified by normalised age."""
    return content * (1.0 + w.alpha * (age_minutes / sla_window))


def oracle_content_score(frame: pd.DataFrame) -> np.ndarray:
    """Gold priority tier -- the ceiling, and a genuine upper bound.

    An earlier version blended gold severity with gold sentiment and kappa, by
    analogy with the system's own score. That was wrong: averaging three signals
    lets a gold-Low with negative sentiment outrank a gold-High, so the "oracle"
    was beaten by TUS on High waiting time at some loads. A quantity the system
    under test can beat is not an upper bound.

    Serving every gold-High first, FIFO within tier, minimises High waiting time
    among all work-conserving policies. That is the ceiling, and it makes
    `tier` vs `oracle` a clean same-policy contrast -- predicted labels against
    gold ones -- which is exactly what isolates classifier error.
    """
    return frame["gold_sev"].to_numpy()


def simplex_grid(step: float = 0.05) -> list[tuple[float, float, float]]:
    """Every (w_P, w_S, w_I) on the 3-simplex at the given step. 231 points at 0.05."""
    n = int(round(1.0 / step))
    return [(i / n, j / n, (n - i - j) / n)
            for i in range(n + 1) for j in range(n + 1 - i)]
