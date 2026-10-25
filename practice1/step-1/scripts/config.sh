#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Все два параметра командной строки; окна закрываются командой exit.
python3 emulator.py --vfs examples/deep.xml --script examples/stage1.shell
python3 emulator.py --vfs examples/several.xml --script examples/stage3.shell
# Ожидаемые ошибки запуска.
if python3 emulator.py --vfs examples/missing.xml --script examples/stage1.shell; then exit 1; fi
if python3 emulator.py --vfs examples/deep.xml --script examples/missing.shell; then exit 1; fi
