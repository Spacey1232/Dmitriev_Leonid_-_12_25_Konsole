#!/bin/bash

path="$1"
files=()

while IFS= read -r file; do
    files+=("$file")
done < <(find "$path" -type f)

found=0

for ((i=0; i<${#files[@]}; i++)); do
    for ((j=i+1; j<${#files[@]}; j++)); do
        if cmp -s "${files[i]}" "${files[j]}"; then
            echo "Найдены дубликаты:"
            echo "${files[i]}"
            echo "${files[j]}"
            echo
            found=1
        fi
    done
done

if [[ $found -eq 0 ]]; then
    echo "Дубликаты не найдены"
fi
