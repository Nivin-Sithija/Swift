# Model card — `sentiment_labse`

Swift ticket-sentiment classifier for Sinhala, Tamil and English banking support tickets,
including romanized code-mixed input.

Generated 2026-09-08 from `ml/models/encoders/sentiment_labse/` and the run record
`sentiment__labse__…__ev-all__arm-class-weight__test.json`.

---

## Model details

| | |
|---|---|
| Base model | `sentence-transformers/LaBSE` |
| Task | Binary sentiment on support tickets — `Neutral` / `Negative` |
| Label order | `["Neutral", "Negative"]` (index 1 is the positive class for all reported metrics) |
| Adaptation | Full fine-tune, no LoRA |
| Class balancing | `class_weight` (inverse frequency); `none` and `ros` were also run and lost |
| Learning rate | 2e-5 |
| Batch size / max length | 32 / 128 tokens |
| Epochs | 3, reporting the **final** epoch (not the best — see *Epoch selection*) |
| Precision | fp16 on a single T4 |
| Training rows | 49,990 (`train` + `dev`, all five language tracks pooled) |
| Training time | 1,319 s |
| Seed | 42 |
| Split | frozen, sha `e7b5934392cd` |
| Size on disk | 1.88 GB (`model.safetensors`, plus tokenizer) |

## Intended use

Routing and prioritisation of inbound customer support tickets in a Sri Lankan banking /
fintech setting, where the same customer base writes in Sinhala, Tamil and English, and in
romanized ("Singlish" / "Tanglish") transliterations of the first two.

**Intended as a triage aid, not an adjudicator.** The `Negative` label as constructed here is
substantially a *topic* signal rather than a tone signal — an intent-label-only predictor with
no access to the text at all reaches 0.3301 Negative-F1, **49.6% of this model's score**. Read
a `Negative` prediction as "this ticket is about a class of problem that tends to be serious",
not as "this customer is angry".

## Out-of-scope use

- **Any decision affecting a customer taken without a human in the loop.** Precision is 0.76:
  roughly one in four `Negative` flags is wrong.
- **Non-banking domains.** Training text is BANKING77-derived; the 77 intents are banking
  operations and the vocabulary is narrow.
- **Languages or scripts outside the five tracks.** In particular the model has no exposure to
  Sinhala or Tamil written in scripts other than the two seen here.
- **Inferring customer emotion, satisfaction, or intent to churn.** See *Intended use*.

## Evaluation

Held-out test set, 15,395 rows (3,079 tickets × 5 language tracks), scored once. Fitted on
`train`+`dev`, so no tuning decision saw these rows.

**Headline: Negative-F1 = 0.7138** (precision 0.7601, recall 0.6728).
Accuracy 0.9658 and macro-F1 0.8478 are reported for completeness only — accuracy is not
meaningful here, since ~94% of tickets are `Neutral` and a majority-class predictor scores
above 0.93.

### By language track

| track | script | Negative-F1 |
|---|---|---:|
| english | Latin (native) | 0.8032 |
| tamil | Tamil | 0.7606 |
| sinhala | Sinhala | 0.7234 |
| singlish | romanized Sinhala | 0.6757 |
| tamilish | romanized Tamil | **0.5948** |

**Performance is not uniform, and the gap is large.** Every track is significantly below
English (paired bootstrap, same 3,079 tickets, all CIs clear of zero). Romanized Tamil is
20.8 points below English. Anyone deploying this should expect materially worse service for
customers writing in transliteration than for customers writing in English — which, in this
setting, likely correlates with who those customers are.

### Against alternatives

| system | Negative-F1 |
|---|---:|
| this model | **0.7138** |
| TF-IDF + linear SVM | 0.6653 |
| intent label only, no text | 0.3301 |
| **label ceiling** (shipped labels vs human gold) | **0.7931** |

The advantage over the classical baseline is +0.0485 (95% CI [+0.0257, +0.0721], p < 0.0001)
— but it is **confined to native-script tracks**. On romanized Sinhala the gain is +0.0124
(p = 0.712) and on romanized Tamil +0.0225 (p = 0.490): both indistinguishable from zero. If
your traffic is predominantly romanized, this model is not measurably better than TF-IDF and
costs 1.88 GB and a GPU to serve.

## Limitations

**The ceiling, not the model, is the binding constraint.** Agreement between the shipped
labels and a human annotator is 0.7931 Negative-F1. This model reaches 90.0% of that. Further
modelling effort is likely to be wasted relative to effort spent on label quality.

**That ceiling rests on one annotator and 31 gold Negatives**, with a 95% CI of
[0.6667, 0.8956]. It is the weakest link in every claim above. A two-annotator study is
outstanding.

**Labels are LLM-generated, not human-authored.** Sentiment and priority were produced by a
prompt pipeline and then partially revised; only a 500-row benchmark subset has human labels.

**Translation provenance is uneven.** The Sinhala track's own text is 40.35% Latin characters
(realistic code-mixing); the Tamil track's is 1.26%. The two are not equivalent in how they
were produced, and the Tamil track is documented as having had no manual pass.

## Ethical considerations

- **Differential service quality by language** is the primary risk, and it is measured above
  rather than hypothetical. A 20.8-point spread across tracks in a customer-facing triage
  system means unequal treatment along a line that tracks language community.
- **The `Negative` class encodes topic**, so the model will flag fraud- and loss-related
  tickets regardless of tone. That is arguably the desired behaviour for triage, but it means
  the output must not be presented to staff as a read on the customer's mood.
- **No PII was introduced.** The corpus derives from BANKING77 plus generated multilingual
  variants; it contains no real customer records.

## Reproducing

```
python ml/kaggle/runner.py run --job train_encoders_b --models labse \
    --task sentiment --epochs 3 --fit-portion "train+dev" \
    --eval-portion test --save-models
```

Training is deterministic to the bit at a fixed seed: this exact configuration was run twice,
nineteen days apart on different hardware, and produced headline values identical to 17
significant figures.

## Epoch selection

The record is stamped `epoch_selection: final-epoch`. Earlier versions of the training loop
selected the best epoch by scoring the evaluation set, which on a test run is selection on
test. For this cell the argmax epoch was the final epoch (3 of 3), so the two are the same
number — confirmed by the re-run above. Any future run must use the patched path, which
reports the final epoch on test regardless.
