#!/bin/bash
echo 'Clearing all cache issues...'

# Stop any running servers
pkill -f 'next-server' 2>/dev/null || true
pkill -f 'pnpm dev' 2>/dev/null || true

# Clear Next.js cache
rm -rf .next/
rm -rf node_modules/.cache/

# Clear PNPM cache
export PATH=/opt/homebrew/bin:$PATH
pnpm store prune

# Restart fresh
echo 'Starting fresh development server...'
pnpm dev --port 3000

