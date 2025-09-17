#!/usr/bin/env python3
"""
Test Microsoft Graph with different key combinations
Since tenant ID might be mislabeled, try different arrangements
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv('.env')

# Available values
CLIENT_SECRET_VALUE = "k5X8Q~DssQV1BTrJ2bw5cqjcuW_7RZyThcKMmbf2"
CLIENT_SECRET_ID = "768ceef7-f028-4825-8b17-3f635cd98287"

print("=== Testing Microsoft Graph with different key combinations ===\n")

# Test scenarios - different arrangements in case IDs are mislabeled
test_scenarios = [
    {
        "name": "Scenario 1: Secret ID as Client ID",
        "tenant_id": None,  # Need to find this
        "client_id": CLIENT_SECRET_ID,  # Using secret ID as client ID
        "client_secret": CLIENT_SECRET_VALUE
    },
    {
        "name": "Scenario 2: Look for existing tenant/client in env",
        "tenant_id": os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID"),
        "client_id": os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": CLIENT_SECRET_VALUE
    }
]

# First, let's check what's currently in environment
print("CURRENT ENVIRONMENT:")
print(f"MS_TENANT_ID: {os.getenv('MS_TENANT_ID') or 'NOT SET'}")
print(f"MICROSOFT_TENANT_ID: {os.getenv('MICROSOFT_TENANT_ID') or 'NOT SET'}")
print(f"MS_CLIENT_ID: {os.getenv('MS_CLIENT_ID') or 'NOT SET'}")
print(f"MICROSOFT_CLIENT_ID: {os.getenv('MICROSOFT_CLIENT_ID') or 'NOT SET'}")
print(f"MS_CLIENT_SECRET: {'SET' if os.getenv('MS_CLIENT_SECRET') else 'NOT SET'}")
print(f"MICROSOFT_SECRET_KEY: {'SET' if os.getenv('MICROSOFT_SECRET_KEY') else 'NOT SET'}")
print()

# Search for potential tenant/client IDs in other files
print("SEARCHING FOR POTENTIAL TENANT/CLIENT IDs IN FILES:")
import subprocess
import glob

# Search common locations for Microsoft GUIDs
search_patterns = [
    "*.md", "*.json", "*.py", "*.ts", "*.tsx", "*.yaml", "*.yml"
]

guid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

try:
    result = subprocess.run([
        "grep", "-r", "-E", guid_pattern, ".",
        "--include=*.md", "--include=*.json", "--include=*.py",
        "--include=*.ts", "--include=*.tsx", "--include=*.yaml", "--include=*.yml"
    ], capture_output=True, text=True, timeout=10)

    if result.stdout:
        lines = result.stdout.strip().split('\n')
        unique_guids = set()
        for line in lines[:20]:  # Limit output
            if 'microsoft' in line.lower() or 'azure' in line.lower() or 'tenant' in line.lower():
                print(f"  {line}")
                # Extract GUIDs from the line
                import re
                guids = re.findall(guid_pattern, line)
                unique_guids.update(guids)

        print(f"\nUNIQUE GUIDs FOUND: {len(unique_guids)}")
        for guid in list(unique_guids)[:5]:  # Show first 5
            print(f"  {guid}")

except Exception as e:
    print(f"Search failed: {e}")

print("\n" + "="*60)
print("MANUAL TESTING REQUIRED:")
print("To complete Microsoft Graph testing, we need:")
print("1. TENANT_ID - Your Azure AD tenant identifier")
print("2. CLIENT_ID - Your application (client) ID from Azure App Registration")
print("3. CLIENT_SECRET - The secret value (which we now have)")
print()
print("Please check Azure Portal > Azure Active Directory > App registrations")
print("for the correct TENANT_ID and CLIENT_ID values.")