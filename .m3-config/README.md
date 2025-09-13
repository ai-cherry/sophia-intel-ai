# M3 Mac Deployment Memory

This directory contains ARM64/M3-specific configurations for Sophia Intel AI.

## Quick Start
Run: `./.m3-config/setup.sh`

## Key Principles
1. ALWAYS use Homebrew for dev tools
2. ALWAYS verify ARM64 with: arch
3. ALWAYS use terminal, not IDEs
4. NEVER mix x86 and ARM64 packages

## Daily Commands
- make m3-verify - Check environment
- make m3-run - Start optimized
- make m3-test - Run tests
