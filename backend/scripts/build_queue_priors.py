"""Export aggregate intent priors from the paper's frozen train+dev split (no test rows)."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ("low", "medium", "high")


def main() -> None:
    manifest = json.loads((ROOT / "ml/splits/split_manifest.json").read_text())
    wanted = set(manifest["train_ids"]) | set(manifest["dev_ids"])
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    totals: Counter[str] = Counter()
    sources = {}
    for language in ("english", "sinhala", "singlish", "tamil", "tamilish"):
        path = ROOT / f"datasets/{language}/train_labeled.csv"
        sources[language] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = [r for r in csv.DictReader(stream) if int(r["id"]) in wanted]
        if len(rows) != len(wanted) or len({r["id"] for r in rows}) != len(wanted):
            raise ValueError(f"Incomplete or duplicated training membership: {language}")
        for row in rows:
            priority = row["priority"].lower()
            if priority not in CLASSES:
                raise ValueError(f"Unknown priority: {priority}")
            counts[row["category"]][priority] += 1
            totals[priority] += 1
    base = {k: totals[k] / totals.total() for k in CLASSES}
    artifact = {
        "version": "icatc-logpool-v1",
        "split": manifest["sha"],
        "source_portions": ["train", "dev"],
        "source_sha256": sources,
        "rows": totals.total(),
        "smoothing": 1.0,
        "base_priority": base,
        # Match policy_bakeoff._conditional_table: one base-rate pseudo-observation.
        "priority_given_intent": {
            intent: {k: (n[k] + base[k]) / (n.total() + 1) for k in CLASSES}
            for intent, n in sorted(counts.items())
        },
        "criticality": {i: n["high"] / n.total() for i, n in sorted(counts.items())},
    }
    target = ROOT / "backend/app/domain/queue_priors.json"
    target.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(counts)} aggregate priors from {totals.total()} train+dev rows")


if __name__ == "__main__":
    main()
