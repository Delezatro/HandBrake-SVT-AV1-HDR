#!/usr/bin/env python3
"""Apply the patch series without fuzz; preflight before changing source files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "sources.lock.json").read_text())


def git(source, *args, env=None):
    return subprocess.check_output(["git", "-C", str(source), *args], env=env).decode().strip()


def prepare(source, platform="all", require_pinned=False):
    source = Path(source).resolve()
    if git(source, "status", "--porcelain"):
        raise RuntimeError("Source checkout must be clean, including untracked files")
    revision = git(source, "rev-parse", "HEAD")
    if require_pinned and revision != LOCK["handbrake"]["commit"]:
        raise RuntimeError("HandBrake checkout does not match sources.lock.json")
    patches = [p for p in sorted((ROOT / "patches").glob("*.patch"))
               if platform != "windows" or not p.name.startswith("0005-")]
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        git(source, "read-tree", "HEAD", env=env)
        for patch in patches:
            git(source, "apply", "--cached", "--whitespace=error-all", str(patch), env=env)
        expected_tree = git(source, "write-tree", env=env)
    for patch in patches:
        git(source, "apply", "--whitespace=error-all", str(patch))
    return {
        "handbrake_commit": revision,
        "patched_tree": expected_tree,
        "svt_av1_hdr": LOCK["svt_av1_hdr"],
        "patches": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in patches},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="HandBrake")
    parser.add_argument("--platform", choices=["windows", "all"], default="all")
    parser.add_argument("--require-pinned", action="store_true")
    parser.add_argument("--clone", "-c", action="store_true")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.clone:
        if Path(args.source).exists():
            parser.error("Clone destination already exists; refusing to delete it")
        subprocess.run(["git", "clone", "https://github.com/HandBrake/HandBrake.git", args.source], check=True)
        git(args.source, "checkout", "--detach", LOCK["handbrake"]["commit"])
    result = prepare(args.source, args.platform, args.require_pinned)
    payload = json.dumps(result, indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(payload, newline="\n")
    print(payload)


if __name__ == "__main__":
    main()
