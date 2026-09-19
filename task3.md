#!/bin/bash

text="$1"
len=${#text}
width=$((len + 2))
border="+$(printf '%*s' "$width" | tr ' ' '-')+"

echo "$border"
echo "| $text |"
echo "$border"
