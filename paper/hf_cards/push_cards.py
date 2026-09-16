"""Push the corrected cards to the Swift-Support org.

Requires authentication first -- there is no token in this repo (it was deliberately
removed), so run one of:

    hf auth login                      # interactive
    export HF_TOKEN=hf_...             # or set the env var

Then:
    .venv312/bin/python paper/hf_cards/push_cards.py --dry-run   # show what would change
    .venv312/bin/python paper/hf_cards/push_cards.py             # actually push

Each push is a separate commit with a message naming what it corrects, so the change is
auditable from the Hub's commit history rather than silently overwriting the old card.
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TARGETS = [
    # (local file, repo_id, repo_type, commit message)
    ("updated_dataset.md", "Swift-Support/swift-support-tickets-1.0", "dataset",
     "Document known issue 5: the tamilish TEST rendering does not match its TRAIN rendering (60.3% OOV vs train, against 20-30% elsewhere). Tamilish test scores are contaminated and must not be read as romanized-Tamil handling."),
    ("updated_intent.md", "Swift-Support/labse-intent-1.0", "model",
     "Add held-out test results (LaBSE 88.35 pooled macro-F1, per-language). Flag the tamilish column as a corpus defect, not a model result: the tamilish test rendering is 60.3% OOV against tamilish train."),
    ("updated_priority.md", "Swift-Support/labse-priority-1.0", "model",
     "Add citation block"),
    ("updated_sentiment.md", "Swift-Support/labse-sentiment-1.0", "model",
     "Correct label ceiling to 0.7931 (shipped labels, not prompt output); add per-language "
     "results and the native-script/romanized gain split; add citation"),
    # An HF *organization card* lives in a Space named "<org>/README", not a model repo.
    # Pushing it as a model silently creates a stray model called "README" and leaves the
    # org page blank, which looks identical to the push having failed.
    ("updated_org.md", "Swift-Support/README", "space",
     "Org card: artifacts, label provenance, metric guidance, licence, citation"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="diff local against live and print, push nothing")
    args = ap.parse_args()

    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    try:
        who = api.whoami()
    except Exception as e:
        sys.exit(f"not authenticated ({type(e).__name__}). Run `hf auth login` "
                 f"or set HF_TOKEN, then re-run.")
    print(f"authenticated as {who.get('name')}\n")

    for fname, repo_id, repo_type, message in TARGETS:
        local = (HERE / fname).read_text()
        try:
            live_path = hf_hub_download(repo_id, "README.md", repo_type=repo_type)
            live = Path(live_path).read_text()
        except Exception:
            live = ""
            if not args.dry_run:
                # The org card Space does not exist until the card is first created.
                # `static` is the sdk an org card uses; anything else renders as an app.
                kw = {"space_sdk": "static"} if repo_type == "space" else {}
                api.create_repo(repo_id, repo_type=repo_type, exist_ok=True,
                                private=False, **kw)
                print(f"  {repo_id}: created ({repo_type})")

        if live == local:
            print(f"  {repo_id}: already up to date")
            continue

        if args.dry_run:
            diff = list(difflib.unified_diff(
                live.splitlines(), local.splitlines(),
                fromfile=f"{repo_id} (live)", tofile=fname, lineterm="", n=1))
            adds = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
            dels = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
            print(f"  {repo_id}: +{adds} / -{dels} lines  [{message}]")
            continue

        api.upload_file(path_or_fileobj=str(HERE / fname), path_in_repo="README.md",
                        repo_id=repo_id, repo_type=repo_type, commit_message=message)
        print(f"  {repo_id}: pushed -- {message}")

    if args.dry_run:
        print("\ndry run: nothing was pushed")


if __name__ == "__main__":
    main()
