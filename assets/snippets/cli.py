# CLI Component Snippets

## src/{project_name}/cli.py

```python
import typer
from rich.console import Console

from {project_name}.config import settings

app = typer.Typer(
    name=settings.app_name if hasattr(settings, "app_name") else "{project_name}",
    help="{project_name} CLI",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"[bold]{project_name}[/bold] v0.1.0")


if __name__ == "__main__":
    app()
```

## pyproject.toml additions

```toml
[project.scripts]
{project_name} = "{project_name}.cli:app"
```
