#!/bin/bash

file="$1"
line=$(head -n 1 "$file")

case "$file" in
    *.py)      [[ "$line" =~ ^[[:space:]]*# ]] ;;
    *.c|*.js)  [[ "$line" =~ ^[[:space:]]*(//|/\*) ]] ;;
    *)         echo "Неподдерживаемый файл"; exit 1 ;;
esac

if [[ $? -eq 0 ]]; then
    echo "Комментарий есть"
else
    echo "Комментария нет"
fi
