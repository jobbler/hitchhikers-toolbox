#!/bin/bash

# ==============================================================================
# 🛠️ THE HITCHHIKER'S BOOTSTRAPPER
# 🤝 Co-developed by John Herr & Gemini (Google AI)
#
# This script acts as a lightweight package manager for the Toolbox.
# It uses the GitHub API to fetch, search, and download specific tools
# without requiring a full repository clone.
# ==============================================================================

# --- Configuration ---
USER="YOUR_GITHUB_USERNAME"
REPO="hitchhikers-toolbox"
API_URL="https://api.github.com/repos/$USER/$REPO/contents"
RAW_URL="https://raw.githubusercontent.com/$USER/$REPO/main"

# --- The Exclude List ---
# Add any file or directory names you want the script to ignore
EXCLUDE_LIST=("README.md" "LICENSE" ".git" ".github" "bootstrap.sh" "docs" "tests")

# --- Helper Functions ---

# Checks if a path should be ignored based on the Exclude List
is_excluded() {
    local ITEM_NAME=$(basename "$1")
    for EXCLUDED in "${EXCLUDE_LIST[@]}"; do
        if [[ "$ITEM_NAME" == "$EXCLUDED" ]]; then
            return 0 # It is excluded
        fi
    done
    return 1 # It is NOT excluded
}

# Recursively fetches and downloads
download_path() {
    local REMOTE_PATH=$1
    local LOCAL_DEST=$2
    
    local RESPONSE=$(curl -s "$API_URL/$REMOTE_PATH")
    
    # Check if single file
    if echo "$RESPONSE" | grep -q '"type": "file"'; then
        mkdir -p "$(dirname "$LOCAL_DEST")"
        echo "📥 Downloading: $REMOTE_PATH"
        curl -sL "$RAW_URL/$REMOTE_PATH" -o "$LOCAL_DEST"
        chmod +x "$LOCAL_DEST" 2>/dev/null
    
    # Check if directory
    elif echo "$RESPONSE" | grep -q '"type": "dir"'; then
        mkdir -p "$LOCAL_DEST"
        local ITEMS=$(echo "$RESPONSE" | grep '"path":' | sed -E 's/.*"path": "([^"]+)".*/\1/')
        
        for ITEM in $ITEMS; do
            if ! is_excluded "$ITEM"; then
                local ITEM_NAME=$(basename "$ITEM")
                download_path "$ITEM" "$LOCAL_DEST/$ITEM_NAME"
            fi
        done
    fi
}

# Fetches all files in the repo recursively to search/list
fetch_all_paths() {
    # Using the recursive flag in GitHub API
    curl -s "$API_URL?recursive=1" | grep '"path":' | sed -E 's/.*"path": "([^"]+)".*/\1/'
}

# --- Command Logic ---

case "$1" in
    --list)
        echo "📜 Available Tools in the Toolbox:"
        fetch_all_paths | while read -r line; do
            is_excluded "$line" || echo "  - $line"
        done
        ;;
        
    --search)
        if [ -z "$2" ]; then echo "❌ Provide a search term."; exit 1; fi
        echo "🔍 Searching for '$2'..."
        fetch_all_paths | grep -i "$2" | while read -r line; do
            is_excluded "$line" || echo "  - $line"
        done
        ;;
        
    --get)
        if [ -z "$2" ]; then echo "❌ Provide a path to download."; exit 1; fi
        REMOTE=$2
        LOCAL=${3:-"./hitchhiker_tools/$(basename "$REMOTE")"}
        download_path "$REMOTE" "$LOCAL"
        echo "✅ Done! Files located in: $LOCAL"
        ;;

    *)
        echo "Usage:"
        echo "  --list             List all non-excluded files"
        echo "  --search [term]    Search for a specific tool"
        echo "  --get [path] [dest] Download a file/folder to a destination"
        ;;
esac


