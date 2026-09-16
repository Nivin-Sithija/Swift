"""Error analysis for the paper's analysis section.

Reviewers read the error analysis to decide whether the authors understand their
own system. The project currently has one for Tanglish and nothing else.

Four outputs, each answering a question the paper raises but does not settle:

    intent_confusions.csv     Which of the 77 intents collapse into each other,
                              and is the confusion symmetric? Symmetric pairs are
                              a label-boundary problem; one-way pairs are a model
                              problem.
    negative_errors.csv       The Negative false negatives and false positives,
                              with text, for a qualitative read. This is where the
                              "Negative is a topic construct, not polarity" claim
                              either holds up or does not.
    priority_boundary.csv     The Low/Medium/High confusion matrix. Adjacent-class
                              errors are ordinal noise; Low<->High errors are real
                              failures and are counted separately.
    error_by_language.csv     Error rate per track per task, so the Tanglish gap
                              is quantified against the others rather than asserted.

Run:
    .venv312/bin/python paper/experiments/error_analysis.py
    .venv312/bin/python paper/experiments/error_analysis.py --model tfidf-svm
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"
PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2}


def find(task: str, model: str) -> pd.DataFrame | None:
    hits = sorted(PRED_DIR.glob(f"{task}__{model}__*__ev-all__*__test.csv"))
    return pd.read_csv(hits[0]) if hits else None


def with_text(pred: pd.DataFrame) -> pd.DataFrame:
    """Attach the ticket text and its English source, so errors can be read."""
    test = splits.get(config.LANGUAGES, "test")[["id", "language", "text", "text_en"]]
    return pred.merge(test, on=["id", "language"], how="left")


def intent_confusions(pred: pd.DataFrame, top: int) -> pd.DataFrame:
    wrong = pred[pred["y_true"] != pred["y_pred"]]
    pairs = (wrong.groupby(["y_true", "y_pred"]).size()
             .reset_index(name="n").sort_values("n", ascending=False))
    # Reverse-direction count, to separate a mutual boundary problem from a
    # one-way bias. A pair confused 40/38 is two intents that overlap; a pair
    # confused 40/2 is the model collapsing one into the other.
    rev = {(t, p): n for t, p, n in pairs.itertuples(index=False)}
    pairs["n_reverse"] = [rev.get((p, t), 0) for t, p, n in
                          pairs[["y_true", "y_pred", "n"]].itertuples(index=False)]
    pairs["symmetry"] = (pairs[["n", "n_reverse"]].min(axis=1)
                         / pairs[["n", "n_reverse"]].max(axis=1)).round(3)
    pairs["kind"] = pairs["symmetry"].apply(
        lambda s: "mutual (label boundary)" if s >= 0.5 else "one-way (model bias)")
    return pairs.head(top).reset_index(drop=True)


def negative_errors(pred: pd.DataFrame, per_kind: int) -> pd.DataFrame:
    df = with_text(pred)
    fn = df[(df["y_true"] == "Negative") & (df["y_pred"] != "Negative")].copy()
    fp = df[(df["y_true"] != "Negative") & (df["y_pred"] == "Negative")].copy()
    fn["error"] = "false_negative"
    fp["error"] = "false_positive"
    both = pd.concat([fn.head(per_kind), fp.head(per_kind)])
    return both[["error", "id", "language", "y_true", "y_pred", "text_en", "text"]]\
        .reset_index(drop=True)


def priority_boundary(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for true in config.PRIORITY_LABELS:
        for got in config.PRIORITY_LABELS:
            n = int(((pred["y_true"] == true) & (pred["y_pred"] == got)).sum())
            distance = abs(PRIORITY_RANK[true] - PRIORITY_RANK[got])
            rows.append({"y_true": true, "y_pred": got, "n": n,
                         "distance": distance,
                         "kind": "correct" if distance == 0 else
                                 "adjacent" if distance == 1 else "extreme"})
    df = pd.DataFrame(rows)
    total_err = df.loc[df["kind"] != "correct", "n"].sum()
    df["pct_of_errors"] = (100 * df["n"] / total_err).round(2).where(df["kind"] != "correct")
    return df


def error_by_language(preds: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for task, pred in preds.items():
        for lang in config.LANGUAGES:
            sub = pred[pred["language"] == lang]
            if sub.empty:
                continue
            rows.append({"task": task, "language": lang, "n": len(sub),
                         "errors": int((sub["y_true"] != sub["y_pred"]).sum()),
                         "error_rate": round(float((sub["y_true"] != sub["y_pred"]).mean()), 4)})
    df = pd.DataFrame(rows)
    # Relative to english, the reference track.
    base = df[df["language"] == "english"].set_index("task")["error_rate"]
    df["vs_english"] = (df["error_rate"] - df["task"].map(base)).round(4)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tfidf-svm")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--examples", type=int, default=40)
    args = ap.parse_args()

    preds = {}
    for task in ("intent", "sentiment", "priority"):
        p = find(task, args.model)
        if p is None:
            print(f"  no predictions for {task}/{args.model}")
        else:
            preds[task] = p
    if not preds:
        sys.exit("no predictions found -- run save_test_predictions.py first")

    OUT.mkdir(parents=True, exist_ok=True)

    if "intent" in preds:
        t = intent_confusions(preds["intent"], args.top)
        t.to_csv(OUT / "intent_confusions.csv", index=False)
        print(f"intent: top {len(t)} confusion pairs")
        print(t.head(8).to_string(index=False))
        mutual = int((t["kind"].str.startswith("mutual")).sum())
        print(f"  {mutual}/{len(t)} are mutual (label-boundary) rather than one-way\n")

    if "sentiment" in preds:
        t = negative_errors(preds["sentiment"], args.examples)
        t.to_csv(OUT / "negative_errors.csv", index=False)
        counts = t["error"].value_counts().to_dict()
        p = preds["sentiment"]
        print(f"sentiment: {int(((p['y_true']=='Negative')&(p['y_pred']!='Negative')).sum())} "
              f"false negatives, "
              f"{int(((p['y_true']!='Negative')&(p['y_pred']=='Negative')).sum())} false positives"
              f"  (sampled {counts} to file)\n")

    if "priority" in preds:
        t = priority_boundary(preds["priority"])
        t.to_csv(OUT / "priority_boundary.csv", index=False)
        adj = t.loc[t["kind"] == "adjacent", "n"].sum()
        ext = t.loc[t["kind"] == "extreme", "n"].sum()
        print(f"priority: {adj} adjacent-class errors, {ext} Low<->High errors "
              f"({100*ext/(adj+ext):.1f}% extreme)\n")

    t = error_by_language(preds)
    t.to_csv(OUT / "error_by_language.csv", index=False)
    print("error rate by language:")
    print(t.to_string(index=False))
    print(f"\nwritten to {OUT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
