#!/bin/bash

# Function to add header to Python files in a folder
add_header_to_files() {
    local folder="$1"
    local header="$2"
    
    # Iterate over all files in the folder
    while IFS= read -r -d '' file; do
        # Check if the file is a regular file and a Python file
        if [ -f "$file" ] && [[ "$file" == *.py ]]; then
            # Check if the file does not already contain the header
            if ! grep -qF "$header" "$file"; then
                # Add the header to the file using sed
                sed -i "1s/^/$header\n\n/" "$file"
            fi
        fi
    done < <(find "$folder" -type f -print0)
}

# Specify the root folder path and header
root_folder="./graphrag"
header="#\n# Copyright (c) Microsoft. All rights reserved.\n# Licensed under the MIT license. See LICENSE file in the project.\n#"

# Call the function to add header to all Python files recursively
add_header_to_files "$root_folder" "$header"
