#!/bin/bash

directory="$1"

find "$directory" -maxdepth 1 -type f -name "*.txt" -empty
