---
name: python-scaffold
description: >
  Scaffold new Python projects or add components to existing ones following org conventions.
  Triggers: "new python project", "scaffold", "add ORM/API/CLI to project", "init project",
  "create project skeleton", "update project dependencies". Also use when asked to add
  SQLAlchemy, FastAPI, Celery, Redis, or other components to an existing Python project.
---

# Python Project Scaffold

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
Components needed: [orm, api, cli, celery, redis] — present as checklist, explain briefly
```

### Round 2 — Conditional (ask based on Round 1 answers)

| Condition                  | Ask                                                            |
|----------------------------|----------------------------------------------------------------|
| Always                     | "Is this a distributable library (pip install) or an app?"     |
| If library                 | "Do you need optional extras groups? (e.g. `pip install x[api]`)" |
| If orm selected            | "Postgres (asyncpg) or SQLite (aiosqlite) for dev?"           |
| If api selected            | "Do you need CORS and auth middleware out of the box?"         |
| If api + orm both selected | "Should API routes get a DB session via dependency injection?" |
| If celery selected         | "Redis or RabbitMQ as broker?"                                |

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

- **Package manager**: `uv` (pyproject.toml based, no setup.py, no requirements.txt)
- **Layout**: src layout — `src/{project_name}/`
- **Tests**: `tests/` mirroring src structure, pytest
- **Linting**: ruff (lint + format), mypy for type checking
- **Pre-commit**: always include `.pre-commit-config.yaml`
- **Python version**: 3.12+ unless user specifies otherwise
- **Docstrings**: Google style

## Project Structure (base)

```
{project_name}/
├── pyproject.toml
├── README.md
├── .pre-commit-config.yaml
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
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
| celery      | `assets/snippets/celery_worker.py`  | worker/, celery config           |
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
