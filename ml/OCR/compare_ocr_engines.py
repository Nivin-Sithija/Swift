"""Put two OCR metric files side by side and say which engine wins where.

    python compare_ocr_engines.py ocr_tesseract_optimized_metrics.csv \
        ocr_google_vision_metrics.csv

Only the images present in both files are compared, so a sampled Google Vision run
can be checked against the full Tesseract baseline.
"""

import sys
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(results_dir: Path, filename: str) -> pd.DataFrame:
    path = results_dir / filename
    if not path.exists():
        raise SystemExit(f"{path} not found.")
    return pd.read_csv(path)


def summarize(merged: pd.DataFrame, keys: list[str], left: str, right: str) -> pd.DataFrame:
    summary = merged.groupby(keys).agg(
        cer_a=("cer_a", "mean"),
        cer_b=("cer_b", "mean"),
        wer_a=("wer_a", "mean"),
        wer_b=("wer_b", "mean"),
        n=("image_path", "count"),
    )
    summary["cer_delta"] = summary["cer_b"] - summary["cer_a"]
    summary["wer_delta"] = summary["wer_b"] - summary["wer_a"]
    return summary.rename(
        columns={
            "cer_a": f"cer_{left}",
            "cer_b": f"cer_{right}",
            "wer_a": f"wer_{left}",
            "wer_b": f"wer_{right}",
        }
    ).reset_index()


def main() -> None:
    results_dir = Path(__file__).parent.resolve() / "results"
    baseline_file = sys.argv[1] if len(sys.argv) > 1 else "ocr_tesseract_optimized_metrics.csv"
    candidate_file = sys.argv[2] if len(sys.argv) > 2 else "ocr_google_vision_metrics.csv"

    left = baseline_file.replace("ocr_", "").replace("_metrics.csv", "")[:12]
    right = candidate_file.replace("ocr_", "").replace("_metrics.csv", "")[:12]

    # image_path is the unique key: id repeats once per degradation condition.
    a = load(results_dir, baseline_file)[["image_path", "cer", "wer", "latency"]]
    b = load(results_dir, candidate_file)[
        ["id", "image_path", "cer", "wer", "latency", "condition", "scripts",
         "primary_language"]
    ]
    merged = b.merge(a, on="image_path", suffixes=("_b", "_a"))
    if merged.empty:
        raise SystemExit("No overlapping images between the two result files.")

    print(f"Comparing {len(merged)} images shared by both runs")
    print(f"  A = {baseline_file}")
    print(f"  B = {candidate_file}\n")

    print("=== Overall ===")
    for label, cer, wer, latency in (
        (left, "cer_a", "wer_a", "latency_a"),
        (right, "cer_b", "wer_b", "latency_b"),
    ):
        print(
            f"  {label:>12}: CER {merged[cer].mean():.4f} | "
            f"WER {merged[wer].mean():.4f} | latency {merged[latency].mean():.3f}s"
        )
    cer_gain = merged["cer_a"].mean() - merged["cer_b"].mean()
    print(f"  CER improvement from {right}: {cer_gain:+.4f} ({cer_gain * 100:+.1f} points)")

    wins = (merged["cer_b"] < merged["cer_a"]).mean()
    ties = (merged["cer_b"] == merged["cer_a"]).mean()
    print(f"  Per-image CER: {right} better on {wins:.1%}, tied {ties:.1%}\n")

    print("=== By condition ===")
    print(summarize(merged, ["condition"], left, right).to_string(index=False, float_format="%.4f"))

    print("\n=== By script ===")
    print(summarize(merged, ["scripts"], left, right).to_string(index=False, float_format="%.4f"))

    print("\n=== By language ===")
    print(
        summarize(merged, ["primary_language"], left, right).to_string(
            index=False, float_format="%.4f"
        )
    )

    print("\n=== Worst 10 images for the candidate (largest CER regression) ===")
    worst = merged.assign(delta=merged["cer_b"] - merged["cer_a"]).nlargest(10, "delta")
    print(
        worst[["id", "primary_language", "condition", "cer_a", "cer_b", "delta"]].to_string(
            index=False, float_format="%.4f"
        )
    )


if __name__ == "__main__":
    main()
