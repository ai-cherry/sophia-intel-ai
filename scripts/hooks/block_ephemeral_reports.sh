#!/usr/bin/env bash
# Blocks commit when ephemeral report/artifact files are staged.
# This hook is triggered only for files matching the configured 'files' regex.

printf "%s\n" "Blocking commit - ephemeral report/artifact files should not be committed.
Move them to persistent storage (e.g., object store) or exclude them via .gitignore.
If this is intentional, consider committing to a non-protected branch or add an exception."
exit 1
