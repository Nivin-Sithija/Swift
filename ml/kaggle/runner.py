#!/usr/bin/env python
"""Run Swift training on Kaggle's T4 GPUs from inside this project.

The encoder roster costs ~12 hours on local MPS (measured: 24.1 rows/s for xlm-roberta-base).
Kaggle gives two T4s and ~30 GPU-hours a week. This drives them from here, so the edit-run-read
loop stays in the editor.

    python ml/kaggle/runner.py sync                    # upload code + data as a Kaggle Dataset
    python ml/kaggle/runner.py run --models xlmr-base  # push a GPU kernel and start it
    python ml/kaggle/runner.py status                  # poll
    python ml/kaggle/runner.py fetch                   # pull results back into ml/reports/runs/
    python ml/kaggle/runner.py logs                    # print the kernel log

**Why the Kernels API rather than an SSH tunnel.** Reverse-tunnelling out of a Kaggle session to
attach a local IDE breaks Kaggle's Terms of Service, and accounts do get suspended for it. The
Kernels API is the supported route and gets you the same thing: you edit locally, it executes on
their T4s, results land back in `ml/reports/`. The only thing you give up is an interactive
debugger on the remote box -- so `--smoke` runs the identical code path on a small subsample
first, which is what an interactive session would mostly have been used for anyway.

Setup once:
  1. kaggle.com -> your profile -> Settings -> API -> "Create New Token"
  2. mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json
  3. python ml/kaggle/runner.py doctor
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STAGE = REPO / "ml" / "kaggle" / ".stage"
OUT = REPO / "ml" / "kaggle" / ".output"

# Everything the kernel needs, mirroring the repo layout so SWIFT_REPO_ROOT just works.
PAYLOAD = [
    ("datasets", "datasets", {".csv"}),
    ("ml/swiftbench", "ml/swiftbench", {".py"}),
    ("ml/splits", "ml/splits", {".json"}),
]


def sh(cmd: list[str], check=True, capture=False) -> subprocess.CompletedProcess:
    """Run a command with the venv's kaggle CLI on PATH."""
    env = dict(os.environ)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    return subprocess.run(cmd, check=check, env=env, text=True,
                          capture_output=capture)


_USERNAME: str | None = None


def username() -> str:
    """Resolve the Kaggle username under either auth method.

    Two are supported: the classic `kaggle.json` (username + key) and the newer
    `~/.kaggle/access_token` (`KGAT_...`), where the username is not in the file and has to come
    back from the API.
    """
    global _USERNAME
    if _USERNAME:
        return _USERNAME
    if os.environ.get("KAGGLE_USERNAME"):
        _USERNAME = os.environ["KAGGLE_USERNAME"]
        return _USERNAME
    for p in (Path.home() / ".kaggle" / "kaggle.json",
              Path(os.environ.get("KAGGLE_CONFIG_DIR", "/nonexistent")) / "kaggle.json"):
        if p.exists():
            _USERNAME = json.loads(p.read_text())["username"]
            return _USERNAME
    try:  # access-token auth: ask the API who we are
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        name = api.get_config_value("username")
        if name:
            _USERNAME = name
            return _USERNAME
    except Exception:
        pass
    sys.exit("No Kaggle credentials. See the setup steps at the top of this file.")


def slug(kind: str) -> str:
    return f"{username()}/swift-{kind}"


# ------------------------------------------------------------------ doctor
def doctor(_args):
    print(f"repo            {REPO}")
    ok = True
    kdir = Path.home() / ".kaggle"
    found = [p for p in (kdir / "kaggle.json", kdir / "access_token") if p.exists()]
    if found:
        for p in found:
            mode = oct(p.stat().st_mode)[-3:]
            print(f"credentials     {p} (mode {mode})")
            if mode != "600":
                print(f"                -> chmod 600 {p}")
    else:
        print(f"credentials     MISSING -- expected {kdir}/kaggle.json or {kdir}/access_token")
        ok = False
    try:
        r = sh(["kaggle", "--version"], capture=True)
        print(f"kaggle CLI      {r.stdout.strip()}")
    except FileNotFoundError:
        print("kaggle CLI      MISSING -> pip install kaggle")
        ok = False
    if ok:
        try:
            sh(["kaggle", "datasets", "list", "-m", "--page-size", "1"], capture=True)
            print(f"auth            OK as {username()}")
        except subprocess.CalledProcessError as e:
            print("auth            FAILED -- token may be revoked; create a new one")
            ok = False
    n = sum(len(list((REPO / src).rglob(f"*{e}"))) for src, _, exts in PAYLOAD for e in exts)
    print(f"payload         {n} files across {len(PAYLOAD)} trees")
    print("\nready" if ok else "\nnot ready -- fix the items above")
    return 0 if ok else 1


# ------------------------------------------------------------------ sync
def stage_payload(with_metadata: bool = True) -> Path:
    """Copy the payload into .stage/, mirroring repo layout so SWIFT_REPO_ROOT resolves.

    `with_metadata=False` skips the manifest, which is the only part needing credentials --
    that keeps staging verifiable before a token exists.
    """
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    n = 0
    for src, dst, exts in PAYLOAD:
        for f in (REPO / src).rglob("*"):
            if f.is_file() and f.suffix in exts and "__pycache__" not in f.parts:
                target = STAGE / dst / f.relative_to(REPO / src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
                n += 1
    if with_metadata:
        # isPrivate is explicit rather than relying on the CLI default -- this payload is the
        # project's own dataset and translations, and it should not become public by accident.
        (STAGE / "dataset-metadata.json").write_text(json.dumps({
            "title": "swift-payload",
            "id": slug("payload"),
            "isPrivate": True,
            "licenses": [{"name": "unknown"}],
        }, indent=2))
    # Stamp the payload with a content hash. Kaggle takes a minute or two to process a new dataset
    # version, and a kernel pushed inside that window silently attaches the *previous* version --
    # it runs old code, fails against line numbers that no longer exist, and the traceback looks
    # like a bug in the current source. That cost a GPU session and a wrong diagnosis once. The
    # kernel now asserts this hash matches what the runner staged, so a stale attach fails loudly
    # in seconds instead of misleading quietly.
    # Lives under ml/splits/ rather than the stage root because that tree is already located
    # reliably by `find_swiftbench`; a root-level file's landing place depends on how Kaggle
    # expands the upload.
    stamp_path = STAGE / "ml" / "splits" / "payload_stamp.json"
    h = hashlib.sha256()
    for f in sorted(p for p in STAGE.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(STAGE)).encode())
        h.update(f.read_bytes())
    stamp = h.hexdigest()[:12]
    stamp_path.write_text(json.dumps({"sha": stamp}, indent=2))

    size = sum(f.stat().st_size for f in STAGE.rglob("*") if f.is_file())
    print(f"staged {n} files, {size/1e6:.1f} MB -> {STAGE}  (payload sha {stamp})")

    # The kernel asserts these exist; catching it here costs nothing and saves a GPU session.
    missing = [l for l in ("english", "sinhala", "singlish", "tamil", "tamilish")
               if not (STAGE / "datasets" / l / "train_labeled.csv").exists()
               or not (STAGE / "datasets" / l / "test_labeled.csv").exists()]
    if missing:
        sys.exit(f"payload incomplete -- missing train/test CSVs for: {missing}")
    if not (STAGE / "ml" / "splits" / "split_manifest.json").exists():
        sys.exit("payload incomplete -- ml/splits/split_manifest.json missing; "
                 "without it the kernel would redraw the split and every result would be dropped")
    print("payload check OK: 5 languages x train/test, plus the frozen split manifest")
    return STAGE


def sync(args):
    stage_payload()
    exists = sh(["kaggle", "datasets", "status", slug("payload")],
                check=False, capture=True).returncode == 0
    if exists and not args.new:
        print(f"versioning existing dataset {slug('payload')}")
        sh(["kaggle", "datasets", "version", "-p", str(STAGE),
            "-m", args.message, "--dir-mode", "zip"])
    else:
        print(f"creating dataset {slug('payload')}")
        sh(["kaggle", "datasets", "create", "-p", str(STAGE), "--dir-mode", "zip"])
    print("\nKaggle takes a minute or two to finish processing before a kernel can attach it.")
    return 0


# ------------------------------------------------------------------ run
def write_kernel(args) -> Path:
    """Render the kernel script and its metadata into .stage/kernel/."""
    kdir = REPO / "ml" / "kaggle" / ".stage_kernel"
    if kdir.exists():
        shutil.rmtree(kdir)
    kdir.mkdir(parents=True)

    # The sha the last `sync` staged. The kernel refuses to run against anything else, which is
    # what catches a dataset version that Kaggle has not finished processing yet.
    stamp_file = STAGE / "ml" / "splits" / "payload_stamp.json"
    if not stamp_file.exists():
        sys.exit("no payload stamp in .stage/ -- run `runner.py sync` first")
    expected_sha = json.loads(stamp_file.read_text())["sha"]

    body = (REPO / "ml" / "kaggle" / "kernels" / f"{args.job}.py").read_text()
    header = (
        "# Generated by ml/kaggle/runner.py -- edit ml/kaggle/kernels/*.py instead.\n"
        f"MODELS = {args.models!r}\n"
        f"TASK = {args.task!r}\n"
        f"EPOCHS = {args.epochs}\n"
        f"BATCH_SIZE = {args.batch_size}\n"
        f"LR = {args.lr!r}\n"
        f"LORA = {bool(args.lora)!r}\n"
        f"LORA_R = {args.lora_r}\n"
        f"LORA_ALPHA = {args.lora_alpha}\n"
        f"LORA_TARGETS = {args.lora_targets!r}\n"
        f"SMOKE = {bool(args.smoke)}\n"
        f"FIT_PORTION = {args.fit_portion!r}\n"
        f"EVAL_PORTION = {args.eval_portion!r}\n"
        f"SAVE_MODELS = {bool(args.save_models)!r}\n"
        f"EXPECTED_PAYLOAD_SHA = {expected_sha!r}\n"
        f"DATASET_DIR = '/kaggle/input/swift-payload'\n\n"
    )
    (kdir / "swift_job.py").write_text(header + body)
    (kdir / "kernel-metadata.json").write_text(json.dumps({
        "id": slug(f"job-{args.job.replace('_', '-')}"),
        "title": f"swift-job-{args.job.replace('_', '-')}",
        "code_file": "swift_job.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        # Pin the T4 explicitly. Without this Kaggle may assign a P100 (sm_60), and the current
        # Kaggle image ships torch built only for sm_70+ -- on a P100 every CUDA kernel fails with
        # "no kernel image is available for execution on the device". Kaggle's own kernel-metadata
        # docs flag P100 as incompatible with the default image and recommend NvidiaTeslaT4.
        "machine_shape": "NvidiaTeslaT4",
        "enable_internet": True,          # needed to pull HF checkpoints
        "dataset_sources": [slug("payload")],
        "competition_sources": [],
        "kernel_sources": [],
    }, indent=2))
    return kdir


def run(args):
    kdir = write_kernel(args)
    print(f"pushing kernel {slug(f'job-{args.job}')}  models={args.models} smoke={bool(args.smoke)}")
    sh(["kaggle", "kernels", "push", "-p", str(kdir)])
    print("\nRunning. Poll with:  python ml/kaggle/runner.py status")
    print("Kaggle kernels are capped at 12h; keep each job under that.")
    return 0


def status(args):
    r = sh(["kaggle", "kernels", "status", slug(f"job-{args.job.replace('_','-')}")],
           check=False, capture=True)
    print((r.stdout or r.stderr).strip())
    if args.watch:
        while "running" in (r.stdout or "").lower() or "queued" in (r.stdout or "").lower():
            time.sleep(args.interval)
            r = sh(["kaggle", "kernels", "status", slug(f"job-{args.job.replace('_','-')}")],
                   check=False, capture=True)
            print(time.strftime("%H:%M:%S"), (r.stdout or r.stderr).strip())
    return 0


def label_names(task: str) -> list[str] | None:
    """The label order for `task`, read from swiftbench so there is one source of truth."""
    sys.path.insert(0, str(REPO / "ml"))
    try:
        from swiftbench import config as c
    except Exception:
        return None
    return {"sentiment": c.SENTIMENT_LABELS, "priority": c.PRIORITY_LABELS}.get(task)


def stamp_labels(d: Path) -> str:
    """Write id2label/label2id into a checkpoint config that lacks them.

    Checkpoints trained before 2026-08-07 were saved without a label mapping, so they load as
    LABEL_0/LABEL_1 and the caller has no way to tell which index means "Negative". Guessing wrong
    inverts predictions silently. `train_encoder.py` now embeds this at save time; this repairs the
    older artifacts, and re-applies after `fetch` replaces a directory wholesale.
    """
    cfg = d / "config.json"
    if not cfg.exists():
        return "no config.json"
    c = json.loads(cfg.read_text())
    labels = label_names(d.name.split("_")[0])
    if not labels:
        return "unknown task, left as-is"
    have = c.get("id2label") or {}
    if have and not any(str(v).startswith("LABEL_") for v in have.values()):
        return f"already labelled {list(have.values())}"
    if len(have) not in (0, len(labels)):
        return f"class count {len(have)} != {len(labels)}, left as-is"
    c["id2label"] = {str(i): l for i, l in enumerate(labels)}
    c["label2id"] = {l: i for i, l in enumerate(labels)}
    cfg.write_text(json.dumps(c, indent=2))
    return f"stamped {labels}"


def fetch(args):
    # Cleared first, every time. The Kaggle CLI only writes the files the *current* kernel run
    # produced, so anything left from a previous run survives -- and a run that died before writing
    # its summary leaves the previous run's `encoder_summary.csv` sitting there looking current.
    # That is indistinguishable from a fresh result and it read as a repeat failure once.
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    sh(["kaggle", "kernels", "output", slug(f"job-{args.job.replace('_','-')}"),
        "-p", str(OUT)])
    runs = REPO / "ml" / "reports" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in OUT.rglob("*.json"):
        if f.name.endswith("__dev.json") or f.name.endswith("__test.json"):
            shutil.copy2(f, runs / f.name)
            moved += 1
    for f in OUT.rglob("*.csv"):
        shutil.copy2(f, REPO / "ml" / "reports" / f.name)
    print(f"pulled {moved} run file(s) into ml/reports/runs/")

    models_out = REPO / "ml" / "models" / "encoders"
    saved = 0
    for d in OUT.rglob("models/*"):
        # `config.json` for a full fine-tune, `adapter_config.json` for a LoRA run -- peft's
        # `save_pretrained` writes only the adapter, and gating on `config.json` alone silently
        # skipped every LoRA checkpoint: the kernel saved it, the fetch reported nothing, and the
        # weights were lost with the Kaggle session.
        if d.is_dir() and ((d / "config.json").exists()
                           or (d / "adapter_config.json").exists()):
            dest = models_out / d.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(d, dest)
            saved += 1
            print(f"  {dest.name}: {stamp_labels(dest)}")
    if saved:
        print(f"pulled {saved} model checkpoint(s) into ml/models/encoders/")

    print(f"raw output in {OUT}")
    return 0


def logs(args):
    for f in sorted(OUT.rglob("*.log")) + sorted(OUT.rglob("*.txt")):
        print(f"--- {f.name} ---")
        print(f.read_text()[-8000:])
    if not list(OUT.rglob("*")):
        print("nothing fetched yet -- run `fetch` first")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="check credentials and payload").set_defaults(fn=doctor)

    s = sub.add_parser("sync", help="upload code+data as a Kaggle Dataset")
    s.add_argument("-m", "--message", default="swift payload update")
    s.add_argument("--new", action="store_true", help="create instead of versioning")
    s.set_defaults(fn=sync)

    r = sub.add_parser("run", help="push and start a GPU kernel")
    r.add_argument("--job", default="train_encoders")
    r.add_argument("--models", default="xlmr-base,mmbert,labse",
                   help="comma-separated, from swiftbench.train_encoder.ENCODERS")
    r.add_argument("--task", default="sentiment")
    r.add_argument("--epochs", type=int, default=3)
    r.add_argument("--batch-size", type=int, default=32)
    r.add_argument("--lr", type=float, default=None,
                   help="learning rate; default None lets train_encoder pick (2e-5 full FT). "
                        "Decoder SLMs with LoRA want ~1e-4 -- ENCODER_FINDINGS.md §4's LoRA "
                        "failure was run at the encoder's 2e-5 and is not evidence against LoRA")
    r.add_argument("--lora", action="store_true",
                   help="freeze the backbone, train low-rank adapters + head (required for the "
                        "decoder SLMs -- full fine-tuning a 1B model does not fit a T4)")
    r.add_argument("--lora-r", type=int, default=8,
                   help="rank; arXiv:2606.08051 measured r=8 within 0.2 F1 of r=32")
    r.add_argument("--lora-alpha", type=int, default=16)
    r.add_argument("--lora-targets", default="attn", choices=["attn", "all"],
                   help="which modules get adapters. 'attn' = Q/V only; 'all' adds K/O and the MLP "
                        "projections, which is what arXiv:2606.08051's recipe specifies. On Gemma 3 "
                        "'attn' reaches only 2 of 7 projections. No effect on the encoders.")
    r.add_argument("--fit-portion", default="train", choices=["train", "train+dev"],
                   help="'train' while selecting on dev; 'train+dev' for the final test fit")
    r.add_argument("--eval-portion", default="dev", choices=["dev", "test"],
                   help="'dev' for selection; 'test' only for the final, one-shot eval")
    r.add_argument("--smoke", action="store_true", help="1,200-row sanity run")
    r.add_argument("--save-models", action="store_true",
                   help="write best-epoch weights to /kaggle/working/models/ (downloadable "
                        "kernel output) -- off by default, a full roster run would otherwise "
                        "write a checkpoint per candidate")
    r.set_defaults(fn=run)

    st = sub.add_parser("status", help="poll kernel status")
    st.add_argument("--job", default="train_encoders")
    st.add_argument("--watch", action="store_true")
    st.add_argument("--interval", type=int, default=60)
    st.set_defaults(fn=status)

    f = sub.add_parser("fetch", help="download outputs into ml/reports/")
    f.add_argument("--job", default="train_encoders")
    f.set_defaults(fn=fetch)

    lg = sub.add_parser("logs", help="print fetched logs")
    lg.add_argument("--job", default="train_encoders")
    lg.set_defaults(fn=logs)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
