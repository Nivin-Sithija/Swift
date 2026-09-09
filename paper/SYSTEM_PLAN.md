# Swift as a system, not a benchmark

The plan for the paper's second contribution: a **ticket ordering system** built on the
classifiers, and the methodology that measures it.

Status board is `TRACKER.md` (track **E**). This file is the design and the argument.

---

## 1. Why the paper needs this

As it stands the paper says: *we built a five-track multilingual ticket corpus and measured
classical, encoder and decoder baselines on it.* Every number in it is real and several are
interesting. It is still a benchmark paper, and a benchmark paper invites one question a
use-case track will ask first and hardest:

> A support desk does not want a macro-F1. It wants to know **which ticket to open next**.
> What does 0.89 priority macro-F1 buy the desk?

Nothing in the current results answers that. Worse, the answer is not obvious, and it is not
monotonic in F1 — a classifier that is 3 points better can produce a queue that is no better
at all, because ordering only depends on the classifier where the queue is actually contended.

So the second contribution is the bridge:

**Classification is the input layer. The contribution is the scoring function that turns three
noisy classifier outputs into one ordering, the methodology that evaluates that ordering in
queue terms, and the finding that a classification gap between scripts becomes a *waiting-time
gap between customers*.**

That last clause is the thesis. It is what makes this a use-case paper rather than a
leaderboard entry:

> **Fairness in triage is a scheduling property, not a classification property.**
> A 3-point macro-F1 deficit on romanized Tamil is an abstraction. The same deficit expressed
> as *"Tanglish-writing customers with urgent problems wait N minutes longer than English-writing
> customers with the same problem"* is a finding an operations owner can act on, and it is
> measurable with what we already have.

---

## 2. The Ticket Urgency Score (TUS)

### 2.1 Definition

For ticket `t` evaluated at decision time `τ`:

```
    U(t, τ)  =  S(t) · (1 + α · a(t, τ))

    S(t)     =  w_P · Ê[sev | t]  +  w_S · P̂(Negative | t)  +  w_I · κ(î(t))

    a(t, τ)  =  (τ − arrival(t)) / D            normalised age, D = the SLA window
```

with `w ≥ 0`, `Σw = 1`, and `α ≥ 0`. Three signals, one aging term, four numbers to fit.

### 2.2 Every term, and why it is that and not something else

**`Ê[sev | t] = Σ_k p̂_k(t) · sev_k`, `sev = (Low 0, Medium ½, High 1)` — the posterior, not
the argmax.**

Taking the argmax of the priority head and mapping it to a tier is what a naive deployment
does, and it discards the one thing the queue needs most: *confidence*. A confidently-Low
ticket and a 0.49/0.51 Low–Medium coin flip both become "Low" and then sit in the same FIFO
tier. The expected severity separates them. This is not a stylistic preference — it is the
Bayes-optimal action under a linear cost, and D3 already found that **priority errors
concentrate exactly on the Low/Medium boundary**, which is precisely the region where the
argmax throws away the most information.

*This gives us a controlled comparison the paper can report:* `argmax-tier + FIFO` versus the
same model's posterior. Same classifier, same weights, different consumption of its output.
Any difference is attributable to the scoring function alone.

**`P̂(Negative | t)` — the sentiment posterior.**

The escalation signal. Reported honestly: at 0.71 Negative-F1 with 0.67 recall this head misses
about a third of genuinely negative tickets, so it is a *nudge* in the ordering, never a gate.
The scoring function is the right place for a weak signal — a weak signal with a small fitted
weight is useful; the same signal as a routing rule is dangerous.

**`κ(î(t))` — per-intent criticality, derived and not hand-written.**

```
    κ(i) = P̂(priority = High | intent = i),  estimated on train+dev only
```

77 numbers, all estimated from data the test set never sees. Two reasons this earns its place
rather than being a third redundant severity estimate:

1. It is a **prior that backstops the priority head when the text is degraded.** `card_lost`
   is urgent whether or not the model parsed the sentence — and the tracks where the model
   parses worst are exactly the romanized ones. This is the term with the best chance of
   closing the fairness gap, which makes its weight one of the paper's more interesting
   fitted quantities.
2. The intent labels are **BANKING77 human gold**, the only human ground truth in the corpus.
   Routing intent through the score is the one place a human-labelled signal enters the
   ordering.

**`(1 + α · a)` — multiplicative aging, not additive.**

Additive aging (`S + α·a`) lets any sufficiently stale ticket overtake any fresh one, including
a fresh High, as soon as `α·a > 1`. Multiplicative aging *amplifies* whatever urgency a ticket
already had, so a stale Low climbs but climbs more slowly than a stale High. `α` is then an
explicit, tunable statement of the starvation/urgency trade-off rather than an accident of
units, and `α = 0` recovers a pure static-priority queue as a nested special case.

### 2.3 The redundancy problem, stated up front

`w_S · P̂(Negative)` and `w_I · κ(î)` are **not independent signals.** The project already
measured this: a predictor given only the intent label and no text at all reaches roughly half
the best text model's Negative-F1 (`negative_is_topic.py`). "Negative" in this corpus behaves
closer to a topic construct than to customer tone.

Two consequences, and both are handled rather than hidden:

1. **The weights must be fitted jointly, never set by intuition.** With correlated features,
   intuition double-counts — and a hand-set weight vector is the single most attackable thing
   in a scoring-function paper.
2. **The ablation is a deployment recommendation, whichever way it lands.** If dropping the
   sentiment term costs nothing once intent is in the score, the recommendation is: *do not
   serve a second 1.9 GB encoder in production.* If it costs something, we have quantified what
   the second model buys. Either result is worth the page.

### 2.4 Fitting the weights

Constrain to the simplex (`w ≥ 0`, `Σw = 1`) so the weights are identifiable and readable as
proportions of the score. Fit by **direct grid search on dev at step 0.05** — 231 points on a
3-simplex, times a small `α` grid. The objective is a simulation, so it is non-differentiable
and noisy; a grid is honest, cheap, and gives us the whole surface for free.

**Fitted on dev, scored once on test.** The same discipline as everything else in this project.

Publish the **full simplex surface**, not just the argmin. If the objective is flat across a
wide region — which is a real possibility with correlated signals — then the exact weights are
not the finding and pretending otherwise would be overclaiming. A flat surface is itself a
result: *the ordering is robust to how you weigh these signals.*

---

## 3. Evaluation methodology

Five layers, cheapest first. Layers 1–2 are the core; 3 is the headline; 4–5 are what a
reviewer will ask for.

### Layer 1 — Ranking quality (deterministic, no simulation)

Order the 3,079 test tickets by `S(t)` alone (α is irrelevant with no time axis) and compare
against the gold ordering.

| metric | what it answers |
|---|---|
| Kendall's τ_b vs the gold-severity order | Is the overall ordering right? |
| nDCG@k, gain = gold severity, k ∈ {10, 50, 100} | Is the *top* of the queue right? |
| **Precision@k for gold-High** | Of the next 100 tickets the system surfaces, how many really are urgent? |

Precision@100 is the number to lead with in the paper. It is the only one of the three an
operations owner can read without a statistics background, and it is directly actionable: it
is the hit rate of a shift's worth of work.

### Layer 2 — Discrete-event queue simulation

Where the claim is actually earned.

| component | choice | why / assumption |
|---|---|---|
| arrivals | Poisson(λ), tickets sampled without replacement from test | standard, memoryless; **an assumption, not measured** |
| service | `m` parallel agents, LogNormal service time, stated mean | right-skewed like real handling times |
| load | ρ = λ·E[S]/m swept over **{0.70, 0.85, 0.95}** | see below — this sweep is mandatory |
| replication | ≥ 200 seeds, report mean and bootstrap CI | one simulation run is an anecdote |

**Policies compared:**

1. `random` — floor
2. `FIFO` — the industry default and the honest baseline
3. `argmax-tier + FIFO within tier` — what a naive deployment of our own classifier does
4. **`TUS`** — the proposed system
5. `oracle-TUS` — the same score computed from **gold** labels: the ceiling this scoring
   function reaches if the classifiers were perfect

**Metrics:** mean and p95 time-to-first-response for gold-High · SLA breach rate at a stated
target · weighted tardiness `Σ w_c · max(0, C_j − d_j)` · **p95 wait for gold-Low** (the
starvation check, without which any priority scheme looks good).

**Two methodological commitments:**

**(a) The load sweep is not optional.** At ρ = 0.5 no queue forms and every policy scores
identically, because ordering only matters when there is something to order. Reporting a single
load would let us pick the one that flatters the system. Sweeping it states plainly where the
gains live and where they vanish — and "this buys you nothing below 70% utilisation" is a
useful, publishable sentence.

**(b) Report TUS as a fraction of the oracle's improvement over FIFO.**

```
    attainment  =  (FIFO − TUS) / (FIFO − oracle)
```

This separates *"the scoring function is well designed"* from *"the classifiers are accurate"*,
which are different claims with different remedies. A high attainment with a modest absolute
gain means the scoring function is doing its job and the classifiers are the bottleneck — which
is, given the label-ceiling result, the outcome to expect.

### Layer 3 — The fairness result (the headline)

Run the same simulation with a **language-mixed arrival stream**, and report time-to-first-response
**broken down by the language the customer wrote in**.

The classification finding is already established (`results.md` §16): the encoder's advantage
over TF-IDF is significant on native script and indistinguishable from zero on both romanized
tracks; difference-in-differences sinhala−singlish = +0.0698, CI [+0.0140, +0.1283], p = 0.012.

This layer converts that into **minutes of extra wait for a customer with an equally urgent
problem, who happens to type in Latin script**. Same ticket, same gold priority, different
rendering, measurably worse service.

Test it properly: bootstrap over simulation seeds, and compare against a **gold-label control**
in which the same arrival stream is ordered by gold priority — where the per-language gap is
zero by construction. Any gap in the predicted condition that is absent from the control is
attributable to the model, not to the arrival process.

This is the single most quotable result the project can produce, and it costs no GPU time.

### Layer 4 — Calibration

The score consumes probabilities, so calibration is load-bearing in a way it never was for the
F1 tables. Two things are already known and both point here: the sentiment model is documented
as uncalibrated, and a CV-tuned threshold failed to transfer from dev to test (−0.005).

- Expected Calibration Error **per language track**, on dev
- Temperature scaling, fitted on dev, re-run through Layers 1–3

**The hypothesis worth testing:** if the romanized tracks are systematically *less confident*
as well as less accurate, then the uncalibrated score **under-prioritises them twice over** —
once for the errors, and again because their correct predictions carry lower probability mass
into `Ê[sev]`. If that holds, temperature scaling is a near-free fairness intervention, and
that is a genuinely useful finding for anyone deploying a multilingual triage stack.

### Layer 5 — Ablation and sensitivity

- **Signal ablation:** priority only · +sentiment · +intent · full. Answers whether the
  multi-task pipeline earns its serving cost. Ties directly to §2.3.
- **α sweep:** the urgency/starvation frontier, plotted as p95-High against p95-Low. A frontier
  is the right object here, not a single operating point — the choice along it is the desk's,
  not ours.
- **Weight sensitivity:** the dev simplex surface, and whether the dev argmin transfers to test.
- **Classifier substitution:** the same scoring function fed by TF-IDF instead of LaBSE.
  Isolates how much of the queue improvement is the encoder and how much is the scoring
  function — and given §16, we should expect the answer to *differ by script*.

---

## 4. Research methodology, stated for the paper's Methods section

**Design.** Quantitative computational study in two coupled parts: (i) a controlled supervised
learning experiment on a frozen split, and (ii) a discrete-event simulation study that consumes
(i)'s outputs as its input distribution. Part (i) establishes what the models know; part (ii)
establishes what that knowledge is worth to a queue.

**Unit of analysis.** The *ticket* (`id`), not the row. Every ticket exists five times, once per
language track. The split is drawn on `id` and fanned out — drawing it on rows would put a
ticket's English copy in train and its Sinhala copy in test and turn every subsequent number
into memorisation. This also makes the fairness comparison in Layer 3 a genuinely paired
design: the same ticket, the same gold label, five renderings.

**Controls.** One frozen split (`e7b5934392cd`) · one label version (v8, final) · identical
budget across models · dev for all selection, test scored once · every run record stamped with
split sha, label version, seed, epoch-selection rule.

**Inference.** Paired bootstrap (1,000 resamples) for metric differences; exact McNemar for
paired classifiers; difference-in-differences for the script contrast, resampling ticket ids
once so all four cells move together. Simulation results bootstrapped over seeds. We do **not**
compare two p-values to each other — the difference between significant and non-significant is
not itself significant (Gelman & Stern).

**Ceilings, reported alongside every score.** Sentiment and priority labels are LLM-generated
and benchmarked against human annotation: 0.7931 negative-F1 and 0.7722 macro-F1 respectively.
A model at 0.7138 is at 90% of its ceiling, not at 71% of possible. Reporting the raw score
without the ceiling misstates where the remaining headroom is — and in this project it is in
the labels, not the models.

**Threats to validity, and what is done about each.**

| threat | mitigation |
|---|---|
| Simulation parameters (λ, service distribution, m) are assumed, not measured from a real desk | Sweep the load; report attainment normalised to oracle, which is invariant to much of it; state the assumption in the caption, not a footnote |
| Romanized tracks are synthetic (rule-generated / machine-translated), so cleaner than human typing | Already documented; the fairness gap is therefore an **optimistic lower bound** — real code-mixed input should widen it. Say so. |
| Sentiment/priority labels are LLM-generated | Ceiling reported everywhere; IAA study (track C) bounds the label noise |
| Weights fitted and evaluated on the same data | Fitted on dev, scored once on test; the dev→test transfer is reported as a result, not assumed |
| Single seed for the classifiers | Seed-variance study (A6) |
| The scoring function could be tuned to flatter itself | Publish the full simplex surface and the α frontier, not just the chosen point |

**What would strengthen it most, in order.** (1) Any real published helpdesk arrival/service
statistics, so the simulation is parameterised from literature rather than assumption — a
literature task, not an experiment. (2) The IAA study, which converts "agreement with one
annotator" into a defensible reliability bound. (3) Human-typed romanized text, which would
turn the fairness lower bound into a measurement.

---

## 5. Where this leaves the paper

| | contribution | evidence |
|---|---|---|
| **C1** | A five-track multilingual ticket-triage corpus with a frozen split and a measured label ceiling | done |
| **C2** | Multilingual pretraining transfers across *languages* it has seen, not across *scripts* it has not — with the tokenizer mechanism identified (`[UNK]`, not fertility) | done (§16, MuRIL) |
| **C3** | **A ticket-ordering system that consumes classifier posteriors, and a queue-level methodology for evaluating triage** | track E |
| **C4** | **Script-based service disparity: the classification gap in C2, expressed as waiting time** | track E, Layer 3 |

C1 and C2 are the NLP track. C3 and C4 are the use-case track, and C4 is the one that ties them
together — the paper's argument is that you cannot see the cost of C2 until you build C3.

---

## 6. What changed once it was built

The plan above is kept as written. This section records where reality diverged from it,
because two of the divergences are findings and two were defects in the design.

**Layer 4's hypothesis was refuted, and the refutation is more interesting.** §3 Layer 4
predicted that the romanized tracks would be both less accurate and less confident, so
that an uncalibrated score penalises them twice and temperature scaling is a near-free
fairness intervention. The first half is exactly right — LaBSE's priority ECE is 0.0658
pooled and **0.1071 on tamilish**, its worst track, against TF-IDF's 0.0180 / 0.0235.
The intervention is not. Temperature scaling fixed the calibration and made the queue
**worse** on every metric. ECE measures agreement between top-1 confidence and accuracy;
a queue needs posteriors that *separate* tickets, and softening the distribution costs
discrimination everywhere in order to rescue confident errors it cannot identify. See
`results.md` §17.6.

**Layer 3's headline turned out to be a fix, not just a diagnosis.** The plan expected to
report that a script-level accuracy gap becomes a waiting-time gap. It does — **+6.99 min
for a Tanglish customer under the naive argmax deployment** — but the scoring function
removes about 85% of it, leaving a residual that still excludes zero. Diagnosis, mechanism,
fix and residual is a stronger contribution than diagnosis alone.

**The oracle in §3 Layer 2 was not an upper bound.** As specified it used "the same three
signals the system uses" from gold labels, so a gold-Low with negative sentiment could
outrank a gold-High and TUS beat the oracle at some loads. Redefined as gold tier with
FIFO within tier, which is a genuine bound on High waiting time and makes `tier` vs
`oracle` a clean predicted-vs-gold contrast.

**The fitting objective in §2.4 selected a degenerate system.** Absolute tardiness weighted
by severity handed the objective to the 55% Low majority; the argmin was intent criticality
alone. Replaced with relative tardiness, `max(0, wait − d)/d`. Full account in
`results.md` §17.7.

**One thing the plan called correctly and one it under-called.** §2.3's warning that the
sentiment and intent terms are correlated held up — the fitted weights put 0.80 on priority
and split 0.20 between the other two, and the ablation shows sentiment adding little. What
the plan did not anticipate is §17.3: **the argmax-tier policy has the highest Kendall τ of
any system and the worst queue head.** Layer 1 was written as a cheap warm-up for Layer 2
and it produced the sharpest argument for why Layer 2 has to exist at all.
