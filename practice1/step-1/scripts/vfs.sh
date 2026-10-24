#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
for vfs in minimal several deep; do
  python3 emulator.py --vfs "examples/$vfs.xml" --script examples/stage1.shell --headless
done
if python3 emulator.py --vfs examples/missing.xml --headless; then exit 1; fi
