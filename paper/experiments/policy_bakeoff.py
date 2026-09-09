"""Literature-grounded bake-off: how should a support queue be ordered?

Nothing in this file is a scoring function we invented. Every ordering policy below is a
named rule from the scheduling / queueing literature, and every label model is a named
estimator from the multi-label literature. Each carries the result that licenses it and
the assumptions that result needs. Where a published rule assumes the job's class is
*known* and we only have a classifier posterior, the adaptation is itself cited
(Argon & Ziya 2009), not improvised.

---------------------------------------------------------------------------
WHY THE LABELS CANNOT BE TREATED AS THREE INDEPENDENT SIGNALS
---------------------------------------------------------------------------
Measured on train (english track, n = 9,998), in nats:

    H(priority)            0.9333
    I(intent; priority)    0.7178   = 76.9% of H(priority)
    I(sentiment; priority) 0.0172   =  1.8% of H(priority)
    I(intent; sentiment)   0.0453   = 19.3% of H(sentiment)
    I(sent; prio | intent) 0.0149   -> only 13.4% of the sentiment-priority
                                       association is explained away by intent

Intent very nearly determines priority. So any additive score of the form
`w_P * f(priority head) + w_I * g(intent head)` is adding two estimates of substantially
the same quantity, and the weight it fits is not a measure of how much the intent term
contributes -- it is an artefact of the collinearity. This is the standard failure of
*binary relevance* (independent per-label models) under label dependence, which is the
problem classifier chains were introduced to solve (Read et al. 2009).

Sentiment is the opposite case: it carries little information about priority in absolute
terms (1.8% of H(priority)), but what it carries is *not* redundant with intent (86.6%
of its association with priority survives conditioning on intent). So sentiment is a weak
but genuinely independent signal, and intent is a strong but almost entirely redundant
one. Those two facts pull in opposite directions and neither is visible in a fitted
simplex weight.

---------------------------------------------------------------------------
THE COST MODEL, AND WHY IT IS NOT A FREE PARAMETER
---------------------------------------------------------------------------
Every policy below needs a per-class delay cost rate c_k and/or a deadline D_k. We take
D_k from the first-response SLA and set

    c_k = 1 / D_k

so that one SLA-window of delay costs the same for every class. This is not a tuning
choice: it is the design intent of Kleinrock's delay-dependent priority, whose whole
purpose was to hit targets expressed as *ratios* of class waiting times
(Kleinrock 1964; Stanford, Taylor & Ziedins 2014). It also makes the objective
scale-free, so no class's cost can be inflated by choosing its units.

D_k is an assumption about the desk, not a measurement -- see tracker E10.

References
    Cobham (1954)                Priority assignment in waiting line problems. Opns Res 2(1).
    Jackson (1955)               Scheduling a production line to minimise maximum tardiness.
    Cox & Smith (1961)           Queues. (the c-mu rule)
    Kleinrock (1964)             A delay dependent queue discipline. Nav Res Log 11(3).
    Van Mieghem (1995)           Dynamic scheduling with convex delay costs: the
                                 generalized c-mu rule. Ann Appl Prob 5(3):809-833.
    Argon & Ziya (2009)          Priority assignment under imperfect information on
                                 customer type identities. M&SOM 11(4):674-693.
    Read et al. (2009)           Classifier chains for multi-label classification. ECML.
    Dembczynski et al. (2010)    Bayes optimal multilabel classification via
                                 probabilistic classifier chains. ICML.
    Stanford, Taylor & Ziedins   Waiting time distributions in the accumulating
      (2014)                     priority queue. Queueing Syst 77(3):297-330.
    Wolpert (1992)               Stacked generalization. Neural Networks 5(2).
"""
from __future__ import annotations

import heapq
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
POSTERIORS = REPO / "paper" / "results" / "posteriors"
OUT = REPO / "paper" / "results" / "tables"
sys.path.insert(0, str(REPO / "ml"))

PRIORITY_CLASSES = ["Low", "Medium", "High"]
SLA_MINUTES = {"Low": 480.0, "Medium": 120.0, "High": 30.0}
D = np.array([SLA_MINUTES[k] for k in PRIORITY_CLASSES])   # deadline per class
C = 1.0 / D                                                # cost rate per class

SERVICE_MEAN_MIN = 8.0
SERVICE_SIGMA = 0.75
N_AGENTS = 5
TICKETS_PER_REPLICATION = 1000


# ==========================================================================
# LABEL MODELS -- how the three dependent labels produce P(priority | ticket)
# ==========================================================================
# Priority is the cost-bearing class: the delay cost of a ticket is a property of how
# urgent it actually is. Intent and sentiment enter only through what they say about
# priority. That is a modelling commitment, and it is the one the scheduling literature
# requires -- every rule below is defined over a distribution on the *cost-bearing*
# class, so a signal that does not speak to delay cost has no place in the index.

def _train_dev() -> pd.DataFrame:
    from swiftbench import config, splits
    tr = splits.get(config.LANGUAGES, "train")
    dv = splits.get(config.LANGUAGES, "dev")
    return pd.concat([tr, dv], ignore_index=True)


def _conditional_table(df: pd.DataFrame, by: list[str], smoothing: float = 1.0
                       ) -> pd.DataFrame:
    """P(priority | by), Laplace-smoothed so unseen cells fall back to the base rate."""
    counts = (df.groupby(by)["priority"].value_counts().unstack(fill_value=0)
              .reindex(columns=PRIORITY_CLASSES, fill_value=0).astype(float))
    base = df["priority"].value_counts(normalize=True).reindex(PRIORITY_CLASSES).to_numpy()
    return (counts + smoothing * base) .div((counts.sum(axis=1) + smoothing), axis=0)


def _load(task: str, model: str, portion: str) -> pd.DataFrame:
    return pd.read_csv(POSTERIORS / f"{task}__{model}__{portion}.csv", comment="#")


def build_frame(priority_model: str, sentiment_model: str, intent_model: str,
                portion: str) -> pd.DataFrame:
    """One row per ticket with the full posterior from each head, joined on (id, language)."""
    pri, sen, itn = (_load("priority", priority_model, portion),
                     _load("sentiment", sentiment_model, portion),
                     _load("intent", intent_model, portion))
    key = pd.MultiIndex.from_arrays([pri["id"], pri["language"]])
    sen_i, itn_i = (sen.set_index(["id", "language"]), itn.set_index(["id", "language"]))

    frame = pd.DataFrame({"id": pri["id"], "language": pri["language"],
                          "gold_priority": pri["y_true"],
                          "pred_priority": pri["y_pred"]})
    for k in PRIORITY_CLASSES:
        frame[f"pri_{k}"] = pri[f"p_{k}"].to_numpy()
    frame["p_negative"] = sen_i["p_Negative"].reindex(key).to_numpy()
    frame["pred_intent"] = itn_i["y_pred"].reindex(key).to_numpy()
    frame["gold_intent"] = itn_i["y_true"].reindex(key).to_numpy()

    # Full intent posterior, kept as a matrix so the chain can marginalise over it
    # rather than conditioning on the argmax -- conditioning on a hard intent throws
    # away exactly the uncertainty the chain exists to propagate.
    icols = [c for c in itn.columns if c.startswith("p_")]
    frame.attrs["intent_labels"] = [c[2:] for c in icols]
    frame.attrs["intent_post"] = itn_i[icols].reindex(key).to_numpy()
    if frame.isna().any().any():
        raise ValueError("join on (id, language) left gaps")
    return frame


def label_model(name: str, frame: pd.DataFrame, fitted: dict) -> np.ndarray:
    """Return an (n, 3) posterior over PRIORITY_CLASSES."""
    P_direct = frame[[f"pri_{k}" for k in PRIORITY_CLASSES]].to_numpy()

    if name == "marginal":
        # BINARY RELEVANCE (Read et al. 2009's baseline). The priority head alone,
        # ignoring the other two labels. Correct if and only if priority is
        # conditionally independent of intent and sentiment given the text -- which
        # the mutual information above says is false, but it is the honest null.
        return P_direct

    if name == "chain-intent":
        # PROBABILISTIC CLASSIFIER CHAIN, intent -> priority (Read et al. 2009;
        # Dembczynski et al. 2010). Marginalises over the intent posterior:
        #     P(prio | x) = sum_i P(intent=i | x) * P(prio | intent=i)
        # P(prio | intent) is estimated on train+dev gold only. This is the correct
        # way to use intent: as a conditioning variable in a joint model, not as an
        # additive third term that re-states the priority head.
        return frame.attrs["intent_post"] @ fitted["p_prio_given_intent"]

    if name == "chain-full":
        # The two-parent chain, intent AND sentiment -> priority. Marginalises over
        # both posteriors. This is the model the measured dependence argues for:
        # intent carries most of the signal, sentiment carries a little that intent
        # does not, so conditioning on both is strictly better specified than either.
        tab_neg, tab_neu = fitted["p_prio_given_intent_neg"], fitted["p_prio_given_intent_neu"]
        pn = frame["p_negative"].to_numpy()[:, None]
        return (frame.attrs["intent_post"] @ tab_neg) * pn + \
               (frame.attrs["intent_post"] @ tab_neu) * (1.0 - pn)

    if name == "logpool":
        # LOGARITHMIC OPINION POOL of the direct head and the intent chain. The
        # standard aggregator for *dependent* probabilistic experts: the linear pool
        # double-counts shared evidence, the log pool combines log-odds and is
        # externally Bayesian. Given I(intent;priority) = 77% of H(priority), the two
        # experts here are heavily overlapping, which is exactly the case the linear
        # pool handles worst.
        P_chain = frame.attrs["intent_post"] @ fitted["p_prio_given_intent"]
        G = np.exp(0.5 * np.log(P_direct + 1e-12) + 0.5 * np.log(P_chain + 1e-12))
        return G / G.sum(axis=1, keepdims=True)

    if name == "stacked":
        # STACKED GENERALIZATION (Wolpert 1992): a multinomial logit whose features are
        # the other models' outputs, fitted on dev and applied unchanged to test. Lets
        # the data resolve the collinearity instead of a hand-set weight. This is the
        # only member of the family that can express *suppression* (a negative
        # coefficient), which a simplex of non-negative weights structurally cannot.
        clf = fitted["stacker"]
        return clf.predict_proba(_stack_features(frame, fitted))

    raise ValueError(f"unknown label model {name!r}")


def _stack_features(frame: pd.DataFrame, fitted: dict) -> np.ndarray:
    P_direct = frame[[f"pri_{k}" for k in PRIORITY_CLASSES]].to_numpy()
    P_chain = frame.attrs["intent_post"] @ fitted["p_prio_given_intent"]
    return np.column_stack([P_direct, P_chain, frame["p_negative"].to_numpy()])


def fit_label_models(dev_frame: pd.DataFrame) -> dict:
    """Everything that needs estimating, fitted on train+dev gold or on dev posteriors."""
    from sklearn.linear_model import LogisticRegression
    td = _train_dev()
    fitted: dict = {}

    tab = _conditional_table(td, ["category"])
    fitted["p_prio_given_intent"] = _align(tab, dev_frame.attrs["intent_labels"], td)

    td = td.assign(_neg=(td["sentiment"] == "Negative"))
    for flag, key in ((True, "p_prio_given_intent_neg"), (False, "p_prio_given_intent_neu")):
        sub = td[td["_neg"] == flag]
        fitted[key] = _align(_conditional_table(sub, ["category"]),
                             dev_frame.attrs["intent_labels"], td)

    X = _stack_features(dev_frame, fitted)
    y = dev_frame["gold_priority"].to_numpy()
    clf = LogisticRegression(max_iter=2000)
    clf.fit(X, y)
    # sklearn orders classes alphabetically; reorder columns to PRIORITY_CLASSES.
    order = [list(clf.classes_).index(k) for k in PRIORITY_CLASSES]
    fitted["stacker"] = _Reordered(clf, order)
    return fitted


class _Reordered:
    def __init__(self, clf, order): self.clf, self.order = clf, order
    def predict_proba(self, X): return self.clf.predict_proba(X)[:, self.order]


def _align(tab: pd.DataFrame, intent_labels: list[str], td: pd.DataFrame) -> np.ndarray:
    """(n_intents, 3) matrix in the intent-posterior's own column order."""
    base = td["priority"].value_counts(normalize=True).reindex(PRIORITY_CLASSES).to_numpy()
    return np.vstack([tab.loc[i].to_numpy() if i in tab.index else base
                      for i in intent_labels])


# ==========================================================================
# ORDERING POLICIES -- every one of them published
# ==========================================================================
# Each returns the scheduling index of the waiting tickets at decision time `now`.
# Higher index = served first. `P` is the (n, 3) priority posterior, `age` the time
# each waiting ticket has already spent in the queue.

def policy_index(name: str, P: np.ndarray, age: np.ndarray, beta: float = 2.0
                 ) -> np.ndarray:
    if name == "fcfs":
        # The no-information baseline. Every comparison is against this.
        return age

    if name == "static-tier":
        # COBHAM (1954): fixed priority classes, FIFO within class. What a helpdesk
        # with a High/Medium/Low dropdown actually runs. Uses the ARGMAX, so it is
        # also the policy Argon & Ziya's Theorem 3 says a continuous score must beat.
        return P.argmax(axis=1).astype(float) + 1e-9 * age

    if name == "cmu-hsf":
        # c-mu RULE (Cox & Smith 1961) under an imperfect signal, which is exactly
        # Argon & Ziya's (2009) HIGHEST SCORE FIRST. Service rate is class-independent
        # here (one agent pool, no class-specific handling time), so mu drops out and
        # the index is the expected delay cost rate under the posterior:
        #     index = E[c | posterior] = sum_k p_k c_k
        # THEOREM 3 (Argon & Ziya 2009): the long-run average cost under HSF is at most
        # that of ANY finite-class priority policy. This is the published result that
        # says "order by the posterior, never by the argmax" -- it is a theorem, not an
        # empirical preference.
        # ASSUMES: waiting costs LINEAR in time. If costs are convex, see gcmu.
        return P @ C

    if name == "apq":
        # ACCUMULATING PRIORITY QUEUE (Kleinrock 1964; Stanford, Taylor & Ziedins 2014).
        # Priority accumulates linearly in waiting time at a class-dependent rate b_k;
        # the server takes the highest accumulated priority. Under an imperfect signal
        # the rate is the posterior mean, b_hat = sum_k p_k b_k.
        #     index = b_hat * age
        # WHY THIS RATHER THAN AN AD-HOC AGEING TERM: the APQ was constructed to hit
        # targets stated as RATIOS OF CLASS WAITING TIMES, which is what an SLA is, and
        # its waiting-time distribution is known in closed form per class (Stanford et
        # al. 2014) -- so the ageing rate can be *solved for* from the SLA rather than
        # fitted. It is the healthcare-triage standard for exactly this problem.
        return (P @ C) * age

    if name == "gcmu":
        # GENERALIZED c-mu RULE (Van Mieghem 1995). Index = mu * C'_k(age): the
        # MARGINAL delay cost at the ticket's current age, times the service rate.
        # Asymptotically optimal in heavy traffic for CONVEX delay costs. Under an
        # imperfect signal we take the posterior mean of the marginal cost, which is
        # the extension Argon & Ziya (2009, section 9) found to outperform every other
        # policy they tested under a convex cost structure.
        #     C_k(a) = (a / D_k)^beta   =>   C'_k(a) = beta * a^(beta-1) / D_k^beta
        # beta = 1 recovers the c-mu rule exactly; beta = 2 is the quadratic case
        # Argon & Ziya simulate. NOTE the nesting: cmu-hsf, apq and gcmu are one family
        # at beta = 1, and gcmu at beta = 2.
        return (P @ (beta / D ** beta)) * np.power(np.maximum(age, 0.0), beta - 1.0)

    if name == "edd":
        # EARLIEST DUE DATE (Jackson 1955): minimises maximum lateness on a single
        # machine. Deadline under the posterior is D_hat = sum_k p_k D_k; the index is
        # negative slack, so the most overdue ticket goes first.
        # ASSUMES: the objective is lateness, not weighted delay cost. Included because
        # it is the policy an SLA-driven desk reaches for first, and because it is the
        # natural competitor to APQ.
        return -(P @ D) + age

    raise ValueError(f"unknown policy {name!r}")


POLICIES = ["fcfs", "static-tier", "cmu-hsf", "apq", "gcmu", "edd"]
LABEL_MODELS = ["marginal", "chain-intent", "chain-full", "logpool", "stacked"]

TIME_VARYING = {"fcfs", "apq", "gcmu", "edd"}   # must be re-ranked at every decision


# ==========================================================================
# SIMULATOR
# ==========================================================================

@dataclass
class SimConfig:
    rho: float
    n_agents: int = N_AGENTS
    service_mean: float = SERVICE_MEAN_MIN
    service_sigma: float = SERVICE_SIGMA
    n_tickets: int = TICKETS_PER_REPLICATION
    beta: float = 2.0

    @property
    def arrival_rate(self) -> float:
        return self.rho * self.n_agents / self.service_mean


def simulate(frame: pd.DataFrame, P: np.ndarray, policy: str, cfg: SimConfig,
             seed: int) -> pd.DataFrame:
    """One replication. `wait` is time-to-first-response in minutes."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(frame), size=cfg.n_tickets, replace=False)
    sample = frame.iloc[idx].reset_index(drop=True)
    Ps = P[idx]

    arrivals = np.cumsum(rng.exponential(1.0 / cfg.arrival_rate, size=cfg.n_tickets))
    mu = np.log(cfg.service_mean) - cfg.service_sigma ** 2 / 2
    service = rng.lognormal(mu, cfg.service_sigma, size=cfg.n_tickets)

    static = None if policy in TIME_VARYING else policy_index(policy, Ps,
                                                              np.zeros(cfg.n_tickets))
    start = np.empty(cfg.n_tickets)
    agents = [0.0] * cfg.n_agents
    heapq.heapify(agents)
    waiting: list[int] = []
    nxt = 0

    for _ in range(cfg.n_tickets):
        now = heapq.heappop(agents)
        while nxt < cfg.n_tickets and arrivals[nxt] <= now:
            waiting.append(nxt); nxt += 1
        if not waiting:
            now = arrivals[nxt]
            while nxt < cfg.n_tickets and arrivals[nxt] <= now:
                waiting.append(nxt); nxt += 1

        w = np.asarray(waiting)
        if static is not None:
            key = static[w] - 1e-9 * arrivals[w]      # FIFO within ties
        else:
            key = policy_index(policy, Ps[w], now - arrivals[w], cfg.beta)
            key = key - 1e-9 * arrivals[w]
        chosen = int(w[int(np.argmax(key))])
        waiting.remove(chosen)
        start[chosen] = now
        heapq.heappush(agents, now + service[chosen])

    sample = sample.assign(arrival=arrivals, start=start, wait=start - arrivals,
                           policy=policy, seed=seed, rho=cfg.rho)
    return sample


def summarise(sample: pd.DataFrame) -> dict:
    """Scored against GOLD priority throughout -- a policy is judged on the tickets
    that were really urgent, not on the ones it believed were."""
    gold = sample["gold_priority"]
    sla = gold.map(SLA_MINUTES).to_numpy()
    rel_tard = np.maximum(sample["wait"].to_numpy() - sla, 0.0) / sla
    row = {"mean_wait": sample["wait"].mean(),
           "rel_tardiness": rel_tard.mean(),
           "breach_rate": float((sample["wait"].to_numpy() > sla).mean())}
    for k in PRIORITY_CLASSES:
        m = gold == k
        row[f"wait_{k}"] = sample.loc[m, "wait"].mean()
        row[f"p95_{k}"] = sample.loc[m, "wait"].quantile(0.95)
    row["worst_High"] = sample.loc[gold == "High", "wait"].max()
    # The fairness metric: spread of mean High wait across the five language tracks.
    hi = sample[gold == "High"].groupby("language")["wait"].mean()
    row["lang_spread_High"] = float(hi.max() - hi.min())
    return row
