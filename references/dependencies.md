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

## ORM Component

```
sqlalchemy = ">=2.0.36,<3"
alembic = ">=1.14,<2"
asyncpg = ">=0.30,<1"
factory-boy = ">=3.3,<4"        # dev only
```

## API Component

```
fastapi = ">=0.115,<1"
uvicorn = {version = ">=0.32,<1", extras = ["standard"]}
```

## CLI Component

```
typer = ">=0.15,<1"
rich = ">=13.9,<14"
```

## Redis Component

```
redis = ">=5.2,<6"
fakeredis = ">=2.26,<3"         # dev only
```
