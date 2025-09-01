from typing import Annotated

import typer

app = typer.Typer(help="A sample CLI\n\nThis is a multi-line help message.")


@app.command()
def docs(name: str = typer.Option(..., help="The name of the project")):
    """Generate docs for a project"""
    print(f"Generating docs for {name}")


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
