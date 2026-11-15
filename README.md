# HandBrake-SVT-AV1-HDR
### Windows x64 modernization
The Windows workflow builds a pinned current HandBrake development revision with
SVT-AV1-HDR 4.3 "Crankcase". See [source pins](sources.lock.json) and the
[compatibility and validation report](docs/windows-validation.md).
Run **Windows x64 Build** in Actions, or open a pull request, to build and test
the CLI, native library and .NET 10 GUI together. Download the complete
`HandBrake-Windows-x64` artifact. Builds on main also publish versioned Windows
prereleases. A successful build does **not** verify the reported Blu-ray ISO crash.

For Windows source preparation (also works from PowerShell):
```
python scripts/prepare.py HandBrake --clone --platform windows --require-pinned --manifest build-manifest.json
```
Existing clone destinations are never deleted automatically.

### Purpose of the project
This project contains the patches needed to replace SVT-AV1 with SVT-AV1-HDR inside HandBrake.\
In addition, using GitHub Actions, nightly build of patched executables will be released.
### Instructions to patch/build
* Run ```patch.sh``` on linux. The script will patch the previously cloned HandBrake repo. If you want to also clone it you can use ```--clone``` argument.
* Compile for the desired platform using the commands provided on the HandBrake wiki ([BSD](https://handbrake.fr/docs/en/latest/developer/build-bsd.html), [Linux](https://handbrake.fr/docs/en/latest/developer/build-linux.html), [Mac](https://handbrake.fr/docs/en/latest/developer/build-mac.html), [Windows](https://handbrake.fr/docs/en/latest/developer/build-windows.html))
### Downloads and Build Status
| Operating System  | Download        | Build Status *1 |
| ----------------- | --------------- | ------------- |
| Windows           | [Download](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/releases/tag/win) | [![Windows Build](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-win.yml/badge.svg)](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-win.yml)  |
| macOS             | [Download](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/releases/tag/mac) | [![macOS build](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-mac.yml/badge.svg)](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-mac.yml)  |
| Linux (Flatpak)   | [Download](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/releases/tag/flatpak) | [![Flatpak Build](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-flatpak.yml/badge.svg)](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-flatpak.yml) |
| Ubuntu            | [Download](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/releases/tag/ubuntu) | [![Flatpak Build](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-ubuntu.yml/badge.svg)](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-ubuntu.yml) |
| Arch Linux        | [Download](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/releases/tag/arch) | [![Flatpak Build](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-arch.yml/badge.svg)](https://github.com/Uranite/HandBrake-SVT-AV1-PSY/actions/workflows/nightly-arch.yml) |

*1 Please note that if a build is marked as failed, previous builds may still be available for download!
### Testing
I can currently only test the custom build on Windows. Help for testing on other platforms would be helpful.
### Special thanks
A special thanks to [vincejv (Docker container for HandBrake)](https://github.com/vincejv/docker-handbrake) from which I took inspiration for some patches.

