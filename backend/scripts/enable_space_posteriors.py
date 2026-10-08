"""Apply the approved, single-line full-intent-output change to the configured Space."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    repo = "shazan18/Swift-Support-Demo"
    if settings.intent_space_url.rstrip("/") != "https://shazan18-swift-support-demo.hf.space":
        raise RuntimeError("Configured Space differs from the approved destination")
    if not settings.huggingface_token:
        raise RuntimeError("No Hugging Face credential configured")
    api = HfApi(token=settings.huggingface_token)
    head = api.repo_info(repo, repo_type="space").sha
    with TemporaryDirectory(prefix="swift-space-") as directory:
        file = hf_hub_download(repo, "app.py", repo_type="space", revision=head,
                               token=settings.huggingface_token, local_dir=directory)
        source = Path(file).read_text(encoding="utf-8")
    old = 'gr.Label(label="Intent", num_top_classes=5)'
    new = 'gr.Label(label="Intent", num_top_classes=None)'
    if new in source and old not in source:
        print("Full intent output already enabled; no commit needed")
        return
    if source.count(old) != 1:
        raise RuntimeError("Remote source changed; expected single-line patch no longer matches")
    updated = source.replace(old, new)
    result = api.create_commit(
        repo, repo_type="space", parent_commit=head,
        operations=[CommitOperationAdd(path_in_repo="app.py", path_or_fileobj=updated.encode("utf-8"))],
        commit_message="Return all intent probabilities for dynamic ticket urgency",
        commit_description="Remove Gradio's top-five API truncation so the support backend can marginalize all 77 intent probabilities for the ICATC log pool. Model weights and inference remain unchanged.",
    )
    print(f"Updated Space: {result.commit_url}")


if __name__ == "__main__":
    main()
