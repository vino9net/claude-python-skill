# ORM Component Snippets

Read this file before generating any ORM-related code. Use these exact patterns.

## src/{project_name}/db/session.py

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from {project_name}.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## src/{project_name}/db/base.py

```python
from datetime import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention for constraints (required for alembic autogenerate)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
```

## config.py additions

Add these fields to the existing Settings class:

```python
    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/{project_name}"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    test_database_url: str = "postgresql+asyncpg://localhost:5432/{project_name}_test"
```

## tests/conftest.py — ORM fixtures

Append these fixtures. Do NOT replace existing conftest content.

```python
import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from {project_name}.config import settings
from {project_name}.db.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Session-scoped async engine pointing at the test database."""
    eng = create_async_engine(settings.test_database_url, echo=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session that rolls back after each test."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# --- factory-boy base ---
# Usage: subclass ModelFactory for each model
#
#   class UserFactory(ModelFactory):
#       class Meta:
#           model = User
#       name = factory.Faker("name")

import factory


class ModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        # Override in each test module or via fixture:
        #   ModelFactory._meta.sqlalchemy_session = db_session
```

## alembic/env.py

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from {project_name}.config import settings
from {project_name}.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Directory additions

```
src/{project_name}/db/
├── __init__.py
├── base.py
└── session.py
alembic/
├── env.py
├── script.py.mako
└── versions/
    └── .gitkeep
alembic.ini
```
