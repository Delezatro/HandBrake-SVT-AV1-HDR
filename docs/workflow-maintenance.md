# Workflow maintenance â€” 2026-11-27

## Why failure notifications kept arriving

All five inherited platform workflows scheduled a rebuild every Monday and
Friday, even without repository changes. The Windows source revisions were
already pinned, so these rebuilds did not pick up newer HandBrake or SVT code.
They still picked up changes in the runner's unpinned Rust toolchain.

Windows runs [44772128244](https://github.com/Delezatro/HandBrake-SVT-AV1-HDR/actions/runs/44772128244),
[45248827943](https://github.com/Delezatro/HandBrake-SVT-AV1-HDR/actions/runs/45248827943)
and [46043248711](https://github.com/Delezatro/HandBrake-SVT-AV1-HDR/actions/runs/46043248711)
all failed at the final hb.dll link. Rust's standard library inside static
libdovi referenced `WaitOnAddress`, `WakeByAddressSingle` and `WakeByAddressAll`,
but the Windows system-library list omitted `synchronization`.
The embedded Rust commit `0ef1bc386059596dada8fb65b50425aab2ea637a` identifies
Rust 1.100.0. GUI and release jobs were skipped because they depend on the native
build. This is a build-time linker error, not evidence of a new ISO runtime crash.

## Changes

- Backport the exact one-line [HandBrake upstream fix](https://github.com/HandBrake/HandBrake/commit/19ed158095b6c9f9252e02a90949acb00a6a2608)
  as patch 0008. The existing HandBrake and SVT source pins remain unchanged;
  Dolby Vision support is retained.
- Pin Rust 1.100.0 in `sources.lock.json`, select it explicitly for the native job,
  install its Windows GNU target, and log compiler/Cargo versions.
- Before the full build, compile a tiny Rust synchronization static library and
  link it with MinGW using the system-library list from patched HandBrake.
  This exercises the actual toolchain and catches missing imports early. It is
  a cross-link test, not an executable runtime test. Diagnostics are uploaded
  even if it fails.
- Remove all scheduled builds. Windows retains manual dispatch plus automatic
  builds for changes to its workflow, source lock, patches, scripts, tests or
  Git attributes. Documentation-only changes do not require a Windows build.
- Keep macOS, Ubuntu, Arch and Flatpak as manual-only optional workflows.
  Existing releases and artifacts are not deleted, and GitHub account-wide
  notification preferences are not changed.

## Optional platforms

Ubuntu and Flatpak's November 27 runs clone moving upstream HandBrake master;
patch 0004 no longer applies there. Flatpak previously also failed because its
workflow installs GNOME SDK 49 while the source requests 51. macOS's latest job
was cancelled without a successful build, so no detailed compilation diagnosis
is claimed. Arch succeeded. These are independent platform-maintenance tasks,
not requirements for building or using the Windows package. Making them manual
does not claim their build failures have been fixed.

## Validation

Local validation checks the complete seven-patch Windows series against the
locked HandBrake revision, the SVT archive/API/contrib patch, the build-safety
regression tests, Python syntax, workflow syntax and diff whitespace.
The full Windows Actions build must additionally pass the Rust link preflight,
native and GUI builds, manifest comparison and all six encoder runtime cases.
No new claim is made that the historical ISO access violation is fixed.
