# Claude Python Skill (Plugin: `py`)

A Claude Code plugin for scaffolding Python projects, enforcing quality standards, and running tests.

## Plugin Structure

This is a Claude Code plugin providing three skills:

| Skill | Command | Description |
|-------|---------|-------------|
| **scaffold** | `/py:scaffold` | Generate barebone Python projects |
| **quality** | *(auto-invoked)* | Coding style, linting, type checking, line length |
| **pytest** | `/py:pytest` | Run test suite in isolated subagent |

## Directory Layout

```
.
├── .claude-plugin/
│   └── plugin.json              # Plugin definition (name: "py")
├── skills/
│   ├── scaffold/SKILL.md        # /py:scaffold — project scaffolding (self-contained)
│   ├── quality/SKILL.md         # Auto-invoked quality standards
│   └── pytest/SKILL.md          # /py:pytest — test runner (context: fork)
└── references/                  # Dependency versions, packaging & tool config
    ├── dependencies.md          # Approved package version master list
    ├── packaging.md             # pyproject.toml packaging standards
    └── tool-config.md           # pytest, ruff, coverage config
```

## How It Works

### Scaffolding (`/py:scaffold`)
- Asks for project name and description, then generates a complete project skeleton
- All templates, dependency versions, and tool configs are inlined in the SKILL.md
- No external file reads required — fully self-contained

### Quality (auto-invoked)
- Activates automatically when writing, reviewing, or committing Python code
- Enforces line length (88 chars), modern type annotations, import organization
- Before commits: ruff format → ruff check → ty check → pytest

### Hooks (project-level templates)
Scaffolded projects get these hooks in `.claude/scripts/`, registered via `.claude/settings.json`:
- **`ruff_on_save.py`** (PostToolUse) — auto-runs `ruff format` on `.py` files after Edit/Write
- **`grant_python_heredoc.py`** (PermissionRequest) — auto-grants `python <<<` heredoc commands

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
