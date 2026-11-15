# Windows x64 / SVT-AV1-HDR 4.3

## Sources and compatibility

The Windows workflow builds HandBrake's official development revision
`340f98da51ca335ba896c6064b8eaa4aa2d75312` (master on 2026-11-15).
`sources.lock.json` is the update point. Scheduled builds deliberately rebuild
that reviewed revision; they do not silently move to a new upstream commit.
When updating it, rebase the patches and rerun the build and runtime checks.

SVT-AV1-HDR is pinned to `f5df03be4c2087991d2cbd465874161a64dad6b4`,
4.3 "Crankcase", with archive SHA-256
`12d65b030f8870357195204c661d44e8b5959ff6a77ff0efb53600d8bdf53a3c`.
The archive was downloaded and its digest calculated locally.
The upstream README still says Vendata; the pinned commit message identifies
Crankcase and CMake declares 4.3.0.

The source patch replaces both stock SVT URLs and their checksum. No fallback
to the stock encoder is possible. HandBrake builds SVT statically, with its own
matching headers and `REPRODUCIBLE_BUILDS=ON`. This pins the source inputs, not
bit-for-bit reproducibility of the entire executable (runner images, .NET
servicing and distribution packages can change).

The Windows build uses the official HandBrake x64 GCC/MinGW UCRT toolchain
12.0.0 instead of the previous LLVM/MSVCRT toolchain, with the release asset's
SHA-256 enforced. GUI publishing uses upstream's .NET 10 profiles and build.xml.
FFmpeg 9.0.2 and other native dependencies come from this HandBrake revision's
contrib definitions and checksums. No old native build directory or compiler
cache is restored. This workflow targets x64; ARM64 builds are outside this
validation and are no longer coupled to the x64 release job.

## Patch inventory

| Patch | Behavior |
| --- | --- |
| 0001 | Grain tune maps to SVT tune 6, alongside the current upstream tunes |
| 0002 | Additional research presets -2 and -3 |
| 0003 | HDR encoder display names; stable preset/CLI encoder IDs retained |
| 0004 | Commit-addressed HDR 4.3 archive and verified SHA-256 |
| 0005 | Existing Flatpak network permission; excluded from Windows |
| 0006 | Retains chapter queueing without forcing keyframes at chapter boundaries |
| 0007 | High profile selects planar 4:4:4 at 8 or 10 bits and EB_YUV444 |

All patches were regenerated against the selected upstream revision.
The existing HDR10, HDR10+ and Dolby Vision metadata paths are retained.
SVT's two-argument initialization API and all 24 configuration fields accessed
through `param` in encsvtav1.c were checked against the archive. Its validation
accepts tune 6, presets -2/-3, and 4:4:4 High profile. The existing HandBrake
SVT contrib ARM feature-detection patch also passes `git apply --check` against
the HDR archive. The generic plane-size and byte-to-sample stride handling in
current encsvtav1.c already accommodates 4:4:4 and 10-bit input.

## Avoiding mixed builds

Both jobs check out the same locked HandBrake commit and apply the same ordered
Windows patch series. Preparation preflights the complete series against a
temporary Git index before touching the working tree. It rejects dirty checkouts
and, in Windows CI, an unexpected upstream commit.

The native artifact contains the source commit, patched Git tree, patch hashes,
SVT pin and hashes of hb.dll and HandBrakeCLI.exe. The GUI job compares its own
source manifest, verifies both native binaries and checks the packaged hb.dll
again after publishing. Artifacts are downloaded from the same workflow run.
The portable package includes the manifest and CLI; installer and ZIP come
from the same publish directory. Do not replace individual DLLs in an existing
installation: extract the complete portable package into a new directory.

## Validation status

Locally passed:

- Exact application of the six Windows patches on the pinned clean checkout.
- SVT archive SHA-256, configuration-field/signature checks, version check,
  and inherited contrib patch applicability.
- Two regression tests: rejecting mismatched sources or native hashes, and
  failing a broken patch series without partially modifying the source checkout.
- `git diff --check`.

The Actions workflow additionally runs the native cross-build, GUI/installer
build, packaged-DLL API check, and six short synthetic encodes: 4:2:0 8-bit
with grain tune, 4:2:0 10-bit, 4:4:4 8-bit, 4:4:4 10-bit with PQ/BT.2020 and
static HDR metadata, and research presets -2 and -3. ffprobe checks AV1 profile,
pixel format, frame count and HDR metadata; ffmpeg decodes every output.
Logs and results are uploaded, including on failures. A green build must be
checked for the runtime job too; see the PR for observed CI results.

Not established by these tests: interactive GUI source opening, hardware
decoding/encoding on real GPUs, HDR10+/Dolby Vision end-to-end passthrough,
visual quality, long encodes, non-Windows builds, or the original ISO regression.

## Required original-ISO regression

The reported 2026-10-30 crash is `0xC0000005` in hb.dll at
`ff_nv12ToUV_avx+0x2d`, with a source pointer into MEM_FREE. That is a frame
conversion/read failure; the report alone does not establish whether the cause
was frame lifetime, an upstream bug, toolchain behavior or mismatched components.
Updating the code/toolchain and enforcing matching components are not proof of
a fix. No AVX-disable workaround or speculative FFmpeg memory patch is applied.

1. Record SHA-256 of the affected ISO, Windows version, CPU/GPU and drivers,
   exact official Nightly version, and the new package's build manifest.
2. Extract the entire new portable ZIP into a fresh directory. Open the same
   ISO in the GUI, scan all titles and preview the title that previously failed.
3. Repeat the scan with the same hardware-decoding setting as the failing build,
   then with hardware decoding disabled. Save both full activity logs.
4. Encode a representative segment with SVT 8-bit and 10-bit, then exercise
   grain and High/4:4:4 with suitable sources. Check output decoding and metadata.
5. Compare with the working official Nightly under the same settings. On a
   crash retain the full dump, loaded-module list, package hashes and log.

Until that test is completed, the ISO crash remains **unverified**.
