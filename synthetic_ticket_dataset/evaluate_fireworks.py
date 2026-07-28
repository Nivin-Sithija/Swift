#!/usr/bin/env python3
"""Evaluate generated banking screenshots with Fireworks AI."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import multiprocessing as mp
import os
import queue
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from openai import APITimeoutError, APIStatusError, OpenAI, RateLimitError
from dotenv import load_dotenv


BASE_URL = "https://api.fireworks.ai/inference/v1"
MODEL = "accounts/fireworks/models/kimi-k2p6"
DEFAULT_LIMIT = 20
EVALUATED_FIELDS = ("category", "priority", "sentiment")
RESPONSE_FIELDS = (
    "category",
    "priority",
    "sentiment",
    "visible_text",
    "image_summary",
    "error_code",
    "confidence",
)
SCRIPT_DIR = Path(__file__).resolve().parent

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "banking_screenshot_analysis",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                },
                "sentiment": {
                    "type": "string",
                    "enum": ["negative", "neutral", "positive"],
                },
                "visible_text": {"type": "string"},
                "image_summary": {"type": "string"},
                "error_code": {"type": ["string", "null"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": list(RESPONSE_FIELDS),
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = """Analyze the supplied synthetic mobile-banking screenshot.
Return only JSON matching the provided schema. Infer the support category,
priority, and sentiment from the screenshot itself. Transcribe all legible text
into visible_text, summarize the screen in image_summary, and copy the displayed
error code (or null if none). Confidence must be between 0 and 1.

Priority policy: security threats are critical; missing cash and duplicate
transactions are high; disrupted transfers/payments are medium; general
informational issues are low."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--labels", type=Path, default=SCRIPT_DIR / "labels.json")
    parser.add_argument("--results-dir", type=Path, default=SCRIPT_DIR / "results")
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args()


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def request_worker(
    result_queue: Any, api_key: str, data_url: str, timeout: float
) -> None:
    """Make one API call in a child process so it can be forcibly timed out."""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=BASE_URL,
            timeout=timeout,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            response_format=RESPONSE_FORMAT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Classify and extract this screenshot.",
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The model returned an empty response")
        prediction = json.loads(content)
        missing = set(RESPONSE_FIELDS) - prediction.keys()
        if missing:
            raise ValueError(f"Response missing fields: {sorted(missing)}")
        result_queue.put(("success", prediction))
    except Exception as exc:
        retryable = isinstance(exc, (RateLimitError, APITimeoutError)) or (
            isinstance(exc, APIStatusError) and exc.status_code in (429, 503)
        )
        result_queue.put(
            (
                "error",
                {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "retryable": retryable,
                },
            )
        )


def request_prediction(
    api_key: str, image_path: Path, max_retries: int, timeout: float
) -> dict[str, Any]:
    data_url = image_data_url(image_path)
    context = mp.get_context("fork")
    for attempt in range(max_retries + 1):
        started_at = time.monotonic()
        print(
            f"  Sending request (attempt {attempt + 1}/{max_retries + 1}, "
            f"deadline {timeout:g}s)...",
            flush=True,
        )
        result_queue = context.Queue(maxsize=1)
        process = context.Process(
            target=request_worker,
            args=(result_queue, api_key, data_url, timeout),
            daemon=True,
        )
        process.start()
        process.join(timeout)
        if process.is_alive():
            process.terminate()
            process.join(5)
            error_type = "RequestDeadlineError"
            error_message = f"Request exceeded {timeout:g} seconds"
            retryable = True
        else:
            try:
                status, payload = result_queue.get(timeout=1)
            except queue.Empty:
                status = "error"
                payload = {
                    "type": "RequestWorkerError",
                    "message": f"Request process exited with code {process.exitcode}",
                    "retryable": False,
                }
            if status == "success":
                print(
                    f"  Response received in {time.monotonic() - started_at:.1f}s",
                    flush=True,
                )
                result_queue.close()
                return payload
            error_type = payload["type"]
            error_message = payload["message"]
            retryable = payload["retryable"]
        result_queue.close()

        if not retryable or attempt >= max_retries:
            raise RuntimeError(f"{error_type}: {error_message}")
        delay = min(2**attempt, 30) + random.uniform(0, 0.5)
        print(
            f"  Attempt failed after {time.monotonic() - started_at:.1f}s: "
            f"{error_type}; retrying in {delay:.1f}s",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(delay)
    raise RuntimeError("Retry loop ended unexpectedly")


def confusion_matrix(
    expected: list[str], predicted: list[str]
) -> tuple[list[str], list[list[int]]]:
    labels = sorted(set(expected) | set(predicted))
    positions = {label: index for index, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for truth, guess in zip(expected, predicted):
        matrix[positions[truth]][positions[guess]] += 1
    return labels, matrix


def save_confusion_plot(
    field: str, labels: list[str], matrix: list[list[int]], output: Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    size = max(7, min(16, len(labels) * 0.75))
    fig, axis = plt.subplots(figsize=(size, size))
    image = axis.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=axis)
    axis.set(
        title=f"{field.title()} confusion matrix",
        xlabel="Predicted",
        ylabel="Expected",
        xticks=range(len(labels)),
        yticks=range(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
    for row, values in enumerate(matrix):
        for column, value in enumerate(values):
            axis.text(column, row, value, ha="center", va="center")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.max_retries < 0:
        raise SystemExit("--max-retries cannot be negative")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than 0")

    load_dotenv(SCRIPT_DIR / ".env")
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        print("FIREWORKS_API_KEY is not set.", file=sys.stderr)
        return 2

    labels_path = args.labels.resolve()
    records = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("labels.json must contain a JSON array")
    selected = records[: min(args.limit, len(records))]

    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = results_dir / "predictions.jsonl"
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    with predictions_path.open("w", encoding="utf-8") as output:
        for index, truth in enumerate(selected, start=1):
            relative_path = Path(truth["image_path"])
            image_path = (
                relative_path
                if relative_path.is_absolute()
                else labels_path.parent / relative_path
            )
            print(f"[{index}/{len(selected)}] {truth['image_path']}", flush=True)
            try:
                prediction = request_prediction(
                    api_key, image_path, args.max_retries, args.timeout
                )
                result = {
                    "image_path": truth["image_path"],
                    "status": "success",
                    "expected": {field: truth[field] for field in EVALUATED_FIELDS},
                    "prediction": prediction,
                }
                successes.append(result)
            except Exception as exc:
                result = {
                    "image_path": truth["image_path"],
                    "status": "failed",
                    "expected": {field: truth[field] for field in EVALUATED_FIELDS},
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                failures.append(result)
                print(f"  FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()

    metrics: dict[str, Any] = {}
    incorrect: list[dict[str, str]] = []
    for field in EVALUATED_FIELDS:
        expected = [item["expected"][field] for item in successes]
        predicted = [item["prediction"][field] for item in successes]
        correct = sum(a == b for a, b in zip(expected, predicted))
        labels, matrix = confusion_matrix(expected, predicted)
        metrics[field] = {
            "accuracy": correct / len(successes) if successes else None,
            "correct": correct,
            "evaluated": len(successes),
            "labels": labels,
            "confusion_matrix": matrix,
        }
        if labels:
            save_confusion_plot(
                field, labels, matrix, results_dir / f"{field}_confusion_matrix.png"
            )
        for item in successes:
            expected_value = item["expected"][field]
            predicted_value = item["prediction"][field]
            if expected_value != predicted_value:
                incorrect.append(
                    {
                        "image_path": item["image_path"],
                        "field": field,
                        "expected": expected_value,
                        "predicted": predicted_value,
                    }
                )

    report = {
        "model": MODEL,
        "requested_limit": args.limit,
        "total_selected": len(selected),
        "successful_requests": len(successes),
        "failed_requests": len(failures),
        "metrics": metrics,
        "incorrect_predictions": incorrect,
        "failure_types": dict(Counter(item["error_type"] for item in failures)),
        "failed_items": failures,
    }
    report_path = results_dir / "evaluation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("\nAccuracy (successful requests only):")
    for field, metric in metrics.items():
        accuracy = metric["accuracy"]
        display = "N/A" if accuracy is None else f"{accuracy:.2%}"
        print(f"  {field}: {display} ({metric['correct']}/{metric['evaluated']})")
    print("\nIncorrect predictions:")
    if incorrect:
        for item in incorrect:
            print(
                f"  {item['image_path']} | {item['field']} | "
                f"expected={item['expected']!r} | predicted={item['predicted']!r}"
            )
    else:
        print("  None")
    print(f"\nFailed requests: {len(failures)}")
    print(f"Predictions: {predictions_path}")
    print(f"Report: {report_path}")
    return 0 if successes else 1


if __name__ == "__main__":
    raise SystemExit(main())
