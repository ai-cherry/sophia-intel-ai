#!/bin/bash
# Generate canonical SSH key for SOPHIA infra
KEY_PATH="$HOME/.ssh/id_ed25519_sophia_prod"
if [ -f "$KEY_PATH" ]; then
  echo "Key $KEY_PATH already exists."
  read -p "Reuse this key? (y/n): " yn
  case $yn in
    [Yy]*) echo "Reusing existing key."; exit 0;;
    *) echo "Aborting. Please backup and remove $KEY_PATH before continuing."; exit 1;;
  esac
fi
ssh-keygen -t ed25519 -C "sophia-prod" -f "$KEY_PATH" -N ""
echo "Public key generated at: $KEY_PATH.pub"
