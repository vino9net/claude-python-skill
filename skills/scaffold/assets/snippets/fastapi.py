# API Component Snippets

Read this file before generating any API-related code. Use these exact patterns.

## src/{project_name}/main.py

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from {project_name}.api.router import api_router
from {project_name}.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("starting_up", version=settings.app_version)
    # Add startup logic here (e.g., DB pool init, cache warmup)
    yield
    # Add shutdown logic here
    logger.info("shutting_down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api/v1")
```

## src/{project_name}/api/router.py

```python
from fastapi import APIRouter

from {project_name}.api import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
```

## src/{project_name}/api/health.py

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

## config.py additions

```python
    # API
    app_name: str = "{project_name}"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]
```

## tests/conftest.py — API fixtures

Append these fixtures.

```python
import httpx
import pytest
from {project_name}.main import app


@pytest.fixture()
async def client() -> httpx.AsyncClient:
    """Async test client for FastAPI."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
```

## Directory additions

```
src/{project_name}/
├── main.py
└── api/
    ├── __init__.py
    ├── router.py
    └── health.py
```
