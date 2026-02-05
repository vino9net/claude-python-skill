---
name: scaffold
description: >
  Scaffold new Python projects. Triggers: "new python project", "scaffold",
  "init project", "create project skeleton".
allowed-tools: Bash(uv*), Bash(git init*), Bash(chmod*), Bash(mkdir*), Read, Grep, Edit, Write
---

# Python Project Scaffold

Generate a barebone Python project with quality tooling pre-configured.

## What To Ask

If not already provided, ask the user for:

- **Project name** (suggest snake_case)
- **One-line description**

That's it. Then generate all files below.

## Conventions

- Package manager: `uv` (no setup.py, no requirements.txt)
- Layout: `src/{project_name}/`
- Python: 3.13+
- Linting: ruff (lint + format), ty for type checking
- Testing: pytest
- Docstrings: Google style
- Pre-commit: always included

## Project Structure

Generate this exact structure:

```
{project_name}/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── .python-version          # contains: 3.13
├── .pre-commit-config.yaml
├── .gitignore
├── .claude/
│   ├── settings.json
│   └── scripts/
│       ├── init_remote_env.sh
│       ├── grant_python_heredoc.py
│       └── ruff_on_save.py
├── .vscode/
│   └── settings.json
├── .github/
│   └── workflows/
│       └── python_build.yml
├── src/
│   └── {project_name}/
│       ├── __init__.py      # empty
│       └── py.typed          # empty (PEP 561 marker)
└── tests/
    ├── __init__.py          # empty
    └── conftest.py          # minimal, see below
```

---

## pyproject.toml

Generate this exactly, replacing `{project_name}` and `{description}`:

```toml
[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.13"
dependencies = [
    "pydantic>=2.10,<3",
    "python-dotenv>=1.0,<2",
]

[dependency-groups]
dev = [
    "pytest>=8.3,<9",
    "pytest-cov>=6.0,<7",
    "pytest-asyncio>=0.24,<1",
    "pytest-mock>=3.14",
    "pytest-timeout>=2.4.0",
    "pytest-dotenv>=0.5.2",
    "ruff>=0.14.10,<1",
    "ty>=0.0.14",
    "pre-commit>=4.0,<5",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{project_name}"]

[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["tests"]
pythonpath = ["."]
filterwarnings = [
    "ignore::DeprecationWarning",
]
env_files = [".env"]
timeout = 180
timeout_method = "signal"

[tool.coverage.run]
source = ["."]
omit = [
    "tests/*",
]

[tool.ruff]
line-length = 92
indent-width = 4
exclude = [
    ".git",
    "__pycache__",
    "venv",
    ".venv",
]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "W",      # pycodestyle warnings
    "C",      # flake8-comprehensions + mccabe
    "I",      # isort
    "A",      # flake8-builtins
]
ignore = [
    "E203",   # whitespace before ':'
    "E266",   # too many leading '#' for block comment
    "C901",   # function too complex
]
```

## tests/conftest.py

```python
"""Shared test fixtures."""
```

---

## Template Files

Generate each file with the EXACT content shown. Replace `{project_name}` and
`{description}` placeholders where they appear.

### README.md

```markdown
# {project_name}

{description}

## Setup

```bash
uv sync
```

## Development

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format .
uv run ty check
```
```

### CLAUDE.md

```markdown
# {project_name}

{description}

## Development

- Package manager: `uv` (never use pip, setup.py, or requirements.txt)
- Python: 3.13+
- Layout: `src/{project_name}/`

## Code Style

- **Line length: 88 characters max.** Write concise lines from the start. Do not exceed 88 chars and rely on the formatter.
- Modern type annotations: `str | None`, `list[int]`, not `Optional[str]`, `List[int]`
- Google-style docstrings
- Imports: stdlib first, third-party second, local last — alphabetically sorted

## Auto-formatting

A PostToolUse hook automatically runs `ruff format` on any `.py` file after edits.
You do not need to manually format files during development.

## Quality Gates (before commit)

Run these in order — only commit if ALL pass:

1. ruff format .
2. ruff check . --fix
3. ruff check .
4. ty check
5. pytest -v --timeout=180
```

### .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
*.egg
dist/
build/

# Virtual environments
.venv/
venv/

# Environment
.env
.env.*
!.env.example

# Testing
.coverage
htmlcov/
.pytest_cache/

# Type checking
.ty/
.mypy_cache/

# Editors
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# uv
uv.lock

# proj local files
tmp/
```

### .pre-commit-config.yaml

```yaml
exclude: "^$|deploy|tmp|.claude|.vscode"
fail_fast: false
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-merge-conflict
      - id: end-of-file-fixer
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.10
    hooks:
      - id: ruff-check
        args: [--fix]

      - id: ruff-format

  - repo: local
    hooks:
      - id: ty
        name: ty check
        entry: bash -c 'uv run ty check '
        language: system
        pass_filenames: false
        always_run: true
```

### .vscode/settings.json

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "-s"
    ],
    "python.envFile": "${workspaceFolder}/.env",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit",
            "source.fixAll": "explicit"
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "debugpy.debugJustMyCode": false
}
```

### .github/workflows/python_build.yml

```yaml
name: Python Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync

      - name: Lint with ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type check with ty
        run: uv run ty check

      - name: Run tests
        run: uv run pytest -v
```

### .claude/settings.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/scripts/init_remote_env.sh"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/scripts/grant_python_heredoc.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/scripts/ruff_on_save.py"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:*)",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:*.githubusercontent.com)",
      "Bash(uv add:*)",
      "Bash(uv sync:*)",
      "Bash(uv tree:*)",
      "Bash(ls:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(rm:*)",
      "Bash(rg:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(python -m pytest -v:*)",
      "Bash(python:*)",
      "Bash(pytest:*)",
      "Bash(ruff check:*)",
      "Bash(ruff format:*)",
      "Bash(ty check:*)",
      "Bash(uv run python:*)",
      "Bash(uv run pytest:*)",
      "Bash(uv run ruff:*)",
      "Bash(uv run ty check:*)",
      "Bash(git add:*)",
      "Bash(git log:*)",
      "Bash(git mv:*)",
      "Bash(git worktree:*)",
      "Bash(cat:*)",
      "Read(/tmp/claude/*)",
      "Bash(git commit:*)",
      "Bash(git push origin:*)",
      "Bash(git push:*)"
    ],
    "ask": [
      "Bash(pkill:*)",
      "Bash(git push origin main:*)",
      "Bash(git push origin main)"
    ],
    "deny": [],
    "defaultMode": "acceptEdits"
  },
  "includeCoAuthoredBy": false
}
```

### .claude/scripts/init_remote_env.sh

```bash
#!/bin/bash
# =============================================================================
# Claude Code Web Remote Environment Setup Script
# =============================================================================
#
# removed uv installation logic is no longer needed
#
echo "=== Setup complete! ==="
exit 0
```

### .claude/scripts/grant_python_heredoc.py

```python
#!/usr/bin/env python3
"""PermissionRequest hook: auto-grant permission for python heredoc execution.

Claude Code invokes this script when a permission dialog appears for Bash
tool calls. It receives a JSON object on stdin describing the tool call and
can print a JSON decision to stdout:

    {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
     "decision": {"behavior": "allow"}}}   — skip the permission prompt
    {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
     "decision": {"behavior": "deny", "message": "..."}}}  — block the call
    (no output / exit 0)  — fall through to normal permission flow

This hook matches Bash commands that use python/python3 with a heredoc
(<<<), which Claude commonly uses to run inline Python snippets.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HEREDOC_PATTERN = re.compile(r"^(uv run )?(python3?)\s+<<<")
LOG_FILE = os.path.expanduser("~/tmp/pyhooks.log")


def log(payload: dict, decision: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "hook": "grant_python_heredoc",
        "request": payload,
        "decision": decision,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    if HEREDOC_PATTERN.match(command.strip()):
        decision = "allow"
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"},
                }
            },
            sys.stdout,
        )
    else:
        decision = "passthrough"

    log(payload, decision)


if __name__ == "__main__":
    main()
```

### .claude/scripts/ruff_on_save.py

```python
#!/usr/bin/env python3
"""PostToolUse hook: auto-format Python files after edit/write.

Runs `ruff format` on any .py file that was edited or created by Claude,
preventing style drift and reducing pre-commit formatting overhead.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/tmp/pyhooks.log")


def log(payload: dict, decision: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "hook": "ruff_on_save",
        "request": payload,
        "decision": decision,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".py"):
        log(payload, "skip")
        return

    ruff = shutil.which("ruff")
    if ruff:
        cmd = [ruff, "format", file_path]
    else:
        cmd = ["uv", "run", "ruff", "format", file_path]

    result = subprocess.run(cmd, capture_output=True, timeout=10)
    decision = "formatted" if result.returncode == 0 else "error"
    log(payload, decision)


if __name__ == "__main__":
    main()
```

---

## After Generating All Files

Run these commands to finalize:

```bash
cd {project_name}
git init
chmod +x .claude/scripts/*.sh .claude/scripts/*.py
uv sync
```

Verify the setup works:

```bash
uv run pytest -v
uv run ruff check .
uv run ty check
```
