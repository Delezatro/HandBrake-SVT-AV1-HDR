import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare
import manifest


class BuildSafetyTests(unittest.TestCase):
    def test_binary_and_source_mismatches_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("hb.dll", "HandBrakeCLI.exe"):
                (folder / name).write_bytes(b"test fixture")
            source = {"handbrake_commit": "a", "patched_tree": "b", "svt_av1_hdr": {}, "patches": {}}
            native = dict(source, binaries={name: manifest.digest(folder / name) for name in ("hb.dll", "HandBrakeCLI.exe")})
            (folder / "build-manifest.json").write_text(json.dumps(native))
            manifest.verify(folder, source)
            with self.assertRaisesRegex(ValueError, "source mismatch"):
                manifest.verify(folder, dict(source, patched_tree="wrong"))
            (folder / "hb.dll").write_bytes(b"other build")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                manifest.verify(folder, source)

    def test_invalid_second_patch_does_not_partially_modify_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            patches = root / "patches"
            patches.mkdir()
            subprocess.run(["git", "init", str(source)], check=True, stdout=subprocess.DEVNULL)
            (source / "file.txt").write_text("before\n")
            prepare.git(source, "add", ".")
            prepare.git(source, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "fixture")
            (patches / "0001.patch").write_text("diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-before\n+after\n", newline="\n")
            (patches / "0002.patch").write_text("invalid patch\n", newline="\n")
            with patch.object(prepare, "ROOT", root):
                with self.assertRaises(subprocess.CalledProcessError):
                    prepare.prepare(source)
            self.assertEqual((source / "file.txt").read_text(), "before\n")
            self.assertEqual(prepare.git(source, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
