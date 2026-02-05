---
name: python-dev
description: >
  Scaffold new Python projects, add components, and enforce development standards.
  Triggers: "new python project", "scaffold", "add ORM/API/CLI to project", "init project",
  "create project skeleton", "update project dependencies". Also use when asked to add
  SQLAlchemy, FastAPI, Redis, or other components to an existing Python project.
  Also applies when writing Python code, reviewing code quality, or preparing commits.
allowed-tools: Bash(ruff*), Bash(ty*), Bash(uv*), Bash(pytest*), Read, Grep, Edit
---

# Python Project Scaffold & Development Standards

## Quick Start

1. Read this file for workflow and conventions
2. If generating code for a component, read the matching snippet from `assets/snippets/`
3. If managing dependencies, read `references/dependencies.md` for the version master list
4. If the user asks about packaging/distribution, read `references/packaging.md`

## Scaffold Interview

When the user asks to create a new project, gather requirements BEFORE generating any files.
Do not ask all questions at once — group them into 2 rounds maximum.

### Round 1 — Essential (always ask)

```
Project name: {ask user, suggest snake_case}
One-line description: {ask user}
Components needed: [orm, api, cli, redis] — present as checklist, explain briefly
```

### Round 2 — Conditional (ask based on Round 1 answers)

| Condition                  | Ask                                                            |
|----------------------------|----------------------------------------------------------------|
| Always                     | "Is this a distributable library (pip install) or an app?"     |
| If library                 | "Do you need optional extras groups? (e.g. `pip install x[api]`)" |
| If orm selected            | "Postgres (asyncpg) or SQLite (aiosqlite) for dev?"           |
| If api selected            | "Do you need CORS and auth middleware out of the box?"         |
| If api + orm both selected | "Should API routes get a DB session via dependency injection?" |

### After interview

Summarize the choices back to the user in a short table and ask for confirmation before
generating any files. Example:

```
Project:      fund_parser
Type:         Library (pip installable with extras)
Components:   orm, api, cli
ORM backend:  asyncpg (Postgres)
API extras:   CORS enabled, no auth
Distribution: pip install fund_parser[api,orm]

Proceed? (y/n)
```

Only after confirmation: read the relevant snippet files and generate the project.

## Core Conventions

- **Package manager**: `uv` (pyproject.toml based, no setup.py, no requirements.txt). Never ask the user which package manager to use — always use `uv`.
- **Layout**: src layout — `src/{project_name}/`
- **Tests**: `tests/` mirroring src structure, pytest
- **Linting**: ruff (lint + format), ty for type checking
- **Pre-commit**: always include `.pre-commit-config.yaml`
- **Python version**: 3.13+ unless user specifies otherwise
- **Docstrings**: Google style

## Project Structure (base)

```
{project_name}/
├── pyproject.toml
├── README.md
├── .python-version
├── .pre-commit-config.yaml
├── .gitignore
├── .claude/
│   ├── settings.json        # skill reference + tool permissions
│   └── scripts/
│       ├── init_remote_env.sh
│       └── grant_python_heredoc.py
├── .vscode/
│   └── settings.json        # editor defaults for Python + ruff
├── .github/
│   └── workflows/
│       └── python_build.yml
├── src/
│   └── {project_name}/
│       ├── __init__.py
│       ├── py.typed          # PEP 561 marker
│       └── config.py         # pydantic-settings based
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_config.py
└── docker/
    └── Dockerfile
```

## Scaffold Templates

Always copy these templates from `assets/templates/` into the scaffolded project:

- `.gitignore` → `.gitignore`
- `.pre-commit-config.yaml` → `.pre-commit-config.yaml`
- `vscode-settings.json` → `.vscode/settings.json`
- `python_build.yml` → `.github/workflows/python_build.yml`
- `settings.json` → `.claude/settings.json`
- `init_remote_env.sh` → `.claude/scripts/init_remote_env.sh`
- `grant_python_heredoc.py` → `.claude/scripts/grant_python_heredoc.py`

Ensure the scripts are executable (`chmod +x`).

Skills are added as git submodules under `.claude/skills/`. If the project uses skills,
add a `"skills"` key to the generated settings file.

## Component System

When the user requests a component, follow these steps:

1. Check if the project already exists (look for pyproject.toml)
2. If existing: **merge** new dependencies and add only new files
3. If new: generate base structure + requested components together
4. Always read the matching snippet file from `assets/snippets/` before generating code

### Available Components

| Component   | Snippet File                        | Adds To                          |
|-------------|-------------------------------------|----------------------------------|
| orm         | `assets/snippets/orm.py`            | db/, alembic/, conftest fixtures |
| api         | `assets/snippets/api.py`            | api/, main.py, conftest fixtures |
| cli         | `assets/snippets/cli.py`            | cli.py, pyproject scripts        |
| redis       | `assets/snippets/redis_cache.py`    | cache/, conftest fixtures        |

### Adding to Existing Projects

When adding a component to an existing project:

- **pyproject.toml**: Read `references/dependencies.md` for approved versions. Merge new
  dependencies into existing `[project.dependencies]` — never overwrite existing ones.
- **conftest.py**: Append new fixtures below existing ones. Do not reorder or remove existing
  fixtures. Preserve existing imports and add new ones at the top.
- **config.py**: Add new Settings fields for the component (e.g., `DATABASE_URL` for orm).

## Dependency Management

All dependency versions come from `references/dependencies.md`. This is the single source of
truth for approved versions. When generating pyproject.toml:

- Use exact version pins from the master list for `[project.dependencies]`
- Use compatible release (`~=`) for dev dependencies
- If a library is not in the master list, use latest stable and flag it to the user

## Packaging / Distribution

When the user asks to make the project installable or distributable as a package, read
`references/packaging.md` for the standard pyproject.toml sections to add.

---

# Development Standards

This section governs day-to-day Python development: coding style, linting, type checking,
testing, and commit workflow.

## Core Principles

1. **Format and lint ONLY before commits** — not during normal code changes
2. **Detect Python version** from `.python-version` file in project root
3. **Use standardized tools** — ruff, ty, uv (no alternatives)
4. **Modern type annotations** — Python 3.10+ syntax

## During Development

- Write code following PEP8 conventions
- Use modern type annotation syntax (see below)
- Keep imports at the top of the file
- Keep line length reasonable (ruff enforces this later)
- **DO NOT run linting/formatting** — save it for the pre-commit step

## Pre-Commit Quality Gates

When preparing to commit, run these checks in order. Only commit if ALL pass.

```
1. ruff format .
2. ruff check . --fix
3. ruff check .
4. ty check
5. pytest
6. Commit
```

### After Failed Checks

- Read error messages carefully
- Fix issues one at a time
- Re-run the specific check that failed
- Continue through the checklist

## Type Annotations (Python 3.10+)

Use modern syntax — do not import from `typing` for built-in generics.

```python
# Correct
def process(data: str | None) -> list[dict[str, int]]:
    items: set[str] = set()
    return []

# Incorrect
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
| **ty** | `ty check` · `ty check <file>` |
| **uv** | `uv add <pkg>` · `uv sync` · `uv run <cmd>` |
| **pytest** | `pytest` · `pytest tests/test_file.py` · `pytest -v` |
