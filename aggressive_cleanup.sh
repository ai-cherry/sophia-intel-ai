#!/bin/bash
# aggressive_cleanup.sh
# Disabled destructive cleanup (replaced with safe, no-op validator)
# Rationale: Original script contained incomplete, unsafe sed commands and truncations.

set -euo pipefail

YELLOW='\033[1;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}Aggressive cleanup is disabled for safety.${NC}"
echo -e "${YELLOW}Use ./pre-deploy-verify.sh and targeted fixes instead.${NC}"

# Lightweight sanity checks (read-only)
issues=0

if rg -n "xxx\\.xxx\\.xxx\\.xxx" --hidden -g '!**/.git/**' . >/dev/null; then
  echo -e "${RED}Found placeholder IPs: xxx.xxx.xxx.xxx${NC}"
  issues=$((issues+1))
fi

if rg -n "<(YOUR|REPLACE|INSERT)_[^>]*>" --hidden -g '!**/.git/**' . >/dev/null; then
  echo -e "${RED}Found angle-bracket placeholders like <YOUR_...>${NC}"
  issues=$((issues+1))
fi

if rg -n "raise NotImplementedError" --hidden -g '!**/.git/**' . >/dev/null; then
  echo -e "${RED}Found NotImplementedError placeholders${NC}"
  issues=$((issues+1))
fi

if [ "$issues" -eq 0 ]; then
  echo -e "${GREEN}No obvious placeholder patterns detected.${NC}"
else
  echo -e "${YELLOW}$issues issue patterns detected. Review before deploy.${NC}"
fi

exit 0
