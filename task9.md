#!/bin/bash

input="$1"
output="$2"

sed $'s/    /\t/g' "$input" > "$output"
