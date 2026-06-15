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


def test_plugin_termynal_config_threads_through():
    plugin = MkdocsTyper()
    errors, warnings = plugin.load_config(
        {
            "termynal": True,
            "termynal_width": 100,
            "termynal_buttons": "windows",
            "termynal_type_delay": 5,
        }
    )
    assert not errors and not warnings

    config = {"markdown_extensions": []}
    plugin.on_config(config)
    extension = config["markdown_extensions"][0]

    assert extension.termynal is True
    options = extension.termynal_options
    assert options.width == 100
    assert options.buttons == "windows"
    assert options.type_delay == 5
    # Unspecified options fall back to their defaults.
    assert options.scheme == "xterm"
    assert options.line_delay is None


def test_plugin_on_pre_build():
    plugin = MkdocsTyper()
    config = {}

    # Should not raise any exceptions
    plugin.on_pre_build(config)
