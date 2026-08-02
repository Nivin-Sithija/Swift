"""One JSON per run, filename derived from run identity.

Three people run experiments on three machines and the files have to merge in
git without anybody coordinating. So: no shared results table that everyone
appends to (that is a guaranteed conflict), one file per run instead, named
from the run's own identity so two people running the same thing overwrite
rather than duplicate.

Every file stamps the split sha. `load_all()` drops rows whose sha does not
match the current manifest, so a stale result cannot silently enter a
comparison table.
"""
from __future__ import annotations

import json
import platform
import re
from datetime import datetime, timezone

import pandas as pd

from . import config, splits


def _slug(value) -> str:
    if isinstance(value, (list, tuple)):
        value = "+".join(map(str, value))
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def run_id(task: str, model: str, train_langs, eval_lang: str, arm: str) -> str:
    return "__".join(
        [_slug(task), _slug(model), f"tr-{_slug(train_langs)}", f"ev-{_slug(eval_lang)}", f"arm-{_slug(arm)}"]
    )


def save(task: str, model: str, train_langs, eval_lang: str, arm: str,
         portion: str, scores: dict, author: str = "", extra: dict | None = None) -> str:
    """Write one run's result. Returns the path written."""
    manifest = splits.ensure()
    rid = run_id(task, model, train_langs, eval_lang, arm)

    record = {
        "run_id": rid,
        "task": task,
        "model": model,
        "train_langs": list(train_langs) if not isinstance(train_langs, str) else [train_langs],
        "eval_lang": eval_lang,
        "arm": arm,
        "eval_portion": portion,
        "split_sha": manifest["sha"],
        "author": author,
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        **scores,
    }
    if extra:
        record.update(extra)

    out_dir = config.REPORTS_DIR / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{rid}__{portion}.json"
    path.write_text(json.dumps(record, indent=2))
    return str(path)


def load_all(portion: str | None = None) -> pd.DataFrame:
    """Every recorded run, with stale-split rows dropped."""
    out_dir = config.REPORTS_DIR / "runs"
    if not out_dir.exists():
        return pd.DataFrame()

    current = splits.sha()
    records, stale = [], 0
    for path in sorted(out_dir.glob("*.json")):
        record = json.loads(path.read_text())
        if record.get("split_sha") != current:
            stale += 1
            continue
        records.append(record)

    if stale:
        print(f"warning: dropped {stale} result file(s) recorded against a different split sha")

    df = pd.DataFrame(records)
    if portion is not None and not df.empty:
        df = df[df["eval_portion"] == portion]
    return df.reset_index(drop=True)


def leaderboard(task: str, portion: str = "dev") -> pd.DataFrame:
    """Runs for one task, best headline metric first."""
    df = load_all(portion)
    if df.empty:
        return df
    df = df[df["task"] == task]
    if df.empty:
        return df

    cols = ["model", "arm", "train_langs", "eval_lang", "headline", "headline_metric",
            "accuracy", "macro_f1", "n", "author"]
    cols = [c for c in cols if c in df.columns]
    return df[cols].sort_values("headline", ascending=False).reset_index(drop=True)
