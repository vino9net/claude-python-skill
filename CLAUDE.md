# Agent Python Skill (Plugin: `py`)

A Claude Code plugin for scaffolding Python projects, enforcing quality standards, and running tests.

## Plugin Structure

This is a Claude Code plugin providing three skills:

| Skill | Command | Description |
|-------|---------|-------------|
| **scaffold** | `/py:scaffold` | Generate new Python projects or add components |
| **quality** | *(auto-invoked)* | Coding style, linting, type checking, line length |
| **pytest** | `/py:pytest` | Run test suite in isolated subagent |

## Directory Layout

```
.
├── .claude-plugin/
│   └── plugin.json              # Plugin definition (name: "py")
├── skills/
│   ├── scaffold/SKILL.md        # /py:scaffold — project scaffolding
│   ├── quality/SKILL.md         # Auto-invoked quality standards
│   └── pytest/SKILL.md          # /py:pytest — test runner (context: fork)
├── assets/
│   ├── snippets/                # Code templates for each component
│   │   ├── api.py               # FastAPI component patterns
│   │   ├── orm.py               # SQLAlchemy/Alembic component patterns
│   │   └── cli.py               # Typer CLI component patterns
│   └── templates/               # Files copied into scaffolded projects
│       ├── CLAUDE.md            # → CLAUDE.md (project instructions)
│       ├── .gitignore           # → .gitignore
│       ├── .pre-commit-config.yaml  # → .pre-commit-config.yaml
│       ├── vscode-settings.json     # → .vscode/settings.json
│       ├── python_build.yml    # → .github/workflows/python_build.yml
│       ├── settings.json       # → .claude/settings.json
│       ├── init_remote_env.sh  # → .claude/scripts/init_remote_env.sh
│       ├── grant_python_heredoc.py  # → .claude/scripts/grant_python_heredoc.py
│       └── ruff_on_save.py     # → .claude/scripts/ruff_on_save.py
└── references/                 # Canonical configs and dependency versions
    ├── dependencies.md         # Approved package version master list
    ├── packaging.md            # pyproject.toml packaging standards
    └── tool-config.md          # pytest, ruff, coverage config
```

## How It Works

### Scaffolding (`/py:scaffold`)
1. Conducts a short interview (2 rounds max) to gather project requirements
2. Reads snippet files from `assets/snippets/` for requested components
3. Reads `references/dependencies.md` for pinned dependency versions
4. Generates the project structure with all requested components wired together

### Quality (auto-invoked)
- Activates automatically when writing, reviewing, or committing Python code
- Enforces line length (88 chars), modern type annotations, import organization
- Before commits: ruff format → ruff check → ty check → pytest

### Hooks (project-level templates)
Scaffolded projects get these hooks in `.claude/scripts/`, registered via `.claude/settings.json`:
- **`ruff_on_save.py`** (PostToolUse) — auto-runs `ruff format` on `.py` files after Edit/Write
- **`grant_python_heredoc.py`** (PreToolUse) — auto-grants `python <<<` heredoc commands

Users can customize these scripts per project as needed.

### Pytest (`/py:pytest`)
- Runs `pytest -v --durations=5 --timeout=180` in an isolated subagent
- Reports pass/fail summary, slowest tests, and failure details
- Use before commits or after completing a feature

## Key Conventions

- Package manager: `uv` (no setup.py, no requirements.txt)
- Project layout: `src/{project_name}/`
- Python: 3.13+
- Line length: 88 chars (hard limit 92, enforced by ruff)
- Linting: ruff + ty
- Testing: pytest (async-first)
- Config: pydantic-settings
- Docstrings: Google style
