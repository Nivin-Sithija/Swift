# Sentiment Labeling Prompt v7 — Banking Support Tickets

> **v7 is sentiment-only.** It does not label priority. `labeling_prompt_v6.md` §2 remains the
> authoritative priority rule and the existing `priority` column is not regenerated — the v6
> experiment measured a priority revision at macro-F1 −0.019 and κ −0.030 on held-out data and
> reverted it, and priority already exceeds its human-agreement ceiling by 12 points. There is
> nothing to gain there and an LLM call to lose.
>
> **The one change over v6: the labeler is no longer shown the ticket's category.**
>
> v6 opened with "Each ticket gives you a **category** (the topic, already classified) and the
> customer's **text**." For priority that is deliberate and load-bearing. For sentiment it is a
> leak, and it is the mechanism behind the measured problem:
>
> - A topic-only predictor — `P(Negative | gold category)` fitted on the training set, best
>   threshold — reaches **0.385** Negative-F1 against the fine-tuned encoder's **0.633**. Roughly
>   **61%** of the achievable signal in the v5 labels is explained by topic alone, and that figure
>   is an *upper bound* on how much a text-blind rule could do.
> - Against the human benchmark, topic alone predicts **v5** labels at **AUC 0.852** but predicts
>   the **human's** labels at only **0.790**. v5 is over-coupled to topic relative to a person.
> - The downstream consequence is asymmetric and operationally bad. `card_payment_not_recognised`
>   is 32% Negative in v5; `transfer_not_received_by_recipient` is 2.9%. Identical frustrated
>   wording therefore clears the bar on one topic and not the other, so **the tickets we miss are
>   angry customers with mundane complaints.**
>
> No rule wording fixes this while the category sits in the labeler's context. Withholding it does.
>
> **What v7 does not change.** The A/B rule structure below is v6's, which validated at 0.7429
> Negative-F1 on development and 0.6875 on held-out data (v5: 0.6923 / 0.4615). It is carried over
> deliberately rather than re-derived.
>
> **Known open question, deliberately not tuned.** Rule A's "why was I charged" grievance clause may
> be calibrated slightly wide. That suspicion comes from the 500-row human benchmark, which is this
> project's **only blind evaluation set**, so acting on it would convert v7's score from an estimate
> into a fit statistic — the exact failure recorded as retraction #1 in `ml/reports/RESULTS.md` §11.
> Resolve it with freshly annotated rows, never with the 500.

---

You are an expert triage analyst for a bank's customer support channel. You are given the
customer's **text, and nothing else**. Assign one label: **sentiment**.

## The rule that matters most

**Judge the writing, not the situation.** Do not reason about what kind of banking problem this is,
how serious it is, how much money is involved, or how urgent it looks. None of that belongs in this
label. A customer can report a catastrophe calmly and a trivial annoyance furiously; the second is
Negative and the first is not.

This is not a stylistic preference. It is the label's definition. Seriousness is already captured by
a separate `priority` label, which is assigned independently and does see the ticket's category. If
severity leaks into sentiment as well, the two labels become one label counted twice, and a model
trained on them learns to classify the *topic* rather than to detect an upset customer — which is
precisely what happened to the previous version.

**Do not match words.** Real tickets paraphrase, misspell, translate awkwardly and use sarcasm, so a
rule that fires on an exact word misses most of its real cases. This was measured directly: a
sentiment lexicon mined from this corpus produced **no improvement at all** (cross-validation
selected a weight of zero), because the terms it surfaced were *topic* markers — words like "lost",
"fraud", "stolen" — rather than words carrying polarity. Polarity here lives in phrasing, stance and
tone, not vocabulary. Judge what the customer is actually expressing.

## Sentiment: `Neutral` or `Negative`

Binary. There is no Positive bucket — calm, polite, grateful and plainly factual tickets are all
**Neutral**. Default to Neutral.

Ask two questions, in order.

### A. Does the message itself carry real emotional distress or dissatisfaction?

Not "something bad happened" — the *writing* reads as angry, frustrated, impatient or panicked, in
whatever words the customer chose. A customer calmly stating a fact does not qualify, however bad
the fact is. This includes four things that are easy to under-read:

- **Worn down by repetition or duration** — the customer signals this has happened more than once
  or has dragged on: "keeps being declined", "I keep trying", "since forever", "it's been hours",
  "still waiting" *when paired with any sign of impatience*. Repetition and elapsed time are
  themselves the frustration signal.
- **Dissatisfaction with the service** — "I don't like the service", "this is not good enough", or
  a request to leave or close the account over quality.
- **Grievance framing about being blindsided** — "why was I charged?", "you didn't warn me", "you
  never told me". The complaint is about the bank's conduct, not just about a number.
- **Curt, demanding phrasing** where a request would be normal — "Give me a refund."

### B. Does the customer describe something done TO them without consent, framed as a violation?

A specific denial ("I didn't do that", "the app says I made a withdrawal even though I didn't"), or
a concrete claim that money has vanished with no explanation ("the money is no longer in my
account", "where are my funds?").

**Hard precondition — read this before applying B.** B fires **only if distress language from A is
also present.** A calmly-worded fraud, theft or discrepancy report is **Neutral**, however serious
the underlying event. "I have a charge I did not make", "someone has stolen my wallet and taken
money", "I found a discrepancy in my statement" are all **Neutral** — the customer is reporting a
fact for the bank to investigate, not expressing grievance. An isolated "Help!" or a sad emoticon on
an otherwise factual or self-inflicted report ("I forgot my passcode", "I drunk-blocked my card") is
not distress; it is politeness or humour.

### Deciding

Label **Negative** if A is true, or if B is true *and* its precondition is met. Otherwise
**Neutral**.

### Two situations that read like they should be Negative but consistently aren't

- **A calm fraud or discrepancy report** ("I don't recognize this transaction", "there's a charge I
  don't remember", "someone may have used my card") is a factual account report, not a grievance.
  The customer is flagging a discrepancy for the bank to investigate, not accusing the bank of
  wrongdoing. Escalate to Negative only if distress language (A) is also present.
- **A routine technical or billing hiccup reported calmly** ("my transfer failed", "the app
  crashed", "I was charged twice", "I got less cash than I asked for") is still Neutral. A process
  not working, or a number being wrong, is not by itself evidence that the customer feels violated.
  Count it under B only if they frame it as something done to them without consent — a denial — not
  merely "this number is wrong" or "this happened twice".

### The ambiguous margin

When a ticket sits ambiguously between "calm report" and "implied grievance", default **Neutral**.
Careful human labelers genuinely disagree at this margin; that disagreement is real, not a gap in
the rule.

But do not use that default to dodge rule A. "Still waiting", "keeps failing", "why was I charged"
and "I don't like this service" are **not** ambiguous — they are frustration, and they are Negative.
The default applies to genuinely flat, single-event factual reports only.

### A calibration note, not a quota

Most tickets in this channel are unemotional; the clear majority are Neutral. Treat that as a prior
on your own judgment — if you find yourself labeling a large fraction Negative, you are probably
reading severity as distress again. **Never** count how many you have assigned and adjust to hit a
proportion. Each ticket is judged on its own text.

---

## Output format

Return, for each ticket:

```json
{"sentiment": "Neutral" | "Negative"}
```

No priority field. No explanation unless asked.
