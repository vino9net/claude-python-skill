# Packaging & Distribution

## Making a Project Installable

When the user wants the project to be pip-installable or used as a library by other projects,
add/ensure these sections exist in pyproject.toml:

### Build System

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
```

### Project Metadata (ensure these fields are populated)

```toml
[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
authors = [
    {name = "Team Name", email = "team@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
```

### Package Discovery (src layout)

```toml
[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
where = ["."]
include = ["{project_name}*"]
exclude = ["tests", "tmp"]
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

Always include `src/{project_name}/py.typed` (empty file) so that mypy and other type
checkers recognize the package as typed.
