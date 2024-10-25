import pytest
from typer.testing import CliRunner
from mkdocs_typer2.cli import app

runner = CliRunner()


def test_docs_command():
    result = runner.invoke(app, ["docs", "--name", "test-project"])
    assert result.exit_code == 0
    assert "Generating docs for test-project" in result.stdout


@pytest.mark.parametrize(
    "name,caps,color,expected",
    [
        ("john", False, None, "Hello john"),
        ("john", True, None, "Hello John"),
        ("john", False, "red", "[red]Hello john[/red]"),
        ("john", True, "blue", "[blue]Hello John[/blue]"),
    ],
)
def test_hello_command(name, caps, color, expected):
    args = ["hello", name]
    if caps:
        args.append("--caps")
    if color:
        args.extend(["--color", color])

    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert expected in result.stdout
