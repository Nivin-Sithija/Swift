"""Non-mutating integrity and metric checks for the Swift data-science artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score


ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]
EXPECTED_COLUMNS = ["id", "text_en", "text", "category", "sentiment", "priority"]


def main() -> None:
    result: dict[str, object] = {"dataset": {}, "split": {}, "artifacts": {}, "metrics": {}}
    reference: dict[str, pd.DataFrame] = {}
    structural_pass = True

    for split, expected_rows in (("train", 9998), ("test", 3079)):
        frames = {}
        for language in LANGUAGES:
            path = ROOT / "datasets" / language / f"{split}_labeled.csv"
            frame = pd.read_csv(path)
            frames[language] = frame
            valid = (
                list(frame.columns) == EXPECTED_COLUMNS
                and len(frame) == expected_rows
                and frame["id"].nunique() == expected_rows
                and not frame[EXPECTED_COLUMNS].isna().any().any()
                and frame["category"].nunique() == 77
                and set(frame["sentiment"].unique()) <= {"Neutral", "Negative"}
                and set(frame["priority"].unique()) <= {"Low", "Medium", "High"}
            )
            result["dataset"][f"{language}_{split}"] = {
                "rows": len(frame), "classes": frame["category"].nunique(), "pass": bool(valid)
            }
            structural_pass &= bool(valid)

        english = frames["english"].set_index("id")
        reference[split] = english
        for language, frame in frames.items():
            aligned = frame.set_index("id")
            labels = ["category", "sentiment", "priority"]
            same_ids = aligned.index.equals(english.index)
            same_labels = same_ids and aligned[labels].equals(english[labels])
            same_source_text = same_ids and aligned["text_en"].equals(english["text_en"])
            result["dataset"][f"{language}_{split}"].update({
                "id_alignment": same_ids,
                "cross_language_label_alignment": same_labels,
                "source_text_alignment": same_source_text,
            })
            structural_pass &= same_ids and same_labels and same_source_text

    manifest_path = ROOT / "ml" / "splits" / "split_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    train_ids, dev_ids, test_ids = map(set, (
        manifest["train_ids"], manifest["dev_ids"], manifest["test_ids"]
    ))
    split_pass = (
        manifest["sha"] == "e7b5934392cd"
        and manifest["counts"] == {"train": 8500, "dev": 1498, "test": 3079}
        and len(train_ids) == 8500 and len(dev_ids) == 1498 and len(test_ids) == 3079
        and train_ids.isdisjoint(dev_ids)
    )
    result["split"] = {
        "sha": manifest["sha"], "counts": manifest["counts"],
        "train_dev_disjoint": train_ids.isdisjoint(dev_ids), "pass": split_pass,
        "note": "Train/test ids are indexes in different source CSVs; namespace is split-specific."
    }
    structural_pass &= split_pass

    run_files = list((ROOT / "ml" / "reports" / "runs").glob("*.json"))
    split_shas = {}
    malformed = []
    for path in run_files:
        try:
            payload = json.loads(path.read_text())
            sha = payload.get("split_sha", payload.get("split", {}).get("sha", "missing"))
            split_shas[sha] = split_shas.get(sha, 0) + 1
        except Exception as exc:  # pragma: no cover - evidence path
            malformed.append({"file": path.name, "error": str(exc)})
    result["artifacts"] = {
        "run_json_count": len(run_files), "split_sha_counts": split_shas,
        "malformed_json": malformed, "pass": not malformed,
    }
    structural_pass &= not malformed

    predictions = {
        "intent_labse": ROOT / "ml/predictions/runs/intent__labse__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-class-weight__test.csv",
        "intent_tfidf_svm": ROOT / "ml/predictions/runs/intent__tfidf-svm__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-none__test.csv",
        "sentiment_labse": ROOT / "ml/predictions/runs/sentiment__labse__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-class-weight__test.csv",
        "sentiment_tfidf_svm": ROOT / "ml/predictions/runs/sentiment__tfidf-svm__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-class-weight__test.csv",
        "priority_tfidf_svm": ROOT / "ml/predictions/runs/priority__tfidf-svm__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-class-weight__test.csv",
    }
    for name, path in predictions.items():
        frame = pd.read_csv(path)
        if name.startswith("sentiment"):
            headline = f1_score(frame.y_true, frame.y_pred, pos_label="Negative")
            metric_name = "negative_f1"
        else:
            headline = f1_score(frame.y_true, frame.y_pred, average="macro")
            metric_name = "macro_f1"
        result["metrics"][name] = {
            "rows": len(frame), metric_name: round(float(headline), 6),
            "accuracy": round(float(accuracy_score(frame.y_true, frame.y_pred)), 6),
            "per_language_error_rate": {
                language: round(float((part.y_true != part.y_pred).mean()), 6)
                for language, part in frame.groupby("language")
            },
        }

    result["overall_structural_pass"] = structural_pass
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
