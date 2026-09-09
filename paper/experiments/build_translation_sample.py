"""Draw the shared evaluation sample for the translation-quality comparison.

The claim to be supported
-------------------------
"Swift's Sinhala and Tamil translations are more accurate than off-the-shelf MT."

The trap this script is designed around
---------------------------------------
The obvious experiment -- score Google/GPT-OSS/OpenAI output against Swift's
translation with BLEU or chrF -- is **circular**. Using our own output as the
reference measures similarity to us, not quality, and guarantees we win by
construction. A reviewer spots that immediately and the whole corpus section
loses credibility.

So the sample is built for three evaluations that do not need our text as a
reference:

  1. **Blind human adequacy + fluency** (primary evidence). Raters see the
     English source and four unlabelled candidates in shuffled order.
  2. **Reference-free automatic QE** -- COMET-Kiwi scores source-vs-translation
     with no reference at all.
  3. **Cross-lingual embedding similarity** -- LaBSE cosine between the English
     source and each candidate. Cheap, and LaBSE already covers both scripts.

Outputs
-------
paper/translation_eval/samples/
    sample_ids.csv          the drawn ids, with English source and intent
    prompt_openai.md        the exact prompt to paste, with the rows inline
    prompt_gptoss.md        same prompt, local-model wording
    template_response.csv   the shape returned files must have

Run:
    .venv312/bin/python paper/experiments/build_translation_sample.py
    .venv312/bin/python paper/experiments/build_translation_sample.py --n 200
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, data, splits  # noqa: E402

OUT = REPO / "paper" / "translation_eval" / "samples"

# Sinhala and Tamil only. Singlish and Tanglish are romanisation, not
# translation -- Google Translate does not emit them and the comparison would be
# a category error. Romanisation quality is a separate study.
PAIRS = {"sinhala": "Sinhala (si)", "tamil": "Tamil (ta)"}

PROMPT_HEADER = """\
You are translating customer-support tickets for a **Sri Lankan retail bank**
from English into {target}.

Rules:
1. Translate the *meaning*, not word by word. These are things a real customer
   would type to their bank.
2. Use natural, colloquial {short} as actually written by Sri Lankan bank
   customers -- not formal/literary register, and not Indian {short}.
3. **Keep English banking loanwords in English** where a Sri Lankan speaker
   would naturally use them (card, account, PIN, transfer, ATM, top-up).
   Do not force a native coinage that nobody says out loud.
4. Preserve the customer's tone. If the source sounds frustrated, the
   translation should sound frustrated.
5. Do not add, drop, explain or soften anything. No notes, no alternatives.

Return **only** a CSV with exactly two columns and this header row:

id,translation

One row per input line, ids unchanged, in the same order. Quote any field that
contains a comma. Do not wrap the output in a code fence or add commentary.

Here are the {n} rows to translate:

id,text_en
"""


def draw(n: int, seed: int) -> pd.DataFrame:
    """Stratified draw over the 77 intents, from the test split.

    Test rather than train: the sample is then disjoint from everything used to
    select a model, so nothing here can leak into a modelling claim later.
    """
    english = splits.get(["english"], "test")[["id", "text_en", "text", "category"]]

    # Proportional stratification with at least one row per intent, so all 77
    # intents appear and the sample cannot be accused of cherry-picking easy ones.
    per = max(1, n // english["category"].nunique())
    # Index-based selection rather than groupby().apply(): apply with
    # include_groups=False drops the grouping column, which silently produced a
    # sample covering 47 of 77 intents instead of all 77.
    picks = [
        g.sample(min(per, len(g)), random_state=seed).index
        for _, g in english.groupby("category", sort=False)
    ]
    out = english.loc[[i for idx in picks for i in idx]].reset_index(drop=True)
    if len(out) < n:
        remainder = english[~english["id"].isin(out["id"])]
        out = pd.concat(
            [out, remainder.sample(n - len(out), random_state=seed)], ignore_index=True
        )
    return out.sample(frac=1.0, random_state=seed).head(n).sort_values("id").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150,
                    help="segments per language pair; 150 is the usual floor for "
                         "a human-eval claim, 100 the minimum defensible one")
    ap.add_argument("--seed", type=int, default=config.RANDOM_STATE)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    sample = draw(args.n, args.seed)

    # Attach Swift's existing translation for each target language: this is
    # system A, and it is what the other systems are compared *against a human*
    # with -- never scored against as a reference.
    for lang in PAIRS:
        track = data.load_language(lang, "test")[["id", "text"]]
        sample = sample.merge(
            track.rename(columns={"text": f"swift_{lang}"}), on="id", how="left"
        )

    sample_path = OUT / "sample_ids.csv"
    sample.to_csv(sample_path, index=False)

    for lang, target in PAIRS.items():
        short = target.split(" (")[0]
        rows = "\n".join(
            f'{r.id},"{r.text_en.replace(chr(34), chr(39))}"'
            for r in sample.itertuples()
        )
        body = PROMPT_HEADER.format(target=target, short=short, n=len(sample)) + rows + "\n"

        (OUT / f"prompt_openai_{lang}.md").write_text(body)
        (OUT / f"prompt_gptoss_{lang}.md").write_text(body)

    pd.DataFrame({"id": sample["id"], "translation": ""}).to_csv(
        OUT / "template_response.csv", index=False
    )

    print(f"sample: {len(sample)} rows, {sample['category'].nunique()} of 77 intents")
    print(f"drawn from: test split, sha {splits.sha()}, seed {args.seed}")
    print(f"written to: {OUT.relative_to(REPO)}/")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}")
    print("\nNext: paste each prompt_*.md into the corresponding system, save the")
    print("returned CSV as paper/translation_eval/systems/<system>_<lang>.csv")


if __name__ == "__main__":
    main()
