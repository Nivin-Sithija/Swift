"""Evaluate Google Cloud Vision on the same 2,000-image benchmark as Tesseract.

Writes results/ocr_google_vision_metrics.csv with the exact column schema
evaluate_tesseract.py produces, so analyze_ocr_results.py and
compare_ocr_engines.py can read either file.

    python evaluate_google_vision.py --sample 120     # cheap stratified pilot
    python evaluate_google_vision.py                  # full 2,000-image run

Needs SWIFT_GOOGLE_VISION_API_KEY in the environment or in backend/.env.
"""

import argparse
import asyncio
import base64
import os
import sys
import time
from pathlib import Path

import httpx
import jiwer
import pandas as pd

VISION_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"
MAX_IMAGES_PER_REQUEST = 16  # Cloud Vision's per-call limit for images:annotate

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_language_hints(row: pd.Series) -> list[str]:
    """Mirror evaluate_tesseract.py's per-row language routing."""
    language = str(row.get("primary_language", "")).lower()
    script = str(row.get("scripts", "")).lower()
    if "sinhala" in script or "sinhala" in language:
        return ["si", "en"]
    if "tamil" in script or "tamil" in language:
        return ["ta", "en"]
    return ["en"]


def load_api_key(root_dir: Path) -> str:
    key = os.environ.get("SWIFT_GOOGLE_VISION_API_KEY", "").strip()
    if key:
        return key
    env_path = root_dir.parents[1] / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "SWIFT_GOOGLE_VISION_API_KEY" and value.strip():
                return value.strip().strip('"').strip("'")
    raise SystemExit(
        "SWIFT_GOOGLE_VISION_API_KEY is not set. Put it in backend/.env or the environment."
    )


def select_rows(df: pd.DataFrame, sample: int | None, limit: int | None, seed: int) -> pd.DataFrame:
    if limit:
        return df.head(limit)
    if not sample:
        return df
    # Stratify across condition x language so a small pilot still covers the hard cases.
    groups = df.groupby(["condition", "primary_language"])
    per_group = max(1, sample // max(1, groups.ngroups))
    picked_index = []
    for _, group in groups:
        picked_index.extend(group.sample(min(len(group), per_group), random_state=seed).index)
    subset = df.loc[picked_index]
    if len(subset) > sample:
        subset = subset.sample(sample, random_state=seed)
    elif len(subset) < sample:
        # Integer division leaves a remainder; top up so --sample N really means N.
        spare = df.drop(index=subset.index)
        subset = pd.concat(
            [subset, spare.sample(min(len(spare), sample - len(subset)), random_state=seed)]
        )
    return subset.sort_values("id")


def score(ground_truth: str, predicted: str) -> tuple[float, float]:
    truth, prediction = ground_truth.lower().strip(), predicted.lower().strip()
    try:
        if truth and prediction:
            return jiwer.wer(truth, prediction), jiwer.cer(truth, prediction)
        if truth and not prediction:
            return 1.0, 1.0
        return 0.0, 0.0
    except Exception:
        return 1.0, 1.0


def build_request(root_dir: Path, row: pd.Series) -> dict:
    encoded = base64.b64encode((root_dir / row["image_path"]).read_bytes()).decode("ascii")
    return {
        "image": {"content": encoded},
        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
        "imageContext": {"languageHints": get_language_hints(row)},
    }


def read_annotation(body: dict) -> str:
    if "error" in body:
        return ""
    annotation = body.get("fullTextAnnotation") or {}
    return " ".join(str(annotation.get("text", "")).split())


async def run_batch(
    client: httpx.AsyncClient,
    api_key: str,
    root_dir: Path,
    batch: list[pd.Series],
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    payload = {"requests": [build_request(root_dir, row) for row in batch]}
    async with semaphore:
        started = time.time()
        try:
            response = await client.post(VISION_ENDPOINT, params={"key": api_key}, json=payload)
            response.raise_for_status()
            bodies = response.json().get("responses", [])
        except (httpx.HTTPError, ValueError) as exc:
            print(f"  batch failed: {exc}")
            bodies = []
        # Images in a batch share one round trip, so latency is reported per image.
        latency = (time.time() - started) / len(batch)

    rows = []
    for index, row in enumerate(batch):
        predicted = read_annotation(bodies[index]) if index < len(bodies) else ""
        wer, cer = score(str(row.get("ground_truth", "")), predicted)
        record = row.to_dict()
        record.update(predicted_text=predicted, wer=wer, cer=cer, latency=latency)
        rows.append(record)
    return rows


async def evaluate(args: argparse.Namespace) -> None:
    root_dir = Path(__file__).parent.resolve()
    api_key = load_api_key(root_dir)
    results_path = root_dir / "results" / args.out

    df = pd.read_csv(root_dir / "metadata.csv")
    df = df[df["ground_truth"].astype(str).str.strip() != ""]
    df = df[[(root_dir / p).exists() for p in df["image_path"]]]
    df = select_rows(df, args.sample, args.limit, args.seed)

    done: list[dict] = []
    if args.resume and results_path.exists():
        done = pd.read_csv(results_path).to_dict("records")
        completed = {record["image_path"] for record in done}
        df = df[~df["image_path"].isin(completed)]
        print(f"Resuming: {len(completed)} already scored, {len(df)} to go.")

    print(f"Evaluating {len(df)} images with Google Cloud Vision (DOCUMENT_TEXT_DETECTION)...")
    print(f"Billable units: ~{len(df)} (first 1,000/month free, then ~$1.50 per 1,000).")
    if not len(df):
        return

    rows = [row for _, row in df.iterrows()]
    batches = [
        rows[i : i + args.batch_size] for i in range(0, len(rows), args.batch_size)
    ]
    semaphore = asyncio.Semaphore(args.concurrency)
    results = list(done)
    started = time.time()

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        tasks = [run_batch(client, api_key, root_dir, batch, semaphore) for batch in batches]
        for finished, task in enumerate(asyncio.as_completed(tasks), start=1):
            results.extend(await task)
            if finished % 5 == 0 or finished == len(batches):
                print(f"  {finished}/{len(batches)} batches ({len(results)} images)")

    results_path.parent.mkdir(exist_ok=True)
    frame = pd.DataFrame(results)
    frame.to_csv(results_path, index=False)
    print(f"\nSaved {len(frame)} records to {results_path}")
    print(f"Wall clock: {time.time() - started:.1f}s")
    print(f"Overall CER {frame.cer.mean():.4f} | WER {frame.wer.mean():.4f}")
    print(frame.groupby("condition")[["cer", "wer"]].mean().round(4).to_string())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, help="stratified subset size (cheap pilot)")
    parser.add_argument("--limit", type=int, help="take the first N rows instead")
    parser.add_argument("--out", default="ocr_google_vision_metrics.csv")
    parser.add_argument("--batch-size", type=int, default=MAX_IMAGES_PER_REQUEST)
    parser.add_argument("--concurrency", type=int, default=4, help="parallel API calls")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true", help="skip ids already in --out")
    args = parser.parse_args()
    args.batch_size = max(1, min(args.batch_size, MAX_IMAGES_PER_REQUEST))
    return args


if __name__ == "__main__":
    asyncio.run(evaluate(parse_args()))
