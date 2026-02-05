# py — Python Development Plugin for Claude Code

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin that scaffolds Python projects, enforces quality standards, and runs tests.

## TL;DR

Install from the marketplace:

1. Run `claude` to start Claude Code
2. Type `/plugins` to open the plugin manager
3. Navigate to **Marketplaces** → **Add Marketplace**
4. Enter `vino9net/vino9-claude-marketplace` as the source
5. Browse and enable the **python-dev** plugin

Or install manually:

```bash
# 1. Clone
git clone https://github.com/vino9net/claude-python-skill.git ~/tools/claude-python-skill

# 2. Add to your Claude Code settings (~/.claude/settings.json)
#    { "skills": ["~/tools/claude-python-skill"] }

# 3. Use it
/py:scaffold          # create a new Python project
/py:pytest            # run tests before committing
                      # quality standards apply automatically
```

## Skills

| Skill | Command | Invocation |
|-------|---------|------------|
| **scaffold** | `/py:scaffold` | User types the command |
| **quality** | — | Claude auto-invokes when writing Python |
| **pytest** | `/py:pytest` | User types the command |

### `/py:scaffold`

Generates new Python projects with a standard `src/` layout, CI, Docker, and tooling pre-configured. Adds components to existing projects.

Available components:

| Component | Stack | What Gets Added |
|-----------|-------|-----------------|
| **orm** | SQLAlchemy 2 + Alembic | `db/`, `alembic/`, DB fixtures |
| **api** | FastAPI + Uvicorn | `api/`, health check, test client |
| **cli** | Typer + Rich | `cli.py`, pyproject script entry |
| **redis** | redis-py | `cache/`, fakeredis fixtures |

Claude walks you through a short interview (2 rounds max), then generates the project.

### `quality` (auto-invoked)

Activates when writing, reviewing, or committing Python code:

- **Line length**: 88 chars target (92 hard limit enforced by ruff)
- **Type annotations**: modern syntax (`str | None`, not `Optional[str]`)
- **Pre-commit gates**: ruff format → ruff check → ty check → pytest

### Project Hooks (via scaffold)

Scaffolded projects include these hooks in `.claude/scripts/`, customizable per project:

| Hook | Event | What it does |
|------|-------|--------------|
| `ruff_on_save.py` | PostToolUse (Edit/Write) | Auto-runs `ruff format` on `.py` files |
| `grant_python_heredoc.py` | PreToolUse (Bash) | Auto-grants `python <<<` heredoc commands |

### `/py:pytest`

Runs the test suite in an isolated subagent (keeps your main context clean):

```
uv run pytest -v --durations=5 --timeout=180
```

Reports back: pass/fail summary, slowest 5 tests, and failure tracebacks.

## Installation

Clone and reference in your Claude Code settings:

```bash
git clone https://github.com/you/claude-python-skill.git ~/tools/claude-python-skill
```

### User-level (`~/.claude/settings.json`)

```json
{
  "skills": [
    "~/tools/claude-python-skill"
  ]
}
```

### Project-level (`.claude/settings.json`)

```json
{
  "skills": [
    "~/tools/claude-python-skill"
  ]
}
```

## Generated Project Structure

```
my_project/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── .python-version
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

Components add more directories (e.g. `db/`, `api/`, `cli.py`, `cache/`) as needed.

## Conventions

| Area | Choice |
|------|--------|
| Package manager | `uv` |
| Layout | `src/{name}/` |
| Python | 3.13+ |
| Line length | 88 chars (92 hard limit) |
| Linting | ruff (lint + format) + ty |
| Testing | pytest, pytest-asyncio |
| Config | pydantic-settings |
| Docstrings | Google style |
| Pre-commit | Always included |

## License

Internal tooling — no license specified.
