---
name: quality
description: >
  Python development quality standards. Applies when writing, reviewing,
  or committing Python code. Enforces coding style, line length, type
  annotations, linting (ruff), type checking (ty), and testing (pytest).
user-invocable: false
allowed-tools: Bash(ruff*), Bash(ty*), Bash(uv*), Bash(pytest*), Bash(deptry*), Read, Grep, Edit
---

# Python Quality Standards

These standards apply whenever you write, review, or commit Python code.

## Line Length

**Target 88 characters per line. Hard limit is 92 (enforced by ruff).**

This is critical — write concise lines from the start. Strategies:
- Break function arguments onto separate lines when they exceed 88 chars
- Use intermediate variables instead of deeply nested expressions
- Prefer shorter but clear names
- Break chained method calls across lines

Do NOT write lines over 88 characters and rely on the formatter to fix them.

## Code Style

- PEP8 conventions
- Google-style docstrings
- Keep imports at the top of the file

## Type Annotations (Python 3.10+)

Use modern syntax — do not import from `typing` for built-in generics.

```python
# Correct
def process(data: str | None) -> list[dict[str, int]]:
    items: set[str] = set()
    return []

# Incorrect — never do this
from typing import Optional, List, Dict, Set
def process(data: Optional[str]) -> List[Dict[str, int]]:
    items: Set[str] = set()
    return []
```

Remove unused `typing` imports when converting to modern syntax.

## Import Organization

- Standard library imports first
- Third-party imports second
- Local imports last
- Alphabetically sorted within each group
- Always at top of file

## During Development

- Write clean code following these standards
- **DO NOT run linting/formatting** — a PostToolUse hook auto-formats `.py` files on save
- Focus on correctness and readability

## Testing

- Write tests that verify **behavior**, not implementation details
- Don't test getters, setters, constants, or trivial wiring
- Each test should assert something that could actually break
- Use realistic fixtures (e.g. actual tmux captures, not synthetic data)
- If a test would still pass after deleting the code under test, it's useless

## Pre-Commit Quality Gates

When preparing to commit, run these checks in order. Only commit if ALL pass.

```
1. ruff format .
2. ruff check . --fix
3. ruff check .
4. deptry .
5. ty check
6. pytest -v --timeout=180
7. Commit
```

### After Failed Checks

- Read error messages carefully
- Fix issues one at a time
- Re-run the specific check that failed
- Continue through the checklist

## Package Management with uv

```bash
uv add <package>       # add a dependency
uv sync                # sync lockfile to environment
uv run <command>       # run inside the virtual environment
uv run pytest          # example: run tests
```

## Tools Reference

| Tool | Commands |
|------|----------|
| **ruff** | `ruff format .` · `ruff check .` · `ruff check . --fix` |
| **deptry** | `deptry .` — find unused, missing, and transitive dependencies |
| **ty** | `ty check` · `ty check <file>` |
| **uv** | `uv add <pkg>` · `uv sync` · `uv run <cmd>` |
| **pytest** | `pytest` · `pytest tests/test_file.py` · `pytest -v` |
