#!/bin/bash

# Usage: ./copy_script.sh input.txt /full/path/to/remove

INPUT_FILE=$1             # Text file with full file paths
STRIP_PREFIX=$2           # Folder prefix to remove from the path
DEST_DIR="/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/cap/data-capability/wd/raw_docs_out/www_stats_gov_sa"

# Ensure destination directory exists
mkdir -p "$DEST_DIR"

while IFS= read -r filepath; do
    if [[ -f "$filepath" ]]; then
        # Remove the prefix path
        relative_path="${filepath#$STRIP_PREFIX/}"

        # Create the directory structure in DEST_DIR without the stripped prefix
        dest_path="$DEST_DIR/$relative_path"
        mkdir -p "$(dirname "$dest_path")"

        # Copy the file to the new location
        cp "$filepath" "$dest_path"
    else
        echo "File not found: $filepath"
    fi
done < "$INPUT_FILE"