# Windows x64 / SVT-AV1-HDR 4.3

This snapshot contains a matching HandBrake GUI, native library and CLI built from the source revisions in `build-manifest.json`.

- Extract the complete portable ZIP into a fresh directory. Do not replace individual DLLs in an existing installation.
- The GUI requires Microsoft .NET Desktop Runtime 10 x64.
- `sha256.txt` covers the distributed packages; the build manifest records the native binary hashes and patch provenance.
- Automated tests cover synthetic 8/10-bit AV1 encoding, grain tune, research presets, 4:4:4 and static HDR metadata.
- A successful build or synthetic test does not prove the reported Blu-ray ISO crash fixed. See `docs/windows-validation.md` and the PR for the actual regression results and remaining limitations.

Report fork-specific problems to this repository's issue tracker, including the manifest and a full activity log.
