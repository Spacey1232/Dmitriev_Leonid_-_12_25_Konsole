#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Три варианта VFS: пустой, несколько файлов, три уровня каталогов.
for vfs in minimal several deep; do
    python3 emulator.py --vfs "examples/$vfs.xml" --script examples/stage3.shell
done
