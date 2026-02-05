# Tool Configuration

These are the canonical tool configuration sections for pyproject.toml.
Always include these exactly as shown. Merge into existing pyproject.toml if one exists.

## pytest

```toml
[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["tests"]
pythonpath = ["."]
filterwarnings = [
    "ignore::DeprecationWarning",
]
env_files = [".env"]
```

## coverage

```toml
[tool.coverage.run]
source = ["."]
omit = [
    "tests/*",
]
```

## ruff

```toml
[tool.ruff]
line-length = 92
indent-width = 4
exclude = [
    ".git",
    "__pycache__",
    "venv",
    ".venv",
]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "W",      # pycodestyle warnings
    "C",      # flake8-comprehensions + mccabe
    "I",      # isort
    "A",      # flake8-builtins
]
ignore = [
    "E203",   # whitespace before ':' (conflicts with some formatters)
    "E266",   # too many leading '#' for block comment
    "C901",   # function too complex (mccabe)
]
```