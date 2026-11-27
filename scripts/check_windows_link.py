"""Link a Rust synchronization staticlib using HandBrake's Windows system libraries."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUST_SOURCE = r'''
use std::sync::{Condvar, Mutex};

#[no_mangle]
pub extern "C" fn hb_rust_link_probe() -> i32 {
    let mutex = Mutex::new(0);
    let mut value = mutex.lock().unwrap();
    *value += 1;
    Condvar::new().notify_all();
    *value - 1
}
'''
C_SOURCE = "extern int hb_rust_link_probe(void);\nint main(void) { return hb_rust_link_probe(); }\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handbrake", type=Path)
    parser.add_argument("--log", type=Path, default=Path("diagnostics/rust-link.log"))
    args = parser.parse_args()
    lock = json.loads((ROOT / "sources.lock.json").read_text())["rust"]
    module = (args.handbrake / "libhb/module.defs").read_text()
    libraries = re.search(r"^LIBHB\.GCC\.l \+= (bcrypt[^\n]+)$", module, re.M)
    if not libraries:
        raise RuntimeError("Cannot locate HandBrake's MinGW system-library list")
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", encoding="utf-8") as log:
        def run(command):
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, timeout=180)
            log.write("$ " + " ".join(command) + "\n" + result.stdout + "\n")
            log.flush()
            if result.returncode:
                raise RuntimeError(f"Windows Rust link preflight failed; see {args.log}")
            return result.stdout

        version = run(["rustc", "--version"])
        if not version.startswith("rustc " + lock["version"] + " "):
            raise RuntimeError(f"Unexpected Rust toolchain: {version.strip()}")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            rust, driver, library, binary = (path / name for name in
                                             ("probe.rs", "probe.c", "libprobe.a", "probe.exe"))
            rust.write_text(RUST_SOURCE)
            driver.write_text(C_SOURCE)
            run(["rustc", "--edition=2021", "--crate-type=staticlib", "--target", lock["target"],
                 str(rust), "-o", str(library)])
            run(["x86_64-w64-mingw32-gcc", str(driver), str(library), "-o", str(binary),
                 *["-l" + name for name in libraries.group(1).split()]])
    print("Rust staticlib linked with HandBrake's Windows libraries; see", args.log)
    print("This cross-link check does not execute the probe or replace runtime tests.")


if __name__ == "__main__":
    main()
