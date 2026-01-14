import typer

app = typer.Typer(name="subapp")


@app.command()
def sub_command(
    name: str = typer.Option(..., help="The name of the person to greet"),
):
    typer.echo(f"Sub command {name}")


@app.command()
def sub_command_2(
    name: str = typer.Option(..., help="The name of the person to greet"),
):
    typer.echo(f"Sub command 2 {name}")


if __name__ == "__main__":
    app()
