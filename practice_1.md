cd \etc
sort passwd | cut -d':' -f1

cat protocols | awk '{print $2,$1}' | sort -nr | head -n 5

#!/bin/bash

text="$1"
len=${#text}
width=$((len + 2))
border="+$(printf '%*s' "$width" | tr ' ' '-')+"

echo "$border"
echo "| $text |"
echo "$border"

grep -oE '[a-zA-Z_][a-zA-Z0-9_]*' "$1" | sort -u  | tr '\n' ' '

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


#!/bin/bash

file="$1"
line=$(head -n 1 "$file")

case "$file" in
    *.py)
        if [[ "$line" == *"#"* ]]; then
            echo "Комментарий есть"
        else
            echo "Комментария нет"
        fi
        ;;

    *.c|*.js)
        if [[ "$line" == *"//"* || "$line" == *"/*"* ]]; then
            echo "Комментарий есть"
        else
            echo "Комментария нет"
        fi
        ;;

    *)
        echo "Неподдерживаемое расширение файла"
        ;;
esac

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

#!/bin/bash

input="$1"
output="$2"

sed $'s/    /\t/g' "$input" > "$output"

#!/bin/bash

directory="$1"

find "$directory" -maxdepth 1 -type f -name "*.txt" -empty

