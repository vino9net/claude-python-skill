# python-dev

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that scaffolds Python projects, adds components, and enforces development standards.

## What It Does

- Generates new Python projects with a standard `src/` layout, CI, Docker, and tooling pre-configured
- Adds components to existing projects: **ORM** (SQLAlchemy), **API** (FastAPI), **CLI** (Typer), **Redis**
- Manages dependencies from a curated version master list
- Supports packaging as a distributable library or standalone application
- Enforces coding standards during development: **ruff** (lint/format), **ty** (type checking), **pytest** (testing)
- Defines a pre-commit quality gate workflow (format → lint → type check → test)

## Installation

Add this skill to your Claude Code project or user settings:

### Project-level (`.claude/settings.json`)

```json
{
  "skills": [
    "/path/to/agent-python-skill"
  ]
}
```

### User-level (`~/.claude/settings.json`)

```json
{
  "skills": [
    "/path/to/agent-python-skill"
  ]
}
```

Replace `/path/to/agent-python-skill` with the absolute path to this directory.

## Usage

Once installed, the skill activates in two contexts:

### Scaffolding a project

```
> new python project
> scaffold a python api
> add ORM to this project
> add CLI to this project
> create project skeleton
> update project dependencies
```

Claude will walk you through a short interview:

1. **Round 1** — Project name, description, and which components you need
2. **Round 2** — Follow-up questions based on your choices (DB backend, middleware, distribution type, etc.)

After you confirm, it generates the full project structure.

### During development

The skill also activates when writing, reviewing, or committing Python code. It enforces:

- Modern type annotations (`str | None`, not `Optional[str]`)
- PEP8 conventions and import organization
- A pre-commit checklist before every commit:

```
1. ruff format .
2. ruff check . --fix
3. ruff check .
4. ty check
5. pytest
```

## Generated Project Structure

```
my_project/
├── pyproject.toml
├── README.md
├── .python-version
├── .pre-commit-config.yaml
├── .gitignore
├── .claude/
│   ├── settings.json
│   └── scripts/
│       ├── init_remote_env.sh
│       └── grant_python_heredoc.py
├── .vscode/
│   └── settings.json
├── .github/workflows/python_build.yml
├── src/my_project/
│   ├── __init__.py
│   ├── py.typed
│   └── config.py
├── tests/
│   ├── conftest.py
│   └── test_config.py
└── docker/Dockerfile
```

Components add more directories (e.g. `db/`, `api/`, `cli.py`, `worker/`, `cache/`) as needed.

## Available Components

| Component | Stack | What Gets Added |
|-----------|-------|-----------------|
| **orm** | SQLAlchemy 2 + Alembic | `db/`, `alembic/`, DB fixtures |
| **api** | FastAPI + Uvicorn | `api/`, health check, test client |
| **cli** | Typer + Rich | `cli.py`, pyproject script entry |
| **redis** | redis-py | `cache/`, fakeredis fixtures |

## Conventions

| Area | Choice |
|------|--------|
| Package manager | `uv` |
| Layout | `src/{name}/` |
| Python | 3.13+ |
| Linting | ruff (lint + format) + ty |
| Testing | pytest, pytest-asyncio |
| Config | pydantic-settings |
| Docstrings | Google style |
| Pre-commit | Always included |

## License

Internal tooling — no license specified.
