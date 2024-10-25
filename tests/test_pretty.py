import pytest
from mkdocs_typer2.pretty import (
    CommandNode,
    Option,
    Argument,
    parse_markdown_to_tree,
    tree_to_markdown,
)


def test_parse_markdown_basic_command():
    markdown = """
# mycli
A test CLI tool

```console
$ mycli --help
```

**Arguments**:
* `name`: The name argument [required]

**Options**:
* `--verbose`: Enable verbose mode
* `--output`: Output file path [required]
"""

    result = parse_markdown_to_tree(markdown)

    assert result.name == "mycli"
    assert len(result.arguments) == 1
    assert result.arguments[0].name == "name"
    assert result.arguments[0].required

    assert len(result.options) == 2
    assert result.options[0].name == "--verbose"
    assert not result.options[0].required
    assert result.options[1].name == "--output"
    assert result.options[1].required


def test_tree_to_markdown_basic():
    cmd = CommandNode(
        name="mycli",
        description="A test CLI",
        usage="mycli --help",
        arguments=[Argument(name="input", description="Input file", required=True)],
        options=[
            Option(name="--verbose", description="Verbose output", required=False),
            Option(name="--format", description="Output format", default="json"),
        ],
    )

    markdown = tree_to_markdown(cmd)

    assert "# mycli" in markdown
    assert "A test CLI" in markdown
    assert "`mycli --help`" in markdown
    assert "`input`" in markdown
    assert "`--verbose`" in markdown
    assert "`--format`" in markdown
    assert "`json`" in markdown


def test_tree_to_markdown_with_subcommands():
    cmd = CommandNode(
        name="mycli",
        description="Root command",
        subcommands=[
            CommandNode(
                name="init",
                description="Initialize project",
                options=[Option(name="--force", description="Force init")],
            )
        ],
    )

    markdown = tree_to_markdown(cmd)

    assert "# mycli" in markdown
    assert "### init" in markdown
    assert "Initialize project" in markdown
    assert "`--force`" in markdown


def test_empty_tables():
    cmd = CommandNode(name="mycli", description="A test CLI")

    markdown = tree_to_markdown(cmd)

    assert "*No arguments available*" in markdown
    assert "*No options available*" in markdown


def test_option_with_default():
    markdown = """
# mycli

**Options**:
* `--style`: Output style default: no-caps
"""

    result = parse_markdown_to_tree(markdown)

    assert len(result.options) == 1
    assert result.options[0].name == "--style"
    assert result.options[0].default == "no-caps"


@pytest.mark.parametrize(
    "usage_text",
    [
        "```console\n$ mycli run\n```",
        "```console\n$ mycli run --help\n```",
    ],
)
def test_parse_usage_section(usage_text):
    markdown = f"""
# mycli

{usage_text}
"""
    result = parse_markdown_to_tree(markdown)
    assert result.usage is not None
    assert result.usage.startswith("mycli")
