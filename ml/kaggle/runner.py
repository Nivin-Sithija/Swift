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
    size = sum(f.stat().st_size for f in STAGE.rglob("*") if f.is_file())
    print(f"staged {n} files, {size/1e6:.1f} MB -> {STAGE}")

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

    body = (REPO / "ml" / "kaggle" / "kernels" / f"{args.job}.py").read_text()
    header = (
        "# Generated by ml/kaggle/runner.py -- edit ml/kaggle/kernels/*.py instead.\n"
        f"MODELS = {args.models!r}\n"
        f"TASK = {args.task!r}\n"
        f"EPOCHS = {args.epochs}\n"
        f"BATCH_SIZE = {args.batch_size}\n"
        f"SMOKE = {bool(args.smoke)}\n"
        f"FIT_PORTION = {args.fit_portion!r}\n"
        f"EVAL_PORTION = {args.eval_portion!r}\n"
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


def fetch(args):
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
    r.add_argument("--fit-portion", default="train", choices=["train", "train+dev"],
                   help="'train' while selecting on dev; 'train+dev' for the final test fit")
    r.add_argument("--eval-portion", default="dev", choices=["dev", "test"],
                   help="'dev' for selection; 'test' only for the final, one-shot eval")
    r.add_argument("--smoke", action="store_true", help="1,200-row sanity run")
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
