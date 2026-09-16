# Annotation guideline — sentiment and priority on banking support tickets

**Version 1 · 2026-09-08 · read this fully before annotating anything.**

You are labelling customer support tickets sent to a Sri Lankan retail bank. Each
ticket gets two labels: **sentiment** and **priority**. Work through them in the
order given in your file and do not skip ahead to compare with anyone else.

There is no time limit and no target agreement rate. If a ticket is genuinely
ambiguous, use the `notes` column to say why rather than forcing a confident
label — those notes are more useful to us than a clean-looking spreadsheet.

---

## 1. Sentiment — `Neutral` or `Negative`

Two labels only. There is deliberately no `Positive`: these are support tickets,
and a scan of the corpus found no positive ones. If you believe you have found a
genuinely positive ticket, label it `Neutral` and flag it in `notes`.

### What `Negative` means here

**`Negative` = the customer is expressing dissatisfaction, distress, or alarm.**
It is about *how the customer sounds*, not about how serious the underlying
banking problem is.

This distinction is the single most important thing in this guideline, because it
is where annotators most often diverge. A ticket can describe a severe problem in
completely calm language — that is `Neutral`. A ticket can complain bitterly
about a trivial inconvenience — that is `Negative`.

| Ticket | Label | Why |
|---|---|---|
| "There is a transaction on my card I did not make." | `Neutral` | Serious problem, calm report. Severity is priority's job, not sentiment's. |
| "This is the third time I'm asking. Still nothing. Absolutely useless." | `Negative` | Explicit frustration. |
| "My card still hasn't arrived after 3 weeks and nobody replies." | `Negative` | Complaint about the service, not just a status question. |
| "How long does a transfer to another bank take?" | `Neutral` | Plain question. |
| "Why was I charged a fee for this?? I never agreed to any fee." | `Negative` | Challenge plus indignation. |
| "I need to dispute a charge." | `Neutral` | Procedural request, no affect. |

### Signals that support `Negative`

- Explicit emotion words: *frustrated, angry, upset, ridiculous, unacceptable*
- Complaint about the bank's service or responsiveness, not just the product
- Repetition markers: *again, still, third time, as I said before*
- Intensifiers and punctuation used for emphasis: *!!*, *??*, ALL CAPS
- Threats to leave, escalate, or complain to a regulator

### Signals that do **not** by themselves make it `Negative`

- The word *problem*, *issue*, *error*, *failed*, *declined*, *wrong*
- Fraud, theft, or loss being described factually
- Urgency (*I need this today*) without dissatisfaction
- Being long, or containing several questions

> **Known trap.** An earlier automatic labelling pass conflated `Negative` with
> *fraud and loss topics* — it learned to fire on words like "stolen",
> "unauthorised", "lost" regardless of tone. We are measuring whether human
> annotators agree with each other on the *affect* definition above. So when you
> see a calm fraud report, resist the pull toward `Negative`. Label the tone.

---

## 2. Priority — `Low`, `Medium`, or `High`

Priority *is* about the underlying problem, not the tone. Ask: **how much harm
accrues if this ticket is not handled today?**

| Label | Meaning | Typical cases |
|---|---|---|
| `High` | Money or account security is actively at risk; delay causes irreversible loss | Unauthorised transactions, suspected fraud, card stolen, account compromised, funds sent to the wrong recipient and still recoverable |
| `Medium` | The customer is blocked from normal use of their account, but nothing is being lost | Card not working, cannot log in, transfer stuck or pending, payment declined, card not yet delivered past the promised date |
| `Low` | Information, admin, or a request with no time pressure | How-to questions, fee and rate enquiries, limits, eligibility, updating personal details, general policy questions |

### Decision order

Work down this list and stop at the first that applies:

1. Is money at risk right now, or has it already moved without authorisation? → **`High`**
2. Is account security compromised or suspected compromised? → **`High`**
3. Is the customer unable to use their account or complete a transaction? → **`Medium`**
4. Is there a deadline the customer will miss without help? → **`Medium`**
5. Otherwise → **`Low`**

### Edge cases, decided in advance

- **A question *about* fraud** ("what should I do if my card is stolen?") is
  `Low` — it is informational. An actual report of a stolen card is `High`.
- **A declined payment** is `Medium`, not `High`, unless the customer says money
  left the account.
- **A pending transfer** is `Medium`. A transfer sent to the wrong person is
  `High`.
- **Angry tone does not raise priority.** A furious ticket about an interest rate
  is `Negative` sentiment and `Low` priority. This combination is expected and
  correct.
- **Card not yet arrived** is `Medium` if a delivery window has passed and `Low`
  if the customer is just asking when to expect it.

---

## 3. How to work

1. Read the whole ticket before labelling either field.
2. Label **sentiment** first, then **priority**. Do them in that order every
   time — deciding priority first biases sentiment toward severity.
3. Fill `notes` whenever you hesitate, and say what the competing reading was.
4. Do not discuss specific tickets with the other annotator until both files are
   returned. Agreement measured after discussion is not agreement.
5. If a ticket is unreadable, mistranslated, or empty, put `SKIP` in both label
   columns and explain in `notes`.

Return the file with only the `sentiment`, `priority` and `notes` columns filled.
Do not reorder, add or delete rows — row alignment is how the files are compared.

---

## 4. What happens to your labels

Your labels are compared against the other annotator's to produce Cohen's κ and
Krippendorff's α. That number becomes the reliability ceiling for this task in a
research paper: it tells readers how well a model *could* do before label noise
makes further improvement meaningless.

We are not measuring you. Disagreement between two careful annotators is a real
property of the task and is exactly what we are trying to quantify. Please do not
try to guess what the "official" label would be — label what you actually think.
