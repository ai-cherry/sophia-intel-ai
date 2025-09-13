#!/bin/bash
# Git Worktree Management for Anti-Fragmentation
# From Jul 2025 X post best practices

# Create worktree for agent
wt() { 
    local name="$1"
    local base_dir="${WORKTREES_DIR:-../worktrees}"
    
    # Create worktree from main branch
    if [[ ! -d "$base_dir/$name" ]]; then
        git worktree add "$base_dir/$name" main
    fi
    
    # Switch to worktree and create branch
    cd "$base_dir/$name" && git checkout -b "$name" 2>/dev/null || git checkout "$name"
    
    echo "✅ Worktree '$name' ready at $base_dir/$name"
}

# Clean all worktrees
wtc() { 
    echo "Cleaning all worktrees..."
    git worktree list --porcelain | grep -B2 "branch refs/heads/" | grep "worktree" | cut -d' ' -f2 | xargs -I {} git worktree remove {} 2>/dev/null || true
    echo "✅ All worktrees cleaned"
}

# List active worktrees
wtl() {
    echo "Active Worktrees:"
    git worktree list
}

# Check for duplicates across worktrees
wtd() {
    local pattern="$1"
    local base_dir="${WORKTREES_DIR:-../worktrees}"
    
    echo "Checking for '$pattern' across all worktrees..."
    
    # Check main repo
    echo "Main repository:"
    rg -i "$pattern" . 2>/dev/null | head -5 || echo "  No matches"
    
    # Check each worktree
    if [[ -d "$base_dir" ]]; then
        for wt in "$base_dir"/*; do
            if [[ -d "$wt" ]]; then
                echo ""
                echo "Worktree: $(basename "$wt")"
                rg -i "$pattern" "$wt" 2>/dev/null | head -3 || echo "  No matches"
            fi
        done
    fi
}

# Merge worktree with dedup check
wtm() {
    local branch="$1"
    
    echo "Preparing to merge worktree branch '$branch'..."
    
    # Run deduplication check
    echo "Running deduplication scan..."
    if [[ -f "scripts/dup_scan.py" ]]; then
        python scripts/dup_scan.py --branch "$branch"
    else
        echo "⚠️  No dup_scan.py found, doing basic check..."
        git diff main..."$branch" --name-only | while read -r file; do
            echo "Checking $file for duplicates..."
            rg -i "$(basename "${file%.*}")" --type "$(echo "${file##*.}")" . 2>/dev/null | head -2
        done
    fi
    
    # If clean, merge
    read -p "Proceed with merge? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout main
        git merge --no-ff "$branch" -m "feat(agent): Merge $branch with dedup check"
        echo "✅ Merged successfully"
        
        # Clean up worktree
        git worktree remove "../worktrees/$branch" 2>/dev/null || true
        echo "✅ Worktree cleaned"
    else
        echo "❌ Merge cancelled"
    fi
}

# Status of all worktrees
wts() {
    local base_dir="${WORKTREES_DIR:-../worktrees}"
    
    echo "Worktree Status Report:"
    echo "======================="
    
    git worktree list | while read -r line; do
        local path=$(echo "$line" | awk '{print $1}')
        local branch=$(echo "$line" | grep -oP '\[.*?\]' | tr -d '[]')
        
        if [[ -d "$path" ]]; then
            cd "$path"
            local changes=$(git status --porcelain | wc -l)
            local ahead=$(git rev-list --count HEAD...origin/main 2>/dev/null || echo "0")
            
            echo ""
            echo "📁 $(basename "$path") [$branch]"
            echo "   Path: $path"
            echo "   Changes: $changes files"
            echo "   Ahead of main: $ahead commits"
            
            if [[ $changes -gt 0 ]]; then
                echo "   Modified files:"
                git status --porcelain | head -3 | sed 's/^/      /'
            fi
        fi
    done
}

# Export functions for use in other scripts
export -f wt wtc wtl wtd wtm wts