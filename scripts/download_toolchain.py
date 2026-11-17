"""Download and verify the toolchain selected in sources.lock.json."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import urllib.request


def download(url, target, expected):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(f"Downloading {url}", flush=True)
        with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
    with target.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {target}: {actual}")
    print(f"SHA-256 verified: {target} ({actual})", flush=True)
    return target


if __name__ == "__main__":
    lock = json.loads((Path(__file__).resolve().parents[1] / "sources.lock.json").read_text())
    toolchain = lock["windows_x64_toolchain"]
    destination = Path(sys.argv[1])
    archive = download(toolchain["url"], destination / "toolchain.tar.gz", toolchain["sha256"])
    with tarfile.open(archive) as source:
        source.extractall(destination, filter="data")
    cargo = lock["cargo_c"]
    archive = download(cargo["url"], destination / "cargo-c.tar.gz", cargo["sha256"])
    with tarfile.open(archive) as source:
        source.extractall(destination / "cargo-c", filter="data")
