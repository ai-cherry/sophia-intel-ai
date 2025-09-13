#!/usr/bin/env python3
# Update Bridge API to allow Builder Dashboard CORS

import fileinput
import sys

# Read the bridge/api.py file and update CORS settings
with open('bridge/api.py', 'r') as f:
    content = f.read()

# Replace the CORS origins line
old_line = 'cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")'
new_line = 'cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:8005")'

content = content.replace(old_line, new_line)

# Write back
with open('bridge/api.py', 'w') as f:
    f.write(content)

print('Updated CORS settings to include Builder Dashboard on port 8005')
