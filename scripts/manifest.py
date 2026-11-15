"""Record native hashes or verify that GUI sources and hb.dll belong together."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(directory, gui):
    native = json.loads((directory / "build-manifest.json").read_text())
    for key in ("handbrake_commit", "patched_tree", "svt_av1_hdr", "patches"):
        if native[key] != gui[key]:
            raise ValueError(f"GUI/native source mismatch: {key}")
    for name in ("hb.dll", "HandBrakeCLI.exe"):
        if digest(directory / name) != native["binaries"][name]:
            raise ValueError(f"Native binary hash mismatch: {name}")
    return native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    path = args.directory / "build-manifest.json"
    if args.compare:
        verify(args.directory, json.loads(args.compare.read_text()))
        print("GUI/native source tree and binary hashes match")
    else:
        data = json.loads(path.read_text())
        data["binaries"] = {name: digest(args.directory / name) for name in ("hb.dll", "HandBrakeCLI.exe")}
        path.write_text(json.dumps(data, indent=2) + "\n", newline="\n")


if __name__ == "__main__":
    main()
