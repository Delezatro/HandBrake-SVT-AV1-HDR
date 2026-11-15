#!/usr/bin/env bash
set -euo pipefail
BASEDIR=$(cd -- "$(dirname -- "$0")" && pwd)
python3 "$BASEDIR/scripts/prepare.py" "$@"
# Flatpak consumes the current commit. Windows calls prepare.py directly.
src_dir=HandBrake
for arg in "$@"; do
    case "$arg" in
        -h|--help) exit 0 ;;
        -*) ;;
        *) src_dir=$arg ;;
    esac
done
git -C "$src_dir" add -u
git -C "$src_dir" -c user.name='HandBrake HDR build' -c user.email='build@localhost' commit -m 'Apply SVT-AV1-HDR patches'
