"""Compare Google Cloud Vision against Tesseract on the same images.

Usage (from the backend directory):
    python scripts/benchmark_ocr.py                 # every image in scripts/
    python scripts/benchmark_ocr.py path/to/img.png ...

Google Vision needs SWIFT_GOOGLE_VISION_API_KEY in backend/.env.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Sinhala and Tamil output would otherwise crash a cp1252 Windows console.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.inference.ocr import OcrError, extract_text  # noqa: E402

ENGINES = ("tesseract", "google_vision")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


async def run_engine(engine: str, image_path: str) -> None:
    print(f"\n--- {engine} ---")
    started = time.perf_counter()
    try:
        result = await extract_text(image_path, engine=engine)
    except (OcrError, OSError) as exc:
        print(f"FAILED after {time.perf_counter() - started:.2f}s: {exc}")
        return
    elapsed = time.perf_counter() - started
    confidence = f"{result.confidence:.3f}" if result.confidence is not None else "n/a"
    print(f"time: {elapsed:.2f}s | chars: {len(result.text)} | confidence: {confidence}")
    print(result.text if result.text else "(no text extracted)")


async def benchmark(image_path: str) -> None:
    print("=" * 60)
    print(image_path)
    print("=" * 60)
    if not os.path.exists(image_path):
        print("Error: file not found")
        return
    for engine in ENGINES:
        await run_engine(engine, image_path)


async def main(paths: list[str]) -> None:
    for path in paths:
        await benchmark(path)


if __name__ == "__main__":
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    images = sys.argv[1:] or sorted(
        os.path.join(scripts_dir, name)
        for name in os.listdir(scripts_dir)
        if name.lower().endswith(IMAGE_SUFFIXES)
    )
    if not images:
        print("No images given and none found in scripts/")
        raise SystemExit(1)
    asyncio.run(main(images))
