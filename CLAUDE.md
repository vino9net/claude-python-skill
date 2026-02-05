# Agent Python Skill

This is a Claude Code skill (used via the Claude Code CLI or Claude App) for scaffolding Python projects and enforcing development standards.

## What This Skill Does

The `python-dev` skill covers two areas:

1. **Scaffolding** — generates new Python projects or adds components (ORM, API, CLI, Redis) to existing ones
2. **Development standards** — enforces coding style, linting (ruff), type checking (ty), testing (pytest), and a pre-commit quality gate workflow

## Directory Layout

```
.
├── SKILL.md                    # Skill definition and workflow (entry point)
├── assets/
│   ├── snippets/               # Code templates for each component
│   │   ├── api.py              # FastAPI component patterns
│   │   ├── orm.py              # SQLAlchemy/Alembic component patterns
│   │   └── cli.py              # Typer CLI component patterns
│   └── templates/              # Files copied into scaffolded projects
│       ├── .gitignore          # → .gitignore
│       ├── .pre-commit-config.yaml  # → .pre-commit-config.yaml
│       ├── vscode-settings.json     # → .vscode/settings.json
│       ├── python_build.yml    # → .github/workflows/python_build.yml
│       ├── settings.json       # → .claude/settings.json
│       ├── init_remote_env.sh  # → .claude/scripts/init_remote_env.sh
│       └── grant_python_heredoc.py  # → .claude/scripts/grant_python_heredoc.py
└── references/                 # Canonical configs and dependency versions
    ├── dependencies.md         # Approved package version master list
    ├── packaging.md            # pyproject.toml packaging standards
    └── tool-config.md          # pytest, ruff, coverage config
```

## How It Works

### Scaffolding
1. `SKILL.md` is the entry point — Claude reads it when the skill is triggered.
2. It conducts a short interview (2 rounds max) to gather project requirements.
3. It reads snippet files from `assets/snippets/` for the requested components.
4. It reads `references/dependencies.md` for pinned dependency versions.
5. It generates the project structure with all requested components wired together.

### Development
- The skill also activates when writing, reviewing, or committing Python code.
- During development: write clean code, but do not run linters.
- Before commits: run `ruff format` → `ruff check --fix` → `ruff check` → `ty check` → `pytest`.

## Key Conventions

- Package manager: `uv` (no setup.py, no requirements.txt)
- Project layout: `src/{project_name}/`
- Python: 3.13+
- Linting: ruff + ty
- Testing: pytest (async-first)
- Config: pydantic-settings
- Docstrings: Google style
