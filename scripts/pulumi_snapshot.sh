#!/bin/bash
# Pulumi stack snapshot utility
set -e
BACKUP_DIR=".backups"
mkdir -p "$BACKUP_DIR"
STACK_NAME=$(pulumi stack --show-name 2>/dev/null || echo "dev")
if [ "$1" = "export" ]; then
  pulumi stack export > "$BACKUP_DIR/stack-$STACK_NAME-$(date +%Y%m%d%H%M%S).json"
  echo "Exported stack to $BACKUP_DIR/stack-$STACK_NAME-*.json"
elif [ "$1" = "import" ] && [ -n "$2" ]; then
  pulumi stack import < "$2"
  echo "Imported stack from $2"
else
  echo "Usage: $0 export | import <file>"
  exit 1
fi
