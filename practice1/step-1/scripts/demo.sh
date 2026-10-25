#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 emulator.py --vfs examples/deep.xml --script examples/stage4.shell
python3 emulator.py --vfs examples/deep.xml --script examples/stage5.shell
