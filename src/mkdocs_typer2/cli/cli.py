from enum import Enum
from typing import Annotated

import click
import typer

from .sub_cli import app as sub_app


class ExportFormat(str, Enum):
    json = "json"
    yaml = "yaml"
    markdown = "markdown"


app = typer.Typer(help="A sample CLI\n\nThis is a multi-line help message.")

app.add_typer(sub_app, name="subapp")


@app.command()
def docs(name: str = typer.Option(..., help="The name of the project")):
    """Generate docs for a project"""
    print(f"Generating docs for {name}")


@app.command()
def export(
    detail: str = typer.Option(
        "full",
        click_type=click.Choice(["full", "minimal"]),
        help="Documentation detail level",
    ),
    format: ExportFormat = typer.Option(ExportFormat.json, help="Export format"),
    retries: int = typer.Option(1, help="Number of export attempts"),
    config: str = typer.Option(
        "mkdocs.yml", metavar="PATH", help="Path to config file"
    ),
):
    """Export project documentation"""
    print(
        f"Exporting as {format.value} ({detail}) "
        f"with {retries} retries from {config}"
    )


@app.command(hidden=True)
def hello(
    name: Annotated[str, typer.Argument(..., help="The name of the person to greet")],
    caps: Annotated[
        bool, typer.Option("--caps/--no-caps", help="Whether to capitalize the name")
    ] = False,
    color: Annotated[
        str, typer.Option("--color", help="The color of the output")
    ] = None,
):
    """Some docstring content"""
    _str = ""
    if caps:
        _str = f"Hello {name.capitalize()}"
    else:
        _str = f"Hello {name}"

    if color:
        typer.echo(f"[{color}]{_str}[/{color}]")
    else:
        typer.echo(_str)


if __name__ == "__main__":
    app()
