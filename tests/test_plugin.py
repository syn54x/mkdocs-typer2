from mkdocs_typer2.plugin import MkdocsTyper
from mkdocs_typer2.markdown import TyperExtension


def test_plugin_on_config():
    plugin = MkdocsTyper()
    # Initialize with empty markdown_extensions list
    config = {"markdown_extensions": []}

    result = plugin.on_config(config)

    assert "markdown_extensions" in result
    assert len(result["markdown_extensions"]) == 1
    # Check if the added extension is an instance of TyperExtension
    assert isinstance(result["markdown_extensions"][0], TyperExtension)


def test_plugin_on_config_with_existing_extensions():
    plugin = MkdocsTyper()
    # Initialize with some existing extensions
    existing_extension = "existing_extension"
    config = {"markdown_extensions": [existing_extension]}

    result = plugin.on_config(config)

    assert "markdown_extensions" in result
    assert len(result["markdown_extensions"]) == 2
    assert existing_extension == result["markdown_extensions"][0]
    assert isinstance(result["markdown_extensions"][1], TyperExtension)


def test_plugin_on_pre_build():
    plugin = MkdocsTyper()
    config = {}

    # Should not raise any exceptions
    plugin.on_pre_build(config)
