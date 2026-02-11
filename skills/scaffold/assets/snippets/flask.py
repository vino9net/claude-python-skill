# Flask API Component Snippets

Read this file before generating any Flask API-related code. Use these exact patterns.

## src/{project_name}/main.py

```python
import structlog
from flask import Flask

from {project_name}.api.health import health_bp
from {project_name}.config import settings

logger = structlog.get_logger()


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(health_bp, url_prefix="/api/v1/health")
    logger.info("app_created", version=settings.app_version)
    return app


app = create_app()
```

## src/{project_name}/api/health.py

```python
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("")
def health_check():
    return jsonify(status="ok")
```

## config.py additions

```python
    # API
    app_name: str = "{project_name}"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
```

## tests/conftest.py — API fixtures

Append these fixtures.

```python
import pytest
from {project_name}.main import create_app


@pytest.fixture()
def client():
    """Synchronous test client for Flask."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
```

## Directory additions

```
src/{project_name}/
├── main.py
└── api/
    ├── __init__.py
    └── health.py
```
