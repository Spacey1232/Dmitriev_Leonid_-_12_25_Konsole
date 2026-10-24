#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 emulator.py --vfs examples/deep.xml --script examples/stage1.shell --headless
python3 emulator.py --vfs examples/minimal.xml --script examples/stage1.shell --headless
if python3 emulator.py --vfs examples/deep.xml --script examples/missing.shell --headless; then exit 1; fi
