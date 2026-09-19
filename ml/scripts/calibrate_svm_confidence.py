"""Fit a confidence calibration for the production TF-IDF SVM intent router.

LinearSVC has no predict_proba: its decision scores are margins, not probabilities, so the
backend cannot use them as a confidence directly. This script fits a small logistic model

    P(prediction is correct) = sigmoid(w_top * top_score + w_margin * (top - runner_up) + b)

and writes the three constants next to the model, where `backend/app/inference/services.py`
reads them.

The SVM was fit on the full train file, so the BANKING77 test file is the only held-out data.
It is used here for calibration only; the SVM itself and its reported test scores do not change.
Test ids are split in half (all five language renderings of an id stay on one side): the
calibration is fit on half A and its ECE is reported on half B, so the number is not measured
on the data it was fit on.

    python ml/scripts/calibrate_svm_confidence.py
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
MODEL = REPO / "ml" / "models" / "tfidf_linear_svm_all.joblib"
OUT = REPO / "ml" / "models" / "tfidf_linear_svm_all.calibration.json"
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]
RANDOM_STATE = 42


def load_test() -> pd.DataFrame:
    frames = []
    for language in LANGUAGES:
        frame = pd.read_csv(REPO / "datasets" / language / "test_labeled.csv")
        frames.append(
            pd.DataFrame(
                {
                    "id": frame["id"],
                    "text": frame["text"].astype(str).str.strip(),
                    "label": frame["category"],
                    "language": language,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def features(scores: np.ndarray) -> np.ndarray:
    ordered = np.sort(scores, axis=1)[:, ::-1]
    return np.column_stack([ordered[:, 0], ordered[:, 0] - ordered[:, 1]])


def ece(confidence: np.ndarray, correct: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (confidence > low) & (confidence <= high)
        if mask.any():
            total += mask.mean() * abs(confidence[mask].mean() - correct[mask].mean())
    return total


def main() -> None:
    pipeline = joblib.load(MODEL)
    df = load_test()
    scores = pipeline.decision_function(df["text"].tolist())
    predicted = pipeline.classes_[scores.argmax(axis=1)]
    correct = (predicted == df["label"].to_numpy()).astype(int)
    x = features(scores)

    ids = df["id"].unique()
    rng = np.random.default_rng(RANDOM_STATE)
    half_a = set(rng.choice(ids, size=len(ids) // 2, replace=False))
    in_a = df["id"].isin(half_a).to_numpy()

    model = LogisticRegression().fit(x[in_a], correct[in_a])
    held_out = model.predict_proba(x[~in_a])[:, 1]

    print(f"Rows: {len(df)} ({in_a.sum()} fit / {(~in_a).sum()} held out)")
    print(f"SVM accuracy on held-out half: {correct[~in_a].mean():.4f}")
    print(f"Mean calibrated confidence:    {held_out.mean():.4f}")
    print(f"ECE on held-out half:          {ece(held_out, correct[~in_a]):.4f}")
    print(f"ECE of the old fixed 0.85:     {ece(np.full(len(held_out), 0.85), correct[~in_a]):.4f}")

    w_top, w_margin = model.coef_[0]
    result = {
        "model": MODEL.name,
        "formula": "sigmoid(w_top * top_score + w_margin * (top_score - runner_up_score) + bias)",
        "w_top": float(w_top),
        "w_margin": float(w_margin),
        "bias": float(model.intercept_[0]),
        "fit_rows": int(in_a.sum()),
        "held_out_rows": int((~in_a).sum()),
        "held_out_accuracy": round(float(correct[~in_a].mean()), 4),
        "held_out_ece": round(float(ece(held_out, correct[~in_a])), 4),
        "source": "ml/scripts/calibrate_svm_confidence.py",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
