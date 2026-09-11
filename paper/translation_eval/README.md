# Translation comparison — how to run it, and what it can and cannot conclude

## What you paste

Four files in `samples/`, each self-contained and ready to paste whole:

| file | give to |
|---|---|
| `prompt_openai_sinhala.md` | the OpenAI model |
| `prompt_openai_tamil.md` | the OpenAI model |
| `prompt_gptoss_sinhala.md` | local GPT-OSS |
| `prompt_gptoss_tamil.md` | local GPT-OSS |

Each holds the instructions plus all 150 English rows. **None of them contains our Sinhala
or Tamil** — verified, 0 Sinhala characters in the Sinhala prompt. If the model saw our
translation it would anchor to it and the comparison would be worthless.

Save what comes back **verbatim** as:

```
systems/openai_sinhala.csv     systems/openai_tamil.csv
systems/gptoss_sinhala.csv     systems/gptoss_tamil.csv
systems/google_sinhala.csv     systems/google_tamil.csv
```

Two columns, `id,translation`. Then run the validator — silent row loss is the normal
failure mode of pasting 150 rows through a chat window:

```bash
.venv312/bin/python paper/experiments/validate_translations.py
```

**Record the exact model name and the date** for each system. The paper has to name them.

## Google Translate

`paper/experiments/fetch_google_translations.py` will produce the two Google files if you
have a Cloud Translation key (`GOOGLE_TRANSLATE_API_KEY` in `backend/.env`). Without a key,
paste through the web UI in batches and save in the same format.

---

## What this study can conclude — read before running it

**It cannot be set up to conclude that our corpus is best.** Not because the answer is
unfavourable — it may well be favourable — but because a comparison whose conclusion is
fixed in advance is not evidence, and the one thing this paper has going for it is that its
numbers survive being checked.

There is also a mechanical trap worth naming, because it is the obvious way to get the
"right" answer by accident:

> **Never score the systems against our own translation as the reference.** chrF or BLEU
> with `swift_sinhala` as the reference measures *similarity to us*, so we score 1.0 and
> everyone else is penalised for every legitimate paraphrase. That is not a finding, it is
> the definition of the metric. Anyone reviewing the paper will spot it immediately.

So the evaluation is **reference-free**, all three systems judged on identical terms:

| method | what it measures |
|---|---|
| COMET-Kiwi QE | adequacy without a reference |
| LaBSE source–translation cosine | meaning preservation |
| Blind human ratings | adequacy + fluency + forced ranking, systems unlabelled and shuffled |

## Where our corpus has a real chance of winning — and it is not adequacy

Be clear-eyed about the likely shape of the result:

- **Raw adequacy and fluency: a frontier model may well beat us.** Our Sinhala and Tamil are
  machine-translated and unaudited at scale (dataset known issue 4), and we have just found
  that the tamilish *test* rendering was produced by a different process from its train
  rendering (§18.2). Expecting to win on adequacy is optimistic.
- **Register and code-mixing: this is where we plausibly win, and it is measurable.** The
  corpus was built to keep English banking loanwords in English — *card*, *account*, *PIN*,
  *ATM*, *top-up* — because that is what Sri Lankan bank customers actually type. Generic MT
  systems, Google especially, tend to produce formal literary Sinhala and nativise those
  loanwords into words nobody says out loud.

That gives a **specific, falsifiable, countable** claim: loanword-retention rate and
register markers, measured identically across all three systems. If our corpus retains
code-mixed loanwords at a materially higher rate, then it is the better *fit for this
domain* even where a frontier model produces cleaner prose — and "better fit for the
domain" is a stronger and more interesting claim for a Sri Lankan banking paper than
"higher COMET score".

It is also a claim that can lose. If Google retains loanwords as well as we do, we say so.

## If we lose

That is a publishable result too, and it costs nothing to say: it motivates a v1.1
retranslation, and combined with §18.2 it is the honest version of a corpus paper —
*here is the resource, here is where it is weak, here is what we are doing about it.*
Reviewers trust a paper that reports a defect in its own resource far more than one that
does not have any.
