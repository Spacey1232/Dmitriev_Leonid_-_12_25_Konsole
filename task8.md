#!/bin/bash

extension="${1#.}"
files=()

for file in *."$extension"; do
    if [[ -f "$file" ]]; then
        files+=("$file")
    fi
done

if [[ ${#files[@]} -eq 0 ]]; then
    echo "Файлы с расширением .$extension не найдены"
    exit 1
fi

tar -cf archive.tar "${files[@]}"

echo "Создан архив archive.tar"
