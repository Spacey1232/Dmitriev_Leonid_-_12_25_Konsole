#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command>"
    exit 1
fi
command="$1"
if [ ! -f "$command" ]; then
    echo "Error: File '$command' not found"
    exit 1
fi
chmod +x "$command"
sudo cp "$command" /usr/local/bin/
