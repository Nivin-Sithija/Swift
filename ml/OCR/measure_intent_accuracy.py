"""Intent accuracy against the TRUE label, per router and per OCR engine.

measure_end_to_end_ocr.py scores self-agreement (does the router still reach its own
clean-text answer). This script scores the harder question: is the answer RIGHT.

The bridge is hand-built and is the main assumption in this file. labels.json carries 15
simplified categories; the routers emit 77 BANKING77 intents. ACCEPTABLE maps each category
to the set of BANKING77 intents that mean the same thing, and a prediction counts as correct
when it lands anywhere in that set. Widening or narrowing a set moves the numbers, so the
per-category table is printed alongside the headline to keep that visible.

"OTP not received" has no BANKING77 equivalent at all and is excluded from the headline
accuracy, then reported separately.

    python measure_intent_accuracy.py             # SVM only (the production path)
    python measure_intent_accuracy.py --labse     # adds the LaBSE encoder arm
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENGINES = {
    "tesseract": "ocr_tesseract_optimized_metrics.csv",
    "google_vision": "ocr_google_vision_metrics.csv",
}
CONDITION_ORDER = ["clean", "blur", "rotation", "low-resolution"]

# Synthetic category -> the BANKING77 intents that count as the same answer.
ACCEPTABLE = {
    "Card payment declined": {"declined_card_payment"},
    "Transfer failed": {"failed_transfer", "declined_transfer"},
    "Cash withdrawal failure": {"declined_cash_withdrawal"},
    "Transfer pending": {"pending_transfer", "transfer_timing"},
    "Wrong exchange rate": {
        "card_payment_wrong_exchange_rate",
        "wrong_exchange_rate_for_cash_withdrawal",
        "exchange_rate",
    },
    "Cash not received": {"wrong_amount_of_cash_received", "pending_cash_withdrawal"},
    "Refund pending": {"Refund_not_showing_up", "request_refund"},
    "Unauthorized transaction": {
        "card_payment_not_recognised",
        "cash_withdrawal_not_recognised",
        "direct_debit_payment_not_recognised",
        "compromised_card",
    },
    "Card stolen": {"lost_or_stolen_card", "compromised_card"},
    "Balance not updated": {
        "balance_not_updated_after_bank_transfer",
        "balance_not_updated_after_cheque_or_cash_deposit",
    },
    "Cash withdrawal charged incorrectly": {"cash_withdrawal_charge"},
    "Beneficiary not added": {"beneficiary_not_allowed"},
    "Duplicate transaction": {"transaction_charged_twice"},
    "Account blocked": {"pin_blocked"},
    # No BANKING77 intent expresses "the one-time passcode never arrived".
    "OTP not received": set(),
}
UNMAPPABLE = {category for category, allowed in ACCEPTABLE.items() if not allowed}


def load_true_categories(ml_dir: Path) -> dict[int, str]:
    labels_path = ml_dir.parent / "synthetic_ticket_dataset" / "labels.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    # labels.json holds only the clean image; the id ties the 4 conditions back to it.
    return {int(Path(item["image_path"]).stem.split("_")[-1]): item["category"] for item in labels}


def load_frame(root_dir: Path, ml_dir: Path) -> pd.DataFrame:
    base = None
    for name, filename in ENGINES.items():
        frame = pd.read_csv(root_dir / "results" / filename)[
            ["id", "image_path", "condition", "scripts", "ground_truth", "predicted_text"]
        ].rename(columns={"predicted_text": name})
        base = frame if base is None else base.merge(
            frame[["image_path", name]], on="image_path", how="inner"
        )
    assert base is not None
    base["true_category"] = base["id"].astype(int).map(load_true_categories(ml_dir))
    missing = base["true_category"].isna().sum()
    if missing:
        print(f"Warning: {missing} rows had no true category and were dropped.")
        base = base.dropna(subset=["true_category"])
    return base


def is_correct(row: pd.Series, column: str) -> bool:
    return row[column] in ACCEPTABLE.get(row["true_category"], set())


def accuracy(df: pd.DataFrame, column: str) -> float:
    if df.empty:
        return float("nan")
    return df.apply(lambda r: is_correct(r, column), axis=1).mean() * 100


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labse", action="store_true")
    parser.add_argument("--out", default="intent_accuracy_by_ocr_engine.md")
    args = parser.parse_args()

    root_dir = Path(__file__).parent.resolve()
    ml_dir = root_dir.parent
    df = load_frame(root_dir, ml_dir)
    sources = ["ground_truth"] + list(ENGINES)

    routers = {"SVM": joblib.load(ml_dir / "models" / "tfidf_linear_svm_all.joblib")}
    print(f"Scoring {len(df)} images. Running TF-IDF SVM router...")
    for source in sources:
        df[f"SVM__{source}"] = routers["SVM"].predict(df[source].fillna("").astype(str))

    if args.labse:
        import torch
        from transformers import pipeline

        print("Running LaBSE router (slow on CPU)...")
        model_path = ml_dir / "models" / "encoders" / "intent_labse" / "best_model"
        classifier = pipeline(
            "text-classification",
            model=str(model_path),
            tokenizer=str(model_path),
            device=0 if torch.cuda.is_available() else -1,
            max_length=128,
            truncation=True,
            batch_size=32,
        )
        for source in sources:
            print(f"  - {source}")
            texts = df[source].fillna("").astype(str).tolist()
            df[f"LaBSE__{source}"] = [p["label"] for p in classifier(texts)]
        routers["LaBSE"] = None

    scored = df[~df["true_category"].isin(UNMAPPABLE)]
    excluded = len(df) - len(scored)

    lines = [
        "# Intent Accuracy by Router and OCR Engine",
        "",
        "Accuracy against the **true** category from `labels.json`, not self-agreement. A prediction",
        "counts as correct when it falls in the set of BANKING77 intents that mean the same thing as",
        "the synthetic category (the `ACCEPTABLE` map in `ml/OCR/measure_intent_accuracy.py`).",
        "",
        f"Scored on {len(scored)} of {len(df)} rows. The {excluded} rows labelled "
        f"{sorted(UNMAPPABLE)} are excluded: no BANKING77 intent expresses that meaning, so no",
        "router can be right on them.",
        "",
        "`ground_truth` is the ceiling: perfect OCR. The two engine columns show what each OCR",
        "engine costs against that ceiling.",
    ]

    for router in routers:
        header = f"### {router} router"
        print("\n" + header)
        print(f"{'Condition':<17}" + "".join(f"{s:>16}" for s in sources))
        lines += ["", header, "", "| Condition | " + " | ".join(sources) + " |",
                  "|---" * (1 + len(sources)) + "|"]
        for condition in CONDITION_ORDER + ["OVERALL"]:
            subset = scored if condition == "OVERALL" else scored[scored["condition"] == condition]
            cells = [accuracy(subset, f"{router}__{source}") for source in sources]
            print(f"{condition:<17}" + "".join(f"{c:>15.2f}%" for c in cells))
            label = f"**{condition}**" if condition == "OVERALL" else f"`{condition}`"
            lines.append(f"| {label} | " + " | ".join(f"{c:.2f}%" for c in cells) + " |")

    # Per-category detail keeps the hand-built map honest and visible.
    print("\nPer-category accuracy (SVM, all conditions pooled):")
    lines += ["", "### Per-category accuracy (SVM, all conditions pooled)", "",
              "| Category | " + " | ".join(sources) + " | n |", "|---" * (2 + len(sources)) + "|"]
    for category, group in scored.groupby("true_category"):
        cells = [accuracy(group, f"SVM__{source}") for source in sources]
        print(f"  {category:<38}" + "".join(f"{c:>8.1f}%" for c in cells) + f"{len(group):>7}")
        lines.append(f"| {category} | " + " | ".join(f"{c:.1f}%" for c in cells)
                     + f" | {len(group)} |")

    out_path = ml_dir / "reports" / args.out
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved report to {out_path}")


if __name__ == "__main__":
    main()
