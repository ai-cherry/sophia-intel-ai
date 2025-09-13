#!/usr/bin/env bash
set -euo pipefail

# Setup GitHub SSH deploy keys for this repo using a GitHub PAT for API auth.
# - Generates three SSH keypairs under ./secrets/ssh (gitignored)
# - Adds them as deploy keys (read_write) to the current repository
# - Prints sshconfig snippets you can copy to ~/.ssh/config
#
# Usage:
#   GITHUB_TOKEN=... OWNER=ai-cherry REPO=sophia-intel-ai bash scripts/setup_github_ssh.sh
#

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd -P)"
SSH_DIR="$ROOT_DIR/secrets/ssh"
mkdir -p "$SSH_DIR"

OWNER="${OWNER:-ai-cherry}"
REPO="${REPO:-sophia-intel-ai}"
API="https://api.github.com"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN not set. Export a PAT with repo:admin scope." >&2
  exit 1
fi

declare -a KEYS=("sophia-main" "forge-ui" "portkey-ui")

echo "Generating SSH keypairs in $SSH_DIR (ed25519)"
for name in "${KEYS[@]}"; do
  priv="$SSH_DIR/id_ed25519_${name}"
  pub="$priv.pub"
  if [ ! -f "$priv" ]; then
    ssh-keygen -t ed25519 -N "" -f "$priv" -C "$name@${REPO}"
  else
    echo "Key exists: $priv (skipping generation)"
  fi
done

echo "Adding deploy keys to GitHub repo $OWNER/$REPO"
for name in "${KEYS[@]}"; do
  priv="$SSH_DIR/id_ed25519_${name}"
  pub="$priv.pub"
  title="deploy-$name"
  key=$(cat "$pub")
  # Create deploy key with write access
  code=$(curl -sS -o "$SSH_DIR/resp_${name}.json" -w "%{http_code}" \
    -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
    "$API/repos/$OWNER/$REPO/keys" \
    -d @- <<EOF
{"title":"$title","key":"$key","read_only":false}
EOF
  )
  if [ "$code" != "201" ] && [ "$code" != "422" ]; then
    echo "Failed to add deploy key $title (HTTP $code). See $SSH_DIR/resp_${name}.json" >&2
  else
    echo "Deploy key added or exists: $title (HTTP $code)"
    rm -f "$SSH_DIR/resp_${name}.json"
  fi
done

cat > "$SSH_DIR/ssh_config.sample" << 'EOF'
# Copy these stanzas into ~/.ssh/config and adjust paths as needed
Host github.com-sophia-main
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_sophia_main
  IdentitiesOnly yes

Host github.com-forge-ui
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_forge_ui
  IdentitiesOnly yes

Host github.com-portkey-ui
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_portkey_ui
  IdentitiesOnly yes

# Example remotes:
#   git remote set-url origin git@github.com-sophia-main:${OWNER}/${REPO}.git
#   git clone git@github.com-forge-ui:yourorg/forge-ui.git
#   git clone git@github.com-portkey-ui:yourorg/portkey-ui.git
EOF

echo
echo "SSH deploy keys prepared in $SSH_DIR."
echo "- Public keys added as deploy keys on $OWNER/$REPO"
echo "- Copy ssh_config.sample entries to ~/.ssh/config and move private keys to ~/.ssh/ as desired"
echo "- Update git remotes to use the host aliases if you prefer (examples in the sample file)"

