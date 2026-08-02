"""The frozen train/dev/test split.

The split is drawn **once, on `id`**, and then fanned out to all five languages.
This is the whole point of the module. The same ticket exists five times, once
per language, under one `id`; splitting rows independently would put the English
copy of a ticket in train and its Sinhala copy in dev, and every score after
that would be measuring memorisation.

Test is the official BANKING77 test file, untouched. Dev is carved out of the
official train file, stratified on the 77-way intent.

Regenerating the split invalidates every result file, because each one stamps
the split sha and the merge step drops rows whose sha does not match the
current manifest. Call `ensure()`, not `build()`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from . import config, data


def _sha(dev_ids: list[int], train_ids: list[int]) -> str:
    """Short digest of split membership. Identity of the split, not of the file."""
    payload = ",".join(map(str, sorted(train_ids))) + "|" + ",".join(map(str, sorted(dev_ids)))
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def build() -> dict:
    """Draw the split from scratch. Only ever called once -- use `ensure()`."""
    english = data.load_language("english", "train")
    test = data.load_language("english", "test")

    splitter = StratifiedShuffleSplit(
        n_splits=1, test_size=config.DEV_SIZE, random_state=config.RANDOM_STATE
    )
    train_pos, dev_pos = next(splitter.split(english, english["category"]))

    train_ids = sorted(english.iloc[train_pos]["id"].astype(int).tolist())
    dev_ids = sorted(english.iloc[dev_pos]["id"].astype(int).tolist())
    test_ids = sorted(test["id"].astype(int).tolist())

    overlap = set(train_ids) & set(dev_ids)
    if overlap:
        raise AssertionError(f"train/dev id overlap: {sorted(overlap)[:10]}")

    return {
        "sha": _sha(dev_ids, train_ids),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "drawn_on": "id, stratified by category (77-way intent), english train file",
        "random_state": config.RANDOM_STATE,
        "counts": {"train": len(train_ids), "dev": len(dev_ids), "test": len(test_ids)},
        "note": (
            "Test ids come from the official BANKING77 test file and are never "
            "used for model selection. Train/dev ids are fanned out to all five "
            "languages by id."
        ),
        "train_ids": train_ids,
        "dev_ids": dev_ids,
        "test_ids": test_ids,
    }


def ensure() -> dict:
    """Load the manifest, drawing it only if it does not exist yet."""
    if config.SPLIT_MANIFEST.exists():
        return json.loads(config.SPLIT_MANIFEST.read_text())

    manifest = build()
    config.SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    config.SPLIT_MANIFEST.write_text(json.dumps(manifest, indent=2))
    return manifest


def sha() -> str:
    return ensure()["sha"]


def get(langs: list[str], portion: str) -> pd.DataFrame:
    """Rows for one split portion across the given languages.

    `portion` is "train", "dev" or "test". Train and dev are both drawn from the
    on-disk train file and separated by id; test is the on-disk test file.
    """
    manifest = ensure()
    if portion == "test":
        return data.load_languages(langs, "test")
    if portion not in {"train", "dev"}:
        raise ValueError(f"portion must be 'train', 'dev' or 'test', got {portion!r}")

    wanted = set(manifest[f"{portion}_ids"])
    df = data.load_languages(langs, "train")
    return df[df["id"].isin(wanted)].reset_index(drop=True)
