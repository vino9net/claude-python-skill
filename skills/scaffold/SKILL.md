---
name: scaffold
description: >
  Scaffold new Python projects or add components to existing ones.
  Triggers: "new python project", "scaffold", "add API/CLI to project", "init project",
  "create project skeleton", "update project dependencies". Also use when asked to add
  FastAPI or other components to an existing Python project.
allowed-tools: Bash(uv*), Read, Grep, Edit
---

# Python Project Scaffold

## Quick Start

1. Read this file for workflow and conventions
2. **Do NOT search for files** — read template and snippet files directly by their exact paths listed below
3. For components: read `assets/snippets/api.py` or `assets/snippets/cli.py` directly
4. For dependencies: read `references/dependencies.md` directly
5. For pyproject.toml reference: read `assets/templates/pyproject.toml` directly

## Scaffold Interview

When the user asks to create a new project, gather requirements BEFORE generating any files.
Do not ask all questions at once — group them into 2 rounds maximum.

### Round 1 — Essential (always ask)

```
Project name: {ask user, suggest snake_case}
One-line description: {ask user}
Components needed: [api, cli] — present as checklist, explain briefly
```

### After interview

Summarize the choices back to the user in a short table and ask for confirmation before
generating any files. Example:

```
Project:      fund_parser
Type:         Library (pip installable with extras)
Components:   api, cli
API extras:   CORS enabled, no auth
Distribution: pip install fund_parser[api]

Proceed? (y/n)
```

Only after confirmation: read the relevant snippet files and generate the project.

## Core Conventions

- **Package manager**: `uv` (pyproject.toml based, no setup.py, no requirements.txt). Never ask the user which package manager to use — always use `uv`.
- **Layout**: src layout — `src/{project_name}/`
- **Tests**: `tests/` mirroring src structure, pytest
- **Linting**: ruff (lint + format), ty for type checking, deptry for dependency checks
- **Pre-commit**: always include `.pre-commit-config.yaml`
- **Python version**: 3.13+ unless user specifies otherwise
- **Docstrings**: Google style

## Project Structure (base)

```
{project_name}/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── .python-version
├── .pre-commit-config.yaml
├── .gitignore
├── .claude/
│   ├── settings.json        # skill reference + tool permissions
│   └── scripts/
│       ├── init_remote_env.sh
│       ├── grant_python_heredoc.py
│       └── ruff_on_save.py
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
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_config.py
```

## Scaffold Templates

**Do NOT search for templates.** Read each template file directly by its exact path and copy to the target project.

| Template File (read from)                        | Target Location                        | Replacements                                           |
|--------------------------------------------------|----------------------------------------|--------------------------------------------------------|
| `assets/templates/pyproject.toml`                | `pyproject.toml`                       | `{project_name}`, `{description}`, `{python_version}`  |
| `assets/templates/CLAUDE.md`                     | `CLAUDE.md`                            | `{project_name}`, `{description}`                      |
| `assets/templates/.gitignore`                    | `.gitignore`                           | None                                                   |
| `assets/templates/.pre-commit-config.yaml`       | `.pre-commit-config.yaml`              | None                                                   |
| `assets/templates/vscode-settings.json`          | `.vscode/settings.json`                | None                                                   |
| `assets/templates/python_build.yml`              | `.github/workflows/python_build.yml`   | None                                                   |
| `assets/templates/settings.json`                 | `.claude/settings.json`                | None                                                   |
| `assets/templates/init_remote_env.sh`            | `.claude/scripts/init_remote_env.sh`   | None (make executable)                                 |
| `assets/templates/grant_python_heredoc.py`       | `.claude/scripts/grant_python_heredoc.py` | None (make executable)                              |
| `assets/templates/ruff_on_save.py`               | `.claude/scripts/ruff_on_save.py`      | None (make executable)                                 |

After copying scripts, run `chmod +x` on the `.sh` and `.py` files in `.claude/scripts/`.

## Post-Scaffold Instructions

After all files are generated, tell the user to run these commands to finish setup:

```
cd {project_name}
uv sync
uv run pre-commit install
```

## Component System

When the user requests a component, follow these steps:

1. Check if the project already exists (look for pyproject.toml)
2. If existing: **merge** new dependencies and add only new files
3. If new: generate base structure + requested components together
4. Read the matching snippet file directly by path (do NOT search) before generating code

### Available Components

**Read these snippet files directly by path when the component is requested:**

| Component | Read This File              | Creates                          |
|-----------|-----------------------------|----------------------------------|
| api       | `assets/snippets/api.py`    | api/, main.py, conftest fixtures |
| cli       | `assets/snippets/cli.py`    | cli.py, pyproject scripts        |

### Adding to Existing Projects

When adding a component to an existing project:

- **pyproject.toml**: Read `references/dependencies.md` for approved versions. Merge new
  dependencies into existing `[project.dependencies]` — never overwrite existing ones.
- **conftest.py**: Append new fixtures below existing ones. Do not reorder or remove existing
  fixtures. Preserve existing imports and add new ones at the top.
- **config.py**: Add new Settings fields for the component.

## Dependency Management

All dependency versions come from `references/dependencies.md`. This is the single source of
truth for approved versions. When generating pyproject.toml:

- Use exact version pins from the master list for `[project.dependencies]`
- Use compatible release (`~=`) for dev dependencies
- If a library is not in the master list, use latest stable and flag it to the user

## Packaging / Distribution

When the user asks to make the project installable or distributable as a package, use
`assets/templates/pyproject.toml` as the reference template for standard sections.

## Docker

Do NOT generate Dockerfiles, docker-compose files, or any Docker-related configuration.
If the user asks for Docker support, explain that this scaffold does not include Docker
and suggest they add it manually if needed.
