# Dependency Master List

This is the single source of truth for approved dependency versions.
When generating pyproject.toml, always use versions from this file.

## Update Process

To update versions: edit this file, then ask Claude to update any existing
pyproject.toml files in target projects.

## Core (always included)

```
pydantic = ">=2.10,<3"
python-dotenv = ">=1.0,<2"
```

## Dev / Test (always included)

```
pytest = ">=8.3,<9"
pytest-dotenv = ">= 0.5.2"
pytest-cov = ">=6.0,<7"
pytest-asyncio = ">=0.24,<1"
pytest-mock = ">= 3.14"
pytest-timeout = ">=2.4.0",
ruff = ">=0.14.10,<1"
ty = ">=0.0.14"
pre-commit = ">=4.0,<5"
```

## API Component

```
fastapi = ">=0.115,<1"
uvicorn = {version = ">=0.32,<1", extras = ["standard"]}
pydantic-settings = ">=2.7,<3",
structlog = ">=24.4,<26",
```

## CLI Component

```
typer = ">=0.15,<1"
rich = ">=13.9,<14"
```
