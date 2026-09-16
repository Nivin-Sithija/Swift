"""Discrete-event queue simulation -- what the classifier scores are actually worth.

A macro-F1 does not tell a support desk which ticket to open next. This does: it
puts the scored tickets through an M/G/m queue and measures the thing an operations
owner is held to -- how long an urgent ticket waits before someone answers it.

Model
-----
    arrivals   Poisson(lambda), tickets drawn from the scored pool
    service    m parallel agents, LogNormal handling time with stated mean
    load       rho = lambda * E[S] / m, swept -- see below
    policies   random | fifo | tier | tus | oracle

**The load sweep is not optional.** Below about rho = 0.7 no queue forms, so every
policy scores identically and any single-load result is a choice of how flattering
to be. Sweeping states plainly where the gains live and where they vanish.

**Attainment, not raw deltas.** `(fifo - tus) / (fifo - oracle)` separates "the
scoring function is well designed" from "the classifiers are accurate". Those are
different claims with different remedies, and the raw delta conflates them.

Every parameter here is a stated assumption, not a measurement from a real desk.
That is the study's main threat to validity and it is handled by sweeping the load
and by reporting attainment, which is invariant to much of the parameterisation.
See `paper/SYSTEM_PLAN.md` section 4.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from scoring import SLA_MINUTES, Weights, content_score, oracle_content_score

POLICIES = ("random", "fifo", "tier", "tus", "oracle")
TIER_RANK = {"High": 2.0, "Medium": 1.0, "Low": 0.0}

# Handling-time model. Mean 8 minutes with a right skew, which is the shape every
# published helpdesk handling-time distribution has; the parameters are ours.
SERVICE_MEAN_MIN = 8.0
SERVICE_SIGMA = 0.75
N_AGENTS = 5
TICKETS_PER_REPLICATION = 1000


@dataclass
class SimConfig:
    rho: float
    n_agents: int = N_AGENTS
    service_mean: float = SERVICE_MEAN_MIN
    service_sigma: float = SERVICE_SIGMA
    n_tickets: int = TICKETS_PER_REPLICATION
    sla_window: float = 240.0
    weights: Weights = field(default_factory=lambda: Weights(1 / 3, 1 / 3, 1 / 3))

    @property
    def arrival_rate(self) -> float:
        """lambda such that rho = lambda * E[S] / m."""
        return self.rho * self.n_agents / self.service_mean


def _service_times(rng: np.random.Generator, n: int, cfg: SimConfig) -> np.ndarray:
    """LogNormal with the configured *mean* (not the configured mu)."""
    mu = np.log(cfg.service_mean) - cfg.service_sigma ** 2 / 2
    return rng.lognormal(mu, cfg.service_sigma, size=n)


def simulate(frame: pd.DataFrame, policy: str, cfg: SimConfig,
             seed: int) -> pd.DataFrame:
    """One replication. Returns the sampled tickets with `wait` in minutes.

    `wait` is time-to-first-response: how long the customer sat in the queue before
    an agent picked their ticket up. Handling time after that is policy-independent
    and is not part of the metric.
    """
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}")
    rng = np.random.default_rng(seed)

    idx = rng.choice(len(frame), size=cfg.n_tickets, replace=False)
    sample = frame.iloc[idx].reset_index(drop=True)

    arrivals = np.cumsum(rng.exponential(1.0 / cfg.arrival_rate, size=cfg.n_tickets))
    service = _service_times(rng, cfg.n_tickets, cfg)

    # Static part of whatever key the policy sorts on. Only `tus` needs re-ranking
    # at decision time, because only it has a time-varying term.
    if policy == "tus":
        static = content_score(sample, cfg.weights)
    elif policy == "oracle":
        # Gold tier, FIFO within tier -- an upper bound, not a gold-fed TUS.
        static = oracle_content_score(sample)
    elif policy == "tier":
        static = sample["pred_priority"].map(TIER_RANK).to_numpy(dtype=float)
    elif policy == "random":
        static = rng.random(cfg.n_tickets)
    else:                                            # fifo
        static = np.zeros(cfg.n_tickets)

    alpha = cfg.weights.alpha if policy == "tus" else 0.0
    start = np.empty(cfg.n_tickets)

    agents = [0.0] * cfg.n_agents
    heapq.heapify(agents)
    waiting: list[int] = []
    next_arrival = 0

    for _ in range(cfg.n_tickets):
        now = heapq.heappop(agents)
        while next_arrival < cfg.n_tickets and arrivals[next_arrival] <= now:
            waiting.append(next_arrival)
            next_arrival += 1
        if not waiting:
            # Every agent is idle and the queue is empty: fast-forward to the next
            # arrival. The outer loop runs once per ticket, so one is always pending.
            now = arrivals[next_arrival]
            while next_arrival < cfg.n_tickets and arrivals[next_arrival] <= now:
                waiting.append(next_arrival)
                next_arrival += 1

        w = np.asarray(waiting)
        if alpha > 0.0:
            key = static[w] * (1.0 + alpha * (now - arrivals[w]) / cfg.sla_window)
        elif policy == "fifo":
            key = -arrivals[w]          # earliest arrival wins
        else:
            # Ties broken by arrival order, so `tier` really is FIFO within tier and
            # a policy is never silently advantaged by the sampling order.
            key = static[w] - 1e-9 * arrivals[w]
        chosen = int(w[int(np.argmax(key))])
        waiting.remove(chosen)

        start[chosen] = now
        heapq.heappush(agents, now + service[chosen])

    sample["arrival"] = arrivals
    sample["start"] = start
    sample["wait"] = start - arrivals
    sample["policy"] = policy
    sample["seed"] = seed
    sample["rho"] = cfg.rho
    return sample


def summarise(sample: pd.DataFrame) -> dict[str, float]:
    """The operations-side metrics, computed against *gold* priority throughout.

    Scoring against gold and not against the prediction is the point: a policy that
    confidently mis-ranks a ticket must be charged for it.
    """
    gold = sample["gold_priority"]
    high = sample.loc[gold == "High", "wait"]
    low = sample.loc[gold == "Low", "wait"]
    deadline = gold.map(SLA_MINUTES).to_numpy()
    absolute = np.maximum(0.0, sample["wait"].to_numpy() - deadline)
    # Tardiness relative to the class's own SLA window, which is the standard
    # scale-free scheduling objective and the one this study fits weights against.
    #
    # An earlier version used absolute tardiness weighted by `gold_sev + 0.5`
    # (Low 0.5, Medium 1.0, High 1.5) and it selected a degenerate scorer. The
    # reason is worth recording, because it is a trap any triage objective can fall
    # into: the class mix here is 55% Low / 36% Medium / 9% High, so Low carried
    # 0.55 x 0.5 = 0.275 of the objective's mass against High's 0.095 x 1.5 = 0.143.
    # The objective therefore rewarded *not starving Low* almost twice as much as
    # it rewarded serving High, and the optimum was a score that barely
    # discriminates at all. Weighting classes by population share rather than by
    # urgency inverts what a triage system is for.
    #
    # Dividing by the deadline fixes it by construction: a High 30 minutes late and
    # a Low 480 minutes late both score 1.0, so the objective is denominated in
    # units of the promise made to that customer.
    relative = absolute / deadline
    return {
        "high_mean_wait": float(high.mean()),
        "high_p95_wait": float(high.quantile(0.95)),
        "low_p95_wait": float(low.quantile(0.95)),
        "mean_wait": float(sample["wait"].mean()),
        "sla_breach_rate": float((sample["wait"].to_numpy() > deadline).mean()),
        "high_sla_breach_rate": float(
            (high.to_numpy() > SLA_MINUTES["High"]).mean()),
        "rel_tardiness": float(relative.mean()),
        "high_rel_tardiness": float(relative[(gold == "High").to_numpy()].mean()),
        "low_rel_tardiness": float(relative[(gold == "Low").to_numpy()].mean()),
    }


def run_grid(frame: pd.DataFrame, rhos, seeds, weights: Weights,
             policies=POLICIES) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every (policy, rho, seed). Returns (per-replication summary, per-language waits)."""
    rows, per_lang = [], []
    for rho in rhos:
        cfg = SimConfig(rho=rho, weights=weights)
        for policy in policies:
            for seed in seeds:
                sample = simulate(frame, policy, cfg, seed)
                rows.append({"policy": policy, "rho": rho, "seed": seed,
                             **summarise(sample)})
                grp = (sample[sample["gold_priority"] == "High"]
                       .groupby("language")["wait"].agg(["mean", "median", "size"]))
                for lang, r in grp.iterrows():
                    per_lang.append({"policy": policy, "rho": rho, "seed": seed,
                                     "language": lang, "mean_wait": r["mean"],
                                     "median_wait": r["median"], "n": int(r["size"])})
    return pd.DataFrame(rows), pd.DataFrame(per_lang)


def attainment(summary: pd.DataFrame, metric: str, policy: str = "tus") -> pd.DataFrame:
    """(fifo - policy) / (fifo - oracle), per rho, with a bootstrap CI over seeds."""
    out = []
    for rho, grp in summary.groupby("rho"):
        piv = grp.pivot(index="seed", columns="policy", values=metric)
        if not {"fifo", "oracle", policy} <= set(piv.columns):
            continue
        head = (piv["fifo"] - piv[policy]).to_numpy()
        room = (piv["fifo"] - piv["oracle"]).to_numpy()
        rng = np.random.default_rng(0)
        boot = []
        for _ in range(2000):
            pick = rng.integers(0, len(head), len(head))
            denom = room[pick].mean()
            boot.append(head[pick].mean() / denom if denom else np.nan)
        boot = np.asarray(boot)
        out.append({"rho": rho, "metric": metric, "policy": policy,
                    "fifo": piv["fifo"].mean(), "policy_value": piv[policy].mean(),
                    "oracle": piv["oracle"].mean(),
                    "attainment": head.mean() / room.mean() if room.mean() else np.nan,
                    "ci_lo": float(np.nanpercentile(boot, 2.5)),
                    "ci_hi": float(np.nanpercentile(boot, 97.5))})
    return pd.DataFrame(out)
