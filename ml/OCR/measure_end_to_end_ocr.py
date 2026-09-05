"""Measure what each OCR engine costs the intent router, engine against engine.

Same method as measure_end_to_end_intent.py: the synthetic set carries 15 simplified
categories while the routers emit 77 BANKING77 intents, so the target is the router's own
prediction on the clean ground-truth text. The score is therefore self-agreement -- how
often a router still reaches its own answer when it has to read OCR output instead.

    python measure_end_to_end_ocr.py                # SVM only (the production path)
    python measure_end_to_end_ocr.py --labse        # adds the LaBSE encoder arm

Both engines are scored on the images they share, so the columns are directly comparable.
"""

import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import f1_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENGINES = {
    "tesseract": "ocr_tesseract_optimized_metrics.csv",
    "google_vision": "ocr_google_vision_metrics.csv",
}
CONDITION_ORDER = ["clean", "blur", "rotation", "low-resolution"]


def load_engine_frames(results_dir: Path, engines: dict[str, str]) -> pd.DataFrame:
    """Join every engine's predicted_text onto one row per image."""
    base = None
    for name, filename in engines.items():
        path = results_dir / filename
        if not path.exists():
            raise SystemExit(f"{path} not found.")
        frame = pd.read_csv(path)[
            ["image_path", "condition", "scripts", "ground_truth", "predicted_text"]
        ].rename(columns={"predicted_text": name})
        if base is None:
            base = frame
        else:
            # image_path is the unique key; id repeats once per condition.
            base = base.merge(
                frame[["image_path", name]], on="image_path", how="inner"
            )
    assert base is not None
    return base


def score(target: pd.Series, prediction: pd.Series) -> tuple[float, float]:
    """Macro-F1 against the router's own clean-text answer, plus exact agreement."""
    macro = f1_score(target, prediction, average="macro", zero_division=0) * 100
    exact = (target.to_numpy() == prediction.to_numpy()).mean() * 100
    return macro, exact


def report(df: pd.DataFrame, arms: list[str], engines: list[str]) -> list[str]:
    lines = []
    for arm in arms:
        header = f"### {arm} router"
        print("\n" + header)
        lines += ["", header, ""]
        columns = " | ".join(f"{engine} F1 | {engine} exact" for engine in engines)
        lines.append(f"| Condition | {columns} |")
        lines.append("|---" * (1 + 2 * len(engines)) + "|")
        print(f"{'Condition':<16}" + "".join(f"{engine:>26}" for engine in engines))

        conditions = [c for c in CONDITION_ORDER if c in set(df["condition"])]
        for condition in conditions + ["OVERALL"]:
            subset = df if condition == "OVERALL" else df[df["condition"] == condition]
            cells, printed = [], ""
            for engine in engines:
                macro, exact = score(subset[f"{arm}_gt"], subset[f"{arm}_{engine}"])
                cells.append(f"{macro:.2f}% | {exact:.2f}%")
                printed += f"{macro:>10.2f} F1{exact:>10.2f} exact"
            label = f"**{condition}**" if condition == "OVERALL" else f"`{condition}`"
            lines.append(f"| {label} | {' | '.join(cells)} |")
            print(f"{condition:<16}" + printed)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labse", action="store_true", help="also run the LaBSE encoder arm")
    parser.add_argument("--out", default="end_to_end_ocr_engines.md")
    args = parser.parse_args()

    root_dir = Path(__file__).parent.resolve()
    ml_dir = root_dir.parent
    df = load_engine_frames(root_dir / "results", ENGINES)
    engines = list(ENGINES)
    print(f"Scoring {len(df)} images shared by {', '.join(engines)}.")

    texts = {"gt": df["ground_truth"].fillna("").astype(str)}
    for engine in engines:
        texts[engine] = df[engine].fillna("").astype(str)

    arms = []

    svm = joblib.load(ml_dir / "models" / "tfidf_linear_svm_all.joblib")
    print("Running TF-IDF SVM router...")
    for key, series in texts.items():
        df[f"SVM_{key}"] = svm.predict(series)
    arms.append("SVM")

    if args.labse:
        import torch
        from transformers import pipeline

        model_path = ml_dir / "models" / "encoders" / "intent_labse" / "best_model"
        if not model_path.exists():
            raise SystemExit(f"{model_path} not found.")
        print("Running LaBSE router (this is the slow arm on CPU)...")
        classifier = pipeline(
            "text-classification",
            model=str(model_path),
            tokenizer=str(model_path),
            device=0 if torch.cuda.is_available() else -1,
            max_length=128,
            truncation=True,
            batch_size=32,
        )
        for key, series in texts.items():
            print(f"  - {key}")
            df[f"LaBSE_{key}"] = [p["label"] for p in classifier(series.tolist())]
        arms.append("LaBSE")

    lines = [
        "# End-to-End OCR Impact by Engine",
        "",
        "Target is each router's own prediction on the clean ground-truth text, so the score is",
        "self-agreement: how often the router still reaches its own answer when reading OCR output.",
        "`F1` is macro-F1 over the 77 BANKING77 intents; `exact` is plain agreement.",
        f"Scored on {len(df)} images shared by both engines.",
        "",
        "Generated by `ml/OCR/measure_end_to_end_ocr.py`.",
    ]
    lines += report(df, arms, engines)

    out_path = ml_dir / "reports" / args.out
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved report to {out_path}")


if __name__ == "__main__":
    main()
