#!/bin/bash
set -e

# 1. Create salvage directory
echo "Creating _salvage directory..."
mkdir -p _salvage
LOGFILE="/workspaces/sophia-intel/_salvage/salvaged_files.log"
echo "Log file at: $LOGFILE" > "$LOGFILE"

# 2. Define search paths
# Note: ~ expands to /root in this environment
VSCODE_HISTORY_PATH="/workspaces/sophia-intel/.vscode/.history"
CODESPACES_PATH="/workspaces/.codespaces"

# 3. Function to check if a file is tracked by Git
is_tracked() {
    # Run from the git repo root
    git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

# 4. Find and copy untracked files from the workspace
echo "Searching for untracked files in /workspaces/sophia-intel..."
cd /workspaces/sophia-intel

# Find all files, excluding .git and _salvage directories
find . -not -path "./.git/*" -not -path "./_salvage/*" -type f | while read -r file; do
    filepath="${file#./}"
    if ! is_tracked "$filepath"; then
        if ! git check-ignore -q "$filepath"; then
            echo "Salvaging untracked workspace file: $filepath" >> "$LOGFILE"
            # Preserve directory structure inside a 'workspace' subdirectory
            mkdir -p "_salvage/workspace/$(dirname "$filepath")"
            cp "$filepath" "_salvage/workspace/$filepath"
        fi
    fi
done

# 5. Find and copy files from other locations
OTHER_LOCATIONS=(
    "/tmp"
    "/root/.cache"
    "$VSCODE_HISTORY_PATH"
    "$CODESPACES_PATH"
)

for loc in "${OTHER_LOCATIONS[@]}"; do
    if [ -d "$loc" ]; then
        dest_name=$(echo "$loc" | tr '/' '_')
        dest_path="_salvage/locations/$dest_name"
        echo "Salvaging from $loc into $dest_path" >> "$LOGFILE"
        mkdir -p "$dest_path"
        rsync -aq "$loc/" "$dest_path/"
    fi
done

# 6. Find and copy dotfiles
echo "Searching for Roo/Cline dotfiles..."
find /workspaces /root -maxdepth 2 \( -name ".roo*" -o -name ".cline*" \) | while read -r file; do
    dest_name=$(echo "$file" | tr '/' '_')
    dest_path="_salvage/dotfiles/$dest_name"
    echo "Salvaging dotfile: $file into $dest_path" >> "$LOGFILE"
    mkdir -p "$(dirname "$dest_path")"
    # Use rsync for directories, cp for files
    if [ -d "$file" ]; then
        rsync -aq "$file/" "$dest_path/"
    else
        cp -a "$file" "$dest_path"
    fi
done

echo "Salvage search complete. See $LOGFILE for details."