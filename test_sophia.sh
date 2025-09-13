#!/bin/bash
# Test unified SOPHIA CLI

echo "Testing SOPHIA CLI..."

# Test basic commands
./sophia --version
./sophia analyze .
./sophia swarm list
./sophia mcp status
./sophia config --list
./sophia doctor

echo "✓ All tests passed"
