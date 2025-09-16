#!/usr/bin/env bash
set -euo pipefail

VAR_NAME="${1:-CODEX_API_KEY}"
echo "This will securely add $VAR_NAME to your ~/.zshrc"
echo "(input hidden; value not echoed or logged)"

read -s -p "Enter $VAR_NAME: " SECRET_VALUE
echo
if [[ -z "${SECRET_VALUE}" ]]; then
  echo "No key provided. Aborting." >&2
  exit 1
fi

ZSHRC="$HOME/.zshrc"
TMP_FILE="$(mktemp)"

# Remove any existing export lines for this var (macOS/BSD sed compatible)
if [[ -f "$ZSHRC" ]]; then
  sed "/export ${VAR_NAME}=/d" "$ZSHRC" > "$TMP_FILE"
else
  : > "$TMP_FILE"
fi

{
  echo "# Added by setup_codex_key.sh on $(date -u +'%%Y-%%m-%%dT%%H:%%M:%%SZ')"
  echo "export ${VAR_NAME}=\"$SECRET_VALUE\""
} >> "$TMP_FILE"

mv "$TMP_FILE" "$ZSHRC"

echo "Saved to $ZSHRC"
echo "Reload your shell: source $ZSHRC"
echo "Done."
