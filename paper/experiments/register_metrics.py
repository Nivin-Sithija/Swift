"""Register and code-mixing metrics -- the axis a domain corpus can legitimately win on.

The translation study's obvious trap is scoring systems against our own text as a
reference, which makes us win by construction. The honest alternative is to name,
in advance, a property this corpus was *deliberately built to have* and measure it
identically across every system.

That property is **English banking loanword retention**. The corpus prompt told the
translator to keep `card`, `account`, `PIN`, `ATM`, `top-up` in English because that
is what a Sri Lankan bank customer actually types. Generic MT tends to nativise
those into formal coinages nobody says out loud. So:

    retention(system, w) = P(the translation contains w in Latin script
                             | the English source contains w)

Countable, comparable, and **able to lose**. If Google retains loanwords as well as
we do, the number says so.

Two things this metric is not:
  * It is not quality. A system could retain every loanword and mistranslate
    everything around it. Read it beside COMET-Kiwi and the blind ratings.
  * It is not a claim that more retention is always better. It is a claim about
    matching the register of the domain, which is what makes it a *fit* argument
    rather than a *quality* argument.

Run:
    .venv312/bin/python paper/experiments/register_metrics.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EVAL = REPO / "paper" / "translation_eval"
TABLES = REPO / "paper" / "results" / "tables"

# Banking terms a Sri Lankan customer says in English. Chosen from the corpus
# prompt's own instruction, not fitted to the results.
LOANWORDS = [
    "card", "account", "pin", "atm", "top-up", "top up", "app", "balance",
    "statement", "transaction", "transfer", "credit", "debit", "bank", "online",
    "password", "otp", "sms", "branch", "cheque", "loan", "refund", "payment",
    "fee", "rate", "limit", "verify", "exchange", "delivery", "id", "email",
]
SCRIPT_RANGE = {"sinhala": (0x0D80, 0x0DFF), "tamil": (0x0B80, 0x0BFF)}


def latin_fraction(text: str) -> float:
    letters = [c for c in str(text) if c.isalpha()]
    if not letters:
        return 0.0
    return sum(("a" <= c.lower() <= "z") for c in letters) / len(letters)


def retention(sources: pd.Series, targets: pd.Series) -> tuple[float, pd.DataFrame]:
    """Per-loanword retention, plus the micro-average over all opportunities."""
    rows, hits, opps = [], 0, 0
    for w in LOANWORDS:
        pat = re.compile(rf"\b{re.escape(w)}\b", re.I)
        present = sources.astype(str).str.contains(pat, regex=True)
        n = int(present.sum())
        if n == 0:
            continue
        kept = int(targets[present].astype(str).str.contains(pat, regex=True).sum())
        rows.append({"loanword": w, "opportunities": n, "kept": kept,
                     "retention": kept / n})
        hits += kept
        opps += n
    return (hits / opps if opps else float("nan")), pd.DataFrame(rows)


def main() -> None:
    sample = pd.read_csv(EVAL / "samples" / "sample_ids.csv")
    src = sample["text_en"]

    systems: dict[tuple[str, str], pd.Series] = {}
    for lang, col in (("sinhala", "swift_sinhala"), ("tamil", "swift_tamil")):
        systems[("swift (this corpus)", lang)] = sample[col]
    for system in ("openai", "gptoss", "google"):
        for lang in ("sinhala", "tamil"):
            path = EVAL / "systems" / f"{system}_{lang}.csv"
            if not path.exists():
                continue
            got = pd.read_csv(path).set_index("id")["translation"]
            systems[(system, lang)] = sample["id"].map(got)

    rows, detail = [], []
    for (name, lang), target in systems.items():
        micro, per_word = retention(src, target)
        rows.append({"system": name, "language": lang,
                     "loanword_retention": micro,
                     "latin_char_fraction": float(target.map(latin_fraction).mean()),
                     "n_rows": int(target.notna().sum())})
        per_word.insert(0, "language", lang)
        per_word.insert(0, "system", name)
        detail.append(per_word)

    summary = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    for frame, name, note in (
            (summary, "register_summary.csv",
             "English banking-loanword retention and Latin-script fraction, 150-row "
             "translation sample. Higher retention = closer to the code-mixed register "
             "Sri Lankan bank customers actually write. NOT a quality metric."),
            (pd.concat(detail, ignore_index=True), "register_per_loanword.csv",
             "per-loanword retention, same sample")):
        path = TABLES / name
        with path.open("w") as fh:
            fh.write(f"# {note} generated_by=register_metrics.py\n")
            frame.to_csv(path if False else fh, index=False)
        print(f"-> {path.relative_to(REPO)}")

    print()
    print(summary.round(4).to_string(index=False))

    have = {s for s, _ in systems}
    if have == {"swift (this corpus)"}:
        print("\nOnly this corpus is measured -- no external system collected yet.")
        print("These are the numbers the comparison will be judged against, fixed now,")
        print("before any competitor's file exists.")


if __name__ == "__main__":
    main()
