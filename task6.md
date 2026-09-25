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
