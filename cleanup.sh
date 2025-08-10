#!/bin/bash
set -e

echo "Starting Roo/Cline cleanup..."

# 1. Delete directories and files
echo "Deleting Roo/Cline directories and files..."
rm -rf .roo* .cline* .vscode-shell*

# 2. Clean .vscode/settings.json
SETTINGS_FILE=".vscode/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    echo "Cleaning $SETTINGS_FILE..."
    # Use a temporary file to avoid issues with in-place editing
    tmp_file=$(mktemp)
    # Remove lines containing "roo" or "cline"
    grep -iv "roo\|cline" "$SETTINGS_FILE" > "$tmp_file"
    mv "$tmp_file" "$SETTINGS_FILE"
fi

# 3. Clean .devcontainer/devcontainer.json
DEVCONTAINER_FILE=".devcontainer/devcontainer.json"
if [ -f "$DEVCONTAINER_FILE" ]; then
    echo "Cleaning $DEVCONTAINER_FILE..."
    tmp_file=$(mktemp)
    # A more robust way to remove json elements would be using `jq`,
    # but for this case, we can remove lines with postCreateCommand/postStartCommand if they contain roo/cline
    # This is a simple approach, a more complex devcontainer.json might need a more careful approach
    grep -iv "roo\|cline" "$DEVCONTAINER_FILE" > "$tmp_file"
    mv "$tmp_file" "$DEVCONTAINER_FILE"
fi

# 4. Update .gitignore
echo "Updating .gitignore..."
{
    echo ""
    echo "# Roo/Cline temporary files"
    echo ".roo*"
    echo ".cline*"
    echo ".vscode-shell*"
} >> .gitignore

# 5. Purge other references (simple grep search)
echo "Searching for remaining Roo/Cline references..."
grep -rli "roo\|cline" . --exclude-dir={.git,_salvage} || echo "No other references found."

echo "Cleanup script finished."