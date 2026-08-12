# ml/ — the classifier bake-off

Everything that trains or evaluates a model lives here. Three people run
experiments from this directory on different machines; the layout exists so
their results merge without anybody coordinating.

```text
ml/
  swiftbench/     importable harness — splits, metrics, baselines, result format
  kaggle/         run jobs on Kaggle's T4 GPUs from this repo (see kaggle/README.md)
  scripts/        standalone CLI training runs (intent)
  configs/        recorded experiment configs
  splits/         split_manifest.json — the frozen train/dev/test split
  models/         saved .joblib pipelines
  predictions/    per-run test prediction CSVs
  reports/        metrics, summaries, and reports/runs/*.json (one file per run)
```

`swiftbench` gained three modules after the first test-set evaluation:

| module | why |
|---|---|
| `tokenize.py` | scikit-learn's default `token_pattern` discarded **40% of Sinhala and 69% of Tamil characters**. Word tokenization now goes through `indic-nlp-library`, dispatched on script. |
| `train_encoder.py` | the mirror of `train_classical` for fine-tuning encoders; fp16 on CUDA, fp32 on MPS |
| `config.SWIFT_REPO_ROOT` | env override so the package can be imported from `/kaggle/input` |
| `probe.py` | linear probing — freeze the backbone, extract pooled vectors once, fit a logistic regression. Measures how much task signal pretraining already carried, i.e. how much fine-tuning actually added. Driven from `17_encoder_linear_probe.ipynb`. |

`probe.py` caches pooled vectors under `ml/cache/embeddings/` (gitignored, ~2 GB for the full
roster, regenerable in one forward pass). Every `.npz` carries the `id` array and split sha it was
built from, and `probe.features()` asserts both against the frame it is used with — a stale cache
would match labels to the wrong rows and leave every metric downstream looking plausible.

Notebooks that drive the harness are in [`../notebooks/modeling/`](../notebooks/modeling/).
**Experiments are run in notebooks, not scripts** — you want to watch a sweep
progress and inspect the errors, not read a log after the fact.

---

## Start here

```python
import sys; sys.path.insert(0, "path/to/repo/ml")
import swiftbench as sb

sb.train_classical.run(task="sentiment", model="tfidf-svm",
                       train_langs=["sinhala"], eval_lang="sinhala",
                       arm="ros", author="yourname")
```

Run [`../notebooks/modeling/00_setup_checks.ipynb`](../notebooks/modeling/00_setup_checks.ipynb)
first on any new machine. If it fails, stop — every result downstream of a
broken invariant is meaningless.

## The three rules

**1. The split is drawn on `id`, once, and fanned out to all five languages.**

The same ticket exists five times — once per language — under one `id`. Splitting
rows independently puts the English copy of a ticket in train and its Sinhala
copy in dev, and every score after that is measuring memorisation. `swiftbench`
splits on `id` and never on rows.

Current manifest: `splits/split_manifest.json`, **8,500 train / 1,498 dev /
3,079 test**. Test is the official BANKING77 test file, untouched.

Never regenerate it. Every result file stamps the split sha and
`results.load_all()` drops rows whose sha doesn't match, so a stale result can't
silently enter a comparison table.

**2. Model selection happens on dev. Test is touched once, at the end, by
winners only.**

`portion="dev"` is the default everywhere. You have to ask for `test`
explicitly.

**3. Sentiment is scored on Negative-class F1. Never accuracy.**

95.5% of tickets are Neutral. See the table below for why that matters.

## Measured floors — read every result against these

Dev, split sha `e7b5934392cd`.

| task | floor | number |
|---|---|---|
| sentiment | always answer `Neutral` | accuracy **0.9546**, negative-F1 **0.000** |
| priority | always answer `Low` | macro-F1 **0.2302** |
| priority | `intent-chained` — predicted intent → majority-priority lookup | macro-F1 **0.892–0.904** |
| priority | `intent-lookup` on **gold** intent | macro-F1 **0.9147** — an **oracle**, not a target |

The priority distinction is the one that trips people up. A lookup from intent
to its most common priority is very strong, but the version that uses the *gold*
intent is not servable — at inference nobody hands you the gold intent. The
honest bar is `intent-chained`, which runs the real intent classifier first and
inherits its errors. Quoting the oracle as the target sets an impossible gate.

## Class balancing: three arms, and never a fourth

`none`, `class_weight`, `ros` (random oversampling, training rows only, after
the split).

**No SMOTE arm.** Three papers in [`../research/`](../research/) find plain
oversampling matches or beats it on code-mixed low-resource text, and
interpolating between the TF-IDF vectors of two unrelated tickets does not
produce a sentence any customer would write. Don't add one.

## Recording results

`results.save()` writes one JSON per run to `reports/runs/`, filename derived
from run identity (`task__model__tr-langs__ev-lang__arm__portion.json`). Two
people running the same configuration overwrite rather than duplicate; two
people running different configurations never collide in git. Pass `author=` so
runs stay attributable.

`results.leaderboard(task)` collates them.

## Don't edit `swiftbench/config.py` for one run

It's frozen shared state — paths and the numbers that have to be identical
across everybody's runs for results to be comparable. If you need a different
value, pass it as an argument.

---

## Standalone scripts (intent only)

`scripts/` predates the harness and covers 77-way intent classification only.
All paths are anchored on `__file__`, so they run from any working directory.

```bash
python ml/scripts/train_baseline.py --language tamilish --model linear_svm
python ml/scripts/run_all_baselines.py          # 12-run matrix
python ml/scripts/validate_baseline_suite.py    # 15-section validation
python ml/scripts/train_transformer.py --smoke-test
```

**Two caveats before you trust their numbers**, both of which the harness
avoids:

- `train_baseline.py` fits on train and evaluates **directly on the official
  test set** — there is no dev split in it. Every number in
  `reports/baseline_summary.csv`, and therefore every promotion threshold in
  `reports/promotion_thresholds.csv` and `configs/xlm_roberta_all_01.json`, is a
  test-set number. The gate the transformer must clear was read off the same set
  it will be judged on.
- `train_transformer.py` builds its validation split with `train_test_split`
  over the pooled five-language rows. Because one ticket is five rows sharing an
  `id`, a ticket's English copy can land in train while its Sinhala copy lands
  in validation. That inflates validation macro-F1, and `--language all` is the
  flagship config.

Both scripts also read the label via `r.get("category", r.get("label", ""))`.
The column is `category` and is staying that way, so this works — but the
fallback means any future schema change returns `""` for every row and training
proceeds on empty labels instead of raising. `swiftbench` maps the column in one
place (`config.TASK_LABEL_COLUMN`) and raises on a schema mismatch.

Note the naming: **`category` is the column, `intent` is the task.** `swiftbench`
is called with `task="intent"` and resolves it to the `category` column.
