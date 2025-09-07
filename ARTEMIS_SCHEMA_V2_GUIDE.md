# Artemis Schema v2 - Collaborative Code Change Protocol

## Overview
Schema v2 is a structured format for proposing code changes that can be reviewed, approved, and applied automatically by AI agents (Claude, Codex, Artemis).

## Schema Structure

```json
{
  "type": "code_change",
  "version": "2.0",
  "title": "Short description of the change",
  "description": "Detailed explanation of what and why",
  "operations": [
    // Array of file operations (see below)
  ],
  "tests": [
    // Array of test commands to validate changes
  ],
  "metadata": {
    "author": "agent_name",
    "priority": "high|medium|low",
    "breaking_change": false,
    "dependencies": []
  }
}
```

## Operation Types

### 1. MODIFY - Change existing code
```json
{
  "action": "modify",
  "file": "path/to/file.py",
  "hunks": [
    {
      "start_line": 10,
      "end_line": 15,
      "old": "def old_function():\n    return 'old'",
      "new": "def new_function():\n    return 'new'"
    }
  ]
}
```

### 2. CREATE - Add new files
```json
{
  "action": "create",
  "file": "path/to/new_file.py",
  "content": "# New file content\ndef hello():\n    return 'world'"
}
```

### 3. DELETE - Remove files
```json
{
  "action": "delete",
  "file": "path/to/obsolete_file.py",
  "reason": "No longer needed after refactoring"
}
```

### 4. RENAME - Move/rename files
```json
{
  "action": "rename",
  "old_file": "old/path/file.py",
  "new_file": "new/path/better_name.py"
}
```

## Complete Example

```json
{
  "type": "code_change",
  "version": "2.0",
  "title": "Add caching to API endpoints",
  "description": "Implement Redis caching for frequently accessed endpoints to improve performance",
  "operations": [
    {
      "action": "create",
      "file": "app/cache/redis_cache.py",
      "content": "import redis\n\nclass CacheManager:\n    def __init__(self):\n        self.client = redis.Redis()\n    \n    def get(self, key):\n        return self.client.get(key)\n    \n    def set(self, key, value, ttl=3600):\n        self.client.setex(key, ttl, value)"
    },
    {
      "action": "modify",
      "file": "app/api/endpoints.py",
      "hunks": [
        {
          "start_line": 1,
          "end_line": 1,
          "old": "from fastapi import APIRouter",
          "new": "from fastapi import APIRouter\nfrom app.cache.redis_cache import CacheManager"
        },
        {
          "start_line": 10,
          "end_line": 15,
          "old": "    # Direct database query\n    result = db.query(User).all()\n    return result",
          "new": "    # Check cache first\n    cache = CacheManager()\n    cached = cache.get('all_users')\n    if cached:\n        return cached\n    result = db.query(User).all()\n    cache.set('all_users', result)\n    return result"
        }
      ]
    }
  ],
  "tests": [
    "pytest tests/test_cache.py -v",
    "python -m app.cache.redis_cache --test"
  ],
  "metadata": {
    "author": "artemis",
    "priority": "high",
    "breaking_change": false,
    "dependencies": ["redis==4.5.0"]
  }
}
```

## Workflow

### 1. Emit Proposal
```bash
./bin/artemis-run collab emit \
  --type proposal \
  --for claude \
  --content '{"type":"code_change","version":"2.0",...}' \
  --validate-proposal \
  --ttl 7d
```

### 2. List & Review
```bash
# List pending proposals
./bin/artemis-run collab list --filter "pending_review"

# Approve a proposal
./bin/artemis-run collab approve \
  --proposal <id> \
  --agent claude \
  --confidence 0.95 \
  --notes "LGTM, good performance improvement"
```

### 3. Apply Changes
```bash
# Check if safe to merge
./bin/artemis-run collab merge-check --proposal <id>

# Apply the changes
./bin/artemis-run collab apply --proposal <id>

# If tests pass, changes are applied
# If tests fail, automatic rollback occurs
```

## Benefits of Schema v2

1. **Atomic Operations**: All changes in a proposal succeed or fail together
2. **Automatic Testing**: Tests run before applying changes
3. **Rollback Safety**: Failed changes automatically revert
4. **Multi-Agent Review**: Multiple agents can review before applying
5. **Audit Trail**: Complete history of who proposed, reviewed, and applied
6. **Conflict Detection**: Checks for overlapping changes before applying

## Advanced Features

### Conditional Operations
```json
{
  "action": "modify",
  "file": "config.py",
  "condition": "file_exists",
  "hunks": [...]
}
```

### Multi-file Refactoring
```json
{
  "operations": [
    {"action": "rename", "old_file": "utils.py", "new_file": "helpers.py"},
    {"action": "modify", "file": "main.py", "hunks": [
      {"old": "from utils import", "new": "from helpers import"}
    ]}
  ]
}
```

### Validation Rules
- All file paths must be relative to repo root
- Line numbers must be valid for target file
- Old content in modify operations must match exactly
- Test commands must be executable
- JSON must be valid and complete

## Error Handling

Failed proposals include detailed error information:
```json
{
  "error": "apply_failed",
  "details": {
    "operation": 2,
    "file": "app/main.py",
    "reason": "Line 45 content doesn't match expected",
    "expected": "def old_func():",
    "actual": "def different_func():"
  },
  "rollback": "completed"
}
```