"""Collect the local GPT-OSS system's translations via the Ollama API (task B2).

Every other system in this comparison (OpenAI, Gemini) is collected by a human
pasting `samples/prompt_{system}_{lang}.md` into that model's chat UI and saving
the reply. GPT-OSS runs locally, so this does the same paste mechanically: it
sends the identical prompt file, unmodified, to `ollama` and saves the reply in
the same `id,translation` format the other systems use. Same prompt, same rows,
same instructions -- only the system differs, which is the whole point of the
comparison (see README.md's "never anchor the model" note).

First attempt is single-shot (the whole prompt in one call), matching exactly
what a human pasting into a chat window would do. If the model truncates or
drops ids -- the standard failure mode `validate_translations.py` checks for,
and more likely on a 20B local model than a frontier one -- this falls back to
chunked calls and records that deviation in `systems/MANIFEST.md`, because a
methods section that silently used a different procedure for one system than
the others is exactly the kind of thing a reviewer catches.

Run:
    .venv312/bin/python paper/experiments/fetch_gptoss_translations.py
    .venv312/bin/python paper/experiments/fetch_gptoss_translations.py --chunk-size 30
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "paper" / "translation_eval" / "samples"
SYSTEMS = REPO / "paper" / "translation_eval" / "systems"
OLLAMA = "http://localhost:11434/api/generate"
MODEL = "gpt-oss-20b"
LANGS = ["sinhala", "tamil"]


def call_ollama(prompt: str, timeout: int) -> str:
    resp = requests.post(
        OLLAMA,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 16384},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def parse_csv_reply(text: str) -> dict[int, str]:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()
    # Some models preface the CSV with a sentence despite instructions not to;
    # cut everything before the header row rather than failing outright.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("id,translation") or line.strip().lower().startswith("id,"):
            text = "\n".join(lines[i:])
            break
    out: dict[int, str] = {}
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    for row in reader:
        if len(row) < 2 or not row[0].strip():
            continue
        try:
            rid = int(row[0].strip())
        except ValueError:
            continue
        out[rid] = ",".join(row[1:]).strip()
    return out


def rows_block(sample_rows: list[tuple[int, str]]) -> str:
    lines = ["id,text_en"]
    for rid, text_en in sample_rows:
        lines.append(f'{rid},"{text_en.replace(chr(34), chr(39))}"')
    return "\n".join(lines)


def build_prompt(template: str, sample_rows: list[tuple[int, str]]) -> str:
    # The saved prompt file already has the full 150-row block baked in for the
    # single-shot case. For chunked/per-row fallback we need the instructions
    # without the original row block, so split on the "Here are the" marker
    # that build_translation_sample.py's header always emits just before the
    # rows.
    marker = "Here are the"
    idx = template.index(marker)
    end_of_line = template.index("\n", idx)
    header = template[: end_of_line + 1]
    # The header line says "Here are the 150 rows to translate" verbatim --
    # leaving that stale count in place while actually sending 1 or 30 rows
    # measurably caused the model to loop in hidden reasoning (reconciling the
    # stated count against what it was actually given) until it ran out of
    # budget and returned nothing, on a handful of rows that succeeded fine
    # once the count matched what was really sent.
    header = re.sub(r"\d+(?=\s+rows? to translate)", str(len(sample_rows)), header)
    return header + rows_block(sample_rows)


def load_prompt_rows(lang: str) -> list[tuple[int, str]]:
    import pandas as pd

    sample = pd.read_csv(SAMPLES / "sample_ids.csv")
    return list(zip(sample["id"].astype(int), sample["text_en"]))


def fetch_lang(lang: str, chunk_size: int, timeout: int) -> tuple[dict[int, str], str]:
    """Returns (id -> translation, method) where method is 'single-shot' or 'chunked:N'."""
    template = (SAMPLES / f"prompt_gptoss_{lang}.md").read_text()
    all_rows = load_prompt_rows(lang)
    expected_ids = {rid for rid, _ in all_rows}

    print(f"  [{lang}] single-shot call ({len(all_rows)} rows)...")
    t0 = time.time()
    reply = call_ollama(template, timeout=timeout)
    got = parse_csv_reply(reply)
    print(f"    {len(got)}/{len(expected_ids)} ids returned in {time.time() - t0:.0f}s")

    if expected_ids <= got.keys():
        return got, "single-shot"

    print(f"    single-shot lost {len(expected_ids - got.keys())} id(s); "
          f"falling back to chunks of {chunk_size}")
    merged: dict[int, str] = {}
    for i in range(0, len(all_rows), chunk_size):
        chunk = all_rows[i:i + chunk_size]
        prompt = build_prompt(template, chunk)
        t0 = time.time()
        reply = call_ollama(prompt, timeout=timeout)
        piece = parse_csv_reply(reply)
        print(f"    rows {i}-{i + len(chunk) - 1}: {len(piece)}/{len(chunk)} ids "
              f"in {time.time() - t0:.0f}s")
        merged.update(piece)
    return merged, f"chunked:{chunk_size}"


def fill_missing(lang: str, timeout: int) -> tuple[int, int]:
    """Retry only the still-blank rows of an existing systems/gptoss_{lang}.csv,
    one row per call. Batches of 30 were blowing the model's hidden reasoning
    budget before it ever reached the visible answer -- a lone row does not, and
    an 11s single-row call observed in testing makes even a large gap affordable.
    Returns (filled, still_missing)."""
    out_path = SYSTEMS / f"gptoss_{lang}.csv"
    template = (SAMPLES / f"prompt_gptoss_{lang}.md").read_text()
    rows = {rid: text for rid, text in load_prompt_rows(lang)}

    import pandas as pd
    df = pd.read_csv(out_path)
    blank = df["translation"].isna() | (df["translation"].astype(str).str.strip() == "")
    missing_ids = df.loc[blank, "id"].astype(int).tolist()

    filled = {}
    for rid in missing_ids:
        prompt = build_prompt(template, [(rid, rows[rid])])
        t0 = time.time()
        try:
            reply = call_ollama(prompt, timeout=timeout)
            piece = parse_csv_reply(reply)
        except requests.exceptions.RequestException as e:
            print(f"    id {rid}: request failed ({e}), leaving blank")
            continue
        dt_s = time.time() - t0
        if rid in piece and piece[rid].strip():
            filled[rid] = piece[rid]
            print(f"    id {rid}: OK in {dt_s:.0f}s")
        else:
            print(f"    id {rid}: still empty after {dt_s:.0f}s")

    for rid, text in filled.items():
        df.loc[df["id"] == rid, "translation"] = text
    df.to_csv(out_path, index=False)
    return len(filled), len(missing_ids) - len(filled)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-size", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=1800,
                     help="seconds per API call; single-shot on a 20B local model is slow")
    ap.add_argument("--fill-missing", action="store_true",
                     help="retry only the blank rows of an existing systems/gptoss_{lang}.csv, "
                          "one row per call, instead of the full single-shot/chunked fetch")
    args = ap.parse_args()

    SYSTEMS.mkdir(parents=True, exist_ok=True)
    manifest_lines = [
        f"## gptoss -- {MODEL} (Ollama, local)",
        f"collected: {dt.datetime.now().isoformat(timespec='seconds')}",
    ]

    if args.fill_missing:
        for lang in LANGS:
            print(f"  [{lang}] retrying blank rows one at a time...")
            filled, still_missing = fill_missing(lang, args.timeout)
            print(f"  [{lang}] filled {filled}, {still_missing} still missing")
            manifest_lines.append(f"- {lang}: per-row retry filled {filled}, "
                                   f"{still_missing} still missing")
        manifest = SYSTEMS / "MANIFEST.md"
        prior = manifest.read_text() if manifest.exists() else "# Collected systems -- exact model + date\n"
        manifest.write_text(prior.rstrip() + "\n\n" + "\n".join(manifest_lines) + "\n")
        print(f"\nRun: .venv312/bin/python paper/experiments/validate_translations.py")
        return

    for lang in LANGS:
        got, method = fetch_lang(lang, args.chunk_size, args.timeout)
        out_path = SYSTEMS / f"gptoss_{lang}.csv"
        with out_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "translation"])
            for rid, text_en in load_prompt_rows(lang):
                w.writerow([rid, got.get(rid, "")])
        missing = sum(1 for rid, _ in load_prompt_rows(lang) if rid not in got)
        print(f"  [{lang}] wrote {out_path.relative_to(REPO)} "
              f"({missing} missing) via {method}")
        manifest_lines.append(f"- {lang}: {method}, {missing} missing, "
                               f"saved to systems/gptoss_{lang}.csv")

    manifest = SYSTEMS / "MANIFEST.md"
    prior = manifest.read_text() if manifest.exists() else "# Collected systems -- exact model + date\n"
    manifest.write_text(prior.rstrip() + "\n\n" + "\n".join(manifest_lines) + "\n")
    print(f"\nRun: .venv312/bin/python paper/experiments/validate_translations.py")


if __name__ == "__main__":
    main()
