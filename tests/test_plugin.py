import pytest

from mkdocs_typer2.plugin import MkdocsTyper
from mkdocs_typer2.markdown import TyperExtension, _as_bool, _as_int


@pytest.mark.parametrize(
    "value, expected",
    [("true", True), ("YES", True), ("0", False), ("no", False)],
)
def test_as_bool_recognized_values(value, expected):
    assert _as_bool(value, default=not expected) is expected


@pytest.mark.parametrize("value", [None, "maybe", ""])
def test_as_bool_falls_back_to_default(value):
    # Unrecognized (or missing) input keeps the supplied default.
    assert _as_bool(value, default=True) is True
    assert _as_bool(value, default=False) is False


def test_as_int_parses_and_falls_back():
    assert _as_int("42", default=1) == 42
    assert _as_int("-1", default=0) == -1
    # Non-integer and missing input keep the default.
    assert _as_int("abc", default=7) == 7
    assert _as_int(None, default=7) == 7
    assert _as_int("abc", default=None) is None


def test_plugin_on_config():
    plugin = MkdocsTyper()
    plugin.load_config({})
    # Initialize with empty markdown_extensions list
    config = {"markdown_extensions": []}

    result = plugin.on_config(config)

    assert "markdown_extensions" in result
    assert len(result["markdown_extensions"]) == 1
    # Check if the added extension is an instance of TyperExtension
    assert isinstance(result["markdown_extensions"][0], TyperExtension)


def test_plugin_on_config_with_existing_extensions():
    plugin = MkdocsTyper()
    plugin.load_config({})
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
            "termynal_subcommands": -1,
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
    assert options.subcommands == -1
    # Unspecified options fall back to their defaults.
    assert options.scheme == "xterm"
    assert options.line_delay is None


def test_plugin_on_pre_build():
    plugin = MkdocsTyper()
    config = {}

    # Should not raise any exceptions
    plugin.on_pre_build(config)
