"""Loading the five language folders under one schema.

Every `datasets/<lang>/{train,test}_labeled.csv` holds the same 3,079 test and
9,998 train tickets, translated. `id` is the alignment key: the same `id` is the
same ticket in all five files, and sentiment/priority are labeled once in
English and copied across, so they are identical for a given `id` everywhere.

That is exactly why splitting has to happen on `id` and not on rows -- see
`splits.py`.
"""
from __future__ import annotations

import pandas as pd

from . import config


def load_language(lang: str, portion: str) -> pd.DataFrame:
    """Load one language/portion, validated against the frozen schema."""
    if lang not in config.LANGUAGES:
        raise ValueError(f"unknown language {lang!r}; expected one of {config.LANGUAGES}")
    if portion not in {"train", "test"}:
        raise ValueError(f"portion must be 'train' or 'test', got {portion!r}")

    path = config.DATASETS_DIR / lang / f"{portion}_labeled.csv"
    df = pd.read_csv(path)

    missing = [c for c in config.SCHEMA if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path} is missing columns {missing}. Expected the frozen schema "
            f"{config.SCHEMA}. If the CSVs were renamed, update "
            f"config.TASK_LABEL_COLUMN rather than patching call sites."
        )

    df = df[config.SCHEMA].copy()
    df["language"] = lang
    df["text"] = df["text"].astype(str).str.strip()
    return df


def load_languages(langs: list[str], portion: str) -> pd.DataFrame:
    """Concatenate several languages. Rows are stacked, `id` repeats across them."""
    return pd.concat(
        [load_language(lang, portion) for lang in langs], ignore_index=True
    )


def label_column(task: str) -> str:
    """Map a task name to the CSV column that holds its label."""
    try:
        return config.TASK_LABEL_COLUMN[task]
    except KeyError:
        raise ValueError(
            f"unknown task {task!r}; expected one of {sorted(config.TASK_LABEL_COLUMN)}"
        ) from None


def xy(df: pd.DataFrame, task: str) -> tuple[pd.Series, pd.Series]:
    """Split a frame into (text, label) for a task."""
    return df[config.TEXT_COLUMN], df[label_column(task)]


def check_alignment() -> pd.DataFrame:
    """Verify sentiment/priority really are id-identical across all five languages.

    Returns one row per language with the mismatch counts against English. Any
    nonzero count means the copy-across-languages invariant has been broken and
    no result computed on top of it is trustworthy.
    """
    rows = []
    for portion in ("train", "test"):
        base = load_language("english", portion).set_index("id")
        for lang in config.LANGUAGES:
            if lang == "english":
                continue
            other = load_language(lang, portion).set_index("id")
            common = base.index.intersection(other.index)
            rows.append(
                {
                    "portion": portion,
                    "language": lang,
                    "ids_in_common": len(common),
                    "ids_only_in_english": len(base.index.difference(other.index)),
                    "ids_only_in_other": len(other.index.difference(base.index)),
                    "category_mismatch": int(
                        (base.loc[common, "category"] != other.loc[common, "category"]).sum()
                    ),
                    "sentiment_mismatch": int(
                        (base.loc[common, "sentiment"] != other.loc[common, "sentiment"]).sum()
                    ),
                    "priority_mismatch": int(
                        (base.loc[common, "priority"] != other.loc[common, "priority"]).sum()
                    ),
                }
            )
    return pd.DataFrame(rows)
