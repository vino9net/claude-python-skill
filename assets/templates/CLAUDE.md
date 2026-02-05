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

```
1. ruff format .
2. ruff check . --fix
3. ruff check .
4. ty check
5. pytest -v --timeout=180
```
