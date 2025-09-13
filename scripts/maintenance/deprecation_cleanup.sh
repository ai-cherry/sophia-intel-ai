#!/usr/bin/env bash
set -euo pipefail

# Smart cleanup for backup-like artifacts.
# Defaults: non-destructive archive move. Configure via env:
#  - DRY_RUN=1|0 (default 1)
#  - MODE=archive|delete (default archive)
#  - SCOPE=top|all (default top)  # search only repo root or entire tree
#  - DEST_ROOT=path (default tmp/cleanup-<timestamp>)
#  - EXTRA_INCLUDE="pattern1|pattern2" (extended regex for detection)
#  - EXTRA_EXCLUDE="name1|name2" (basename regex to exclude)

DRY_RUN=${DRY_RUN:-1}
MODE=${MODE:-archive}
SCOPE=${SCOPE:-top}

timestamp=$(date +%Y%m%d_%H%M%S)
dest_root=${DEST_ROOT:-"tmp/cleanup-${timestamp}"}
manifest="${dest_root}/MANIFEST.txt"

echo "== Sophia cleanup: detect and ${MODE} backup artifacts =="
echo "Mode: ${MODE}${DRY_RUN:+ (DRY_RUN)}"
echo "Scope: ${SCOPE}"
echo "Destination (archive mode): ${dest_root}"
echo

mkdir -p "${dest_root}"
echo "Created: ${dest_root}" >"${manifest}"
echo "Timestamp: ${timestamp}" >>"${manifest}"
echo "Mode: ${MODE}${DRY_RUN:+ (DRY_RUN)}" >>"${manifest}"
echo >>"${manifest}"

# Build detection regex: common backup/archive markers, allowing digits and separators.
base_regex='(backup|bak|archiv|archive|archived|snapshot)'
include_regex="${EXTRA_INCLUDE:-}"
exclude_regex="(^|/)(archives|config/archive|docs/archive|\\.git|node_modules|__pycache__|\\.venv|venv|dist|build|out|\\.next)(/|$)|(^|/)scripts/.+backup.+\\.sh$|(^|/)scripts/backup-all\\.sh$|(^|/)scripts/redis-backup\\.sh$"
extra_exclude_basename="${EXTRA_EXCLUDE:-}"

# Build candidate lists
if [[ "$SCOPE" == "top" ]]; then
  dir_cmd=(find . -maxdepth 1 -mindepth 1 -type d)
  file_cmd=(find . -maxdepth 1 -mindepth 1 -type f)
else
  dir_cmd=(find . -type d)
  file_cmd=(find . -type f)
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
( "${dir_cmd[@]}" | grep -E "${base_regex}|${include_regex:-__never__}" -i | grep -Ev "${exclude_regex}" || true ) >"$tmpdir/cand_dirs.txt"
( "${file_cmd[@]}" | grep -E "${base_regex}|${include_regex:-__never__}" -i | grep -Ev "${exclude_regex}" || true ) >"$tmpdir/cand_files.txt"

# If delete mode, further restrict file candidates to classic backup suffixes only
if [[ "$MODE" == "delete" ]]; then
  awk -F/ '{print $0"\t"$NF}' "$tmpdir/cand_files.txt" \
    | grep -Ei "\t(.*\\.(backup|bak|old|zip|tar\\.gz|tgz)|\\.env(\\.local)?\\.backup)$" \
    | cut -f1 >"$tmpdir/cand_files2.txt" || true
  mv "$tmpdir/cand_files2.txt" "$tmpdir/cand_files.txt" 2>/dev/null || true
fi

# Further filter with basename excludes if provided
if [[ -n "${extra_exclude_basename}" ]]; then
  awk -F/ '{print $0"\t"$NF}' "$tmpdir/cand_dirs.txt" | grep -Ev "\t(${extra_exclude_basename})$" | cut -f1 >"$tmpdir/cand_dirs2.txt" || true
  awk -F/ '{print $0"\t"$NF}' "$tmpdir/cand_files.txt" | grep -Ev "\t(${extra_exclude_basename})$" | cut -f1 >"$tmpdir/cand_files2.txt" || true
  mv "$tmpdir/cand_dirs2.txt" "$tmpdir/cand_dirs.txt" 2>/dev/null || true
  mv "$tmpdir/cand_files2.txt" "$tmpdir/cand_files.txt" 2>/dev/null || true
fi

move_item() {
  local path="$1"
  local base
  base=$(basename -- "$path")
  if [[ "${MODE}" == "archive" ]]; then
    if [[ "${DRY_RUN}" == "0" ]]; then
      mv "$path" "${dest_root}/$base"
    else
      echo "DRY RUN: mv '$path' '${dest_root}/$base'"
    fi
    echo "$path -> ${dest_root}/$base" >>"${manifest}"
  else
    if [[ "${DRY_RUN}" == "0" ]]; then
      rm -rf -- "$path"
    else
      echo "DRY RUN: rm -rf -- '$path'"
    fi
    echo "$path -> DELETED" >>"${manifest}"
  fi
}

echo "-- Candidates (directories) --"
while IFS= read -r d; do
  [[ -n "$d" && -e "$d" ]] || continue
  echo "Queue: $d"
  move_item "$d"
done <"$tmpdir/cand_dirs.txt"

echo "-- Candidates (files) --"
while IFS= read -r f; do
  [[ -n "$f" && -e "$f" ]] || continue
  echo "Queue: $f"
  move_item "$f"
done <"$tmpdir/cand_files.txt"

echo
if [[ "${DRY_RUN}" == "0" ]]; then
  if [[ "${MODE}" == "archive" ]]; then
    echo "Done. Items moved. See manifest: ${manifest}"
  else
    echo "Done. Items deleted. See manifest: ${manifest}"
  fi
else
  echo "Dry run complete. To apply, set DRY_RUN=0."
  echo "Example (archive top-level only): DRY_RUN=0 bash $0"
  echo "Example (delete across tree): MODE=delete SCOPE=all DRY_RUN=0 bash $0"
  echo "Planned actions logged to: ${manifest}"
fi
