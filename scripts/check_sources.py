"""Verify pinned SVT source bytes, integration API and inherited contrib patch."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
from download_toolchain import download

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handbrake", type=Path)
    parser.add_argument("--download", required=True, type=Path)
    args = parser.parse_args()
    lock = json.loads((ROOT / "sources.lock.json").read_text())["svt_av1_hdr"]
    module = (args.handbrake / "contrib/svt-av1/module.defs").read_text()
    assert lock["url"] in module and lock["sha256"] in module
    assert "BUILD_SHARED_LIBS=OFF" in module and "REPRODUCIBLE_BUILDS=ON" in module
    archive = download(lock["url"], args.download, lock["sha256"])
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(archive) as source:
            source.extractall(tmp, filter="data")
        svt = next(Path(tmp).iterdir())
        header = (svt / "Source/API/EbSvtAv1Enc.h").read_text()
        code = (args.handbrake / "libhb/encsvtav1.c").read_text()
        fields = set(re.findall(r"param->(\w+)", code))
        missing = sorted(f for f in fields if not re.search(r"\b" + f + r"\b", header))
        assert not missing, f"Missing configuration fields: {missing}"
        signature = re.search(r"EB_API EbErrorType svt_av1_enc_init_handle\((.*?)\);", header, re.S).group(1)
        assert signature.count(",") == 1, "Expected the current two-argument initialization API"
        assert "VERSION 4.3.0" in (svt / "CMakeLists.txt").read_text()
        settings = (svt / "Source/Lib/Globals/enc_settings.c").read_text()
        assert "TUNE_FILM_GRAIN" in settings and "EB_YUV444" in settings
        assert "ENC_MRS        = -3" in header and "ENC_MRP        = -2" in header
        for patch in sorted((args.handbrake / "contrib/svt-av1").glob("*.patch")):
            subprocess.run(["git", "apply", "--check", "-"], input=patch.read_text().encode(), cwd=svt, check=True)
        print(f"Verified SVT-AV1-HDR 4.3 archive, {len(fields)} configuration fields and contrib patch compatibility")
        print("Structural API checks do not replace compilation or runtime testing.")


if __name__ == "__main__":
    main()
