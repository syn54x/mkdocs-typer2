import pytest
import markdown
from mkdocs_typer2.markdown import TyperExtension, TyperProcessor
from unittest.mock import patch
import xml.etree.ElementTree as etree


def test_typer_extension_initialization():
    extension = TyperExtension()
    md = markdown.Markdown()
    extension.extendMarkdown(md)
    assert "typer" in md.parser.blockprocessors


def test_typer_processor_test_method():
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)

    # Should return True for valid blocks
    valid_block = ":::mkdocs-typer2\n    :module: test_module"
    assert processor.test(None, valid_block) is True

    # Should return False for invalid blocks
    invalid_block = "Some random text"
    assert processor.test(None, invalid_block) is False


@pytest.mark.parametrize(
    "block,expected_module,expected_name",
    [
        (
            ":::mkdocs-typer2\n    :module: test_module\n    :name: test_name",
            "test_module",
            "test_name",
        ),
        (":::mkdocs-typer2\n    :module: test_module", "test_module", ""),
    ],
)
def test_typer_processor_run_success(block, expected_module, expected_name):
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)
    parent = etree.Element("div")  # Create a real XML element instead of MagicMock
    blocks = [block]

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "# Test Output"

        result = processor.run(parent, blocks)

        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert expected_module in cmd
        if expected_name:
            assert expected_name in cmd

        # Verify the output was added to the parent
        assert len(parent.findall("div")) == 1
        assert parent.find("div").get("class") == "typer-docs"


def test_typer_processor_run_missing_module():
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)
    parent = etree.Element("div")  # Create a real XML element here too
    blocks = [":::mkdocs-typer2\n    :name: test_name"]

    with pytest.raises(ValueError, match="Module is required"):
        processor.run(parent, blocks)


@pytest.mark.parametrize(
    "global_pretty,block_pretty,should_use_pretty",
    [
        (True, None, True),  # Global pretty enabled, no block level setting
        (False, None, False),  # Global pretty disabled, no block level setting
        (False, True, True),  # Global pretty disabled, block level enabled
        (True, False, False),  # Global pretty enabled, block level disabled
    ],
)
def test_typer_processor_pretty_option(global_pretty, block_pretty, should_use_pretty):
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser, pretty=global_pretty)
    parent = etree.Element("div")

    # Build block with or without pretty option
    block = ":::mkdocs-typer2\n    :module: test_module"
    if block_pretty is not None:
        block += f"\n    :pretty: {str(block_pretty).lower()}"

    blocks = [block]

    with patch("subprocess.run") as mock_run, patch.object(
        processor, "pretty_output"
    ) as mock_pretty_output:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "# Test Output"
        mock_pretty_output.return_value = "# Pretty Test Output"

        processor.run(parent, blocks)

        if should_use_pretty:
            mock_pretty_output.assert_called_once()
        else:
            mock_pretty_output.assert_not_called()


def test_typer_processor_invalid_engine_raises():
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)
    parent = etree.Element("div")
    blocks = [":::mkdocs-typer2\n    :module: test_module\n    :engine: nope"]

    with pytest.raises(ValueError, match="Engine must be 'legacy' or 'native'"):
        processor.run(parent, blocks)


def test_typer_processor_legacy_failure_returns_true():
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser, engine="legacy")
    parent = etree.Element("div")
    blocks = [":::mkdocs-typer2\n    :module: test_module"]

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""

        result = processor.run(parent, blocks)

    assert result is True
    assert parent.find("div") is None


@pytest.mark.parametrize("pretty_value", [True, False])
def test_typer_processor_native_pretty_branches(pretty_value):
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser, engine="native", pretty=pretty_value)
    parent = etree.Element("div")
    block = ":::mkdocs-typer2\n    :module: test_module"
    if pretty_value:
        block += "\n    :pretty: true"
    blocks = [block]

    with patch.object(processor, "native_output") as mock_native_output:
        mock_native_output.return_value = "# Native Output"
        result = processor.run(parent, blocks)

    assert result is True
    mock_native_output.assert_called_once()


def test_typer_processor_pretty_output():
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)
    output = processor.pretty_output("# mycli")
    assert "# mycli" in output


@pytest.mark.parametrize("pretty_value", [True, False])
def test_typer_processor_native_output(pretty_value):
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser)
    output = processor.native_output("mkdocs_typer2.cli.cli", "app", pretty_value)
    assert "# app" in output


@pytest.mark.parametrize(
    "global_engine,block_engine,expected_engine",
    [
        ("legacy", None, "legacy"),
        ("native", None, "native"),
        ("legacy", "native", "native"),
        ("native", "legacy", "legacy"),
    ],
)
def test_typer_processor_engine_option(global_engine, block_engine, expected_engine):
    md = markdown.Markdown()
    processor = TyperProcessor(md.parser, engine=global_engine)
    parent = etree.Element("div")

    block = ":::mkdocs-typer2\n    :module: test_module"
    if block_engine is not None:
        block += f"\n    :engine: {block_engine}"

    blocks = [block]

    with patch("subprocess.run") as mock_run, patch.object(
        processor, "native_output"
    ) as mock_native_output:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "# Test Output"
        mock_native_output.return_value = "# Native Output"

        processor.run(parent, blocks)

        if expected_engine == "native":
            mock_native_output.assert_called_once()
            mock_run.assert_not_called()
        else:
            mock_run.assert_called_once()
            mock_native_output.assert_not_called()
