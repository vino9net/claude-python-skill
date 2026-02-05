# Packaging & Distribution

## Making a Project Installable

Always include a `[build-system]` in every scaffolded project (required for `project.scripts`
entry points and to avoid uv warnings). Add/ensure these sections exist in pyproject.toml:

### Build System

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Project Metadata (ensure these fields are populated)

```toml
[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.13"
authors = [
    {name = "Team Name", email = "team@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
```

### Dev Dependencies

Use `dependency-groups` (NOT `tool.uv.dev-dependencies`, which is deprecated):

```toml
[dependency-groups]
dev = [
    "pytest>=8.3,<9",
    "pytest-cov>=6.0,<7",
    "pytest-asyncio>=0.24,<1",
    "pytest-mock>=3.14",
    "pytest-timeout>=2.4.0",
    "pytest-dotenv>=0.5.2",
    "ruff>=0.14.10,<1",
    "ty>=0.0.14",
    "pre-commit>=4.0,<5",
]
```

### Package Discovery (src layout)

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/{project_name}"]
```

### Optional Dependencies for Consumers

If the project has optional features, expose them so consumers can do
`pip install {project_name}[api]`:

```toml
[project.optional-dependencies]
api = ["fastapi>=0.115,<1", "uvicorn[standard]>=0.32,<1"]
all = ["{project_name}[api]"]
```

### Entry Points

For CLI tools:

```toml
[project.scripts]
{project_name} = "{project_name}.cli:app"
```

## PEP 561 Type Stub Support

Always include `src/{project_name}/py.typed` (empty file) so that ty and other type
checkers recognize the package as typed.
