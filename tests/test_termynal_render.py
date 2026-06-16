"""Tests for the termynal output mode.

Covers the colored Typer render, the monochrome plain-Click fallback,
subcommand recursion, and the end-to-end ``htmlStash`` injection through the
full Python-Markdown pipeline.
"""

import sys
import types

import click
import markdown
import pytest

pytest.importorskip("ansi2html")  # requires the 'termynal' extra

from mkdocs_typer2.markdown import TyperExtension  # noqa: E402
from mkdocs_typer2.termynal_render import (  # noqa: E402
    TermynalOptions,
    render_termynal_html,
)


def test_render_termynal_html_typer_colored_and_balanced():
    # Depth 1 so a subcommand block (which carries colored type annotations) is
    # included; the root --help of this CLI is styled bold-only.
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(subcommands=1)
    )

    # It is a termynal block.
    assert "data-termynal" in html
    # The fork's CLI is a Typer/rich app, so the help is colored.
    assert 'style="color:' in html
    # Colored spans must be balanced.
    assert html.count("<span") == html.count("</span>")


def test_render_termynal_html_root_only_by_default():
    html = render_termynal_html("mkdocs_typer2.cli.cli", "mkdocs-typer2")

    # Default depth is 0: only the root command's --help, no subcommand blocks.
    assert html.count("data-termynal") == 1
    assert "mkdocs-typer2 docs --help" not in html


def test_render_termynal_html_recurses_into_subcommands():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(subcommands=1)
    )

    # The root block plus one block per direct subcommand.
    assert html.count("data-termynal") >= 2
    # A known subcommand prompt line is present (recursion happened).
    assert "mkdocs-typer2 docs --help" in html


def test_render_termynal_html_unlimited_depth_with_negative():
    full = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(subcommands=-1)
    )
    one_level = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(subcommands=1)
    )

    # -1 means "all levels", so it renders at least as many blocks as one level.
    assert full.count("data-termynal") >= one_level.count("data-termynal") >= 2


def test_command_selects_a_single_subcommand():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", command="docs"
    )

    # Exactly the selected command's --help, nothing else.
    assert html.count("data-termynal") == 1
    assert "mkdocs-typer2 docs --help" in html
    assert "mkdocs-typer2 export --help" not in html


def test_command_selects_nested_path():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", command="subapp sub-command"
    )

    assert html.count("data-termynal") == 1
    assert "mkdocs-typer2 subapp sub-command --help" in html


def test_command_subcommands_recurse_relative_to_selection():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(subcommands=1),
        command="subapp",
    )

    # The selected group plus its own direct subcommands.
    assert "mkdocs-typer2 subapp --help" in html
    assert "mkdocs-typer2 subapp sub-command --help" in html
    assert "mkdocs-typer2 subapp sub-command-2 --help" in html


def _register_nested_typer_app(monkeypatch):
    """A three-level Typer app (root -> middle -> inner -> leaf-cmd)."""
    import typer

    module = types.ModuleType("_nested_typer_app")
    inner = typer.Typer()

    @inner.command()
    def leaf_cmd():
        """A leaf command."""

    middle = typer.Typer()
    middle.add_typer(inner, name="inner")

    @middle.command()
    def middle_cmd():
        """A middle command."""

    app = typer.Typer()
    app.add_typer(middle, name="middle")
    module.app = app
    monkeypatch.setitem(sys.modules, "_nested_typer_app", module)


def test_command_selects_sub_subcommand(monkeypatch):
    _register_nested_typer_app(monkeypatch)
    html = render_termynal_html(
        "_nested_typer_app", "app", command="middle inner leaf-cmd"
    )

    assert html.count("data-termynal") == 1
    assert "app middle inner leaf-cmd --help" in html


def test_subcommands_recursion_reaches_sub_subcommands(monkeypatch):
    _register_nested_typer_app(monkeypatch)

    # Unlimited depth walks the whole tree, including the third level.
    full = render_termynal_html(
        "_nested_typer_app", "app", TermynalOptions(subcommands=-1)
    )
    assert "app middle inner leaf-cmd --help" in full

    # Depth 1 stops one level down, before the sub-subcommand.
    one_level = render_termynal_html(
        "_nested_typer_app", "app", TermynalOptions(subcommands=1)
    )
    assert "app middle --help" in one_level
    assert "app middle inner leaf-cmd --help" not in one_level


def test_command_unknown_path_raises():
    with pytest.raises(ValueError, match="no subcommand"):
        render_termynal_html("mkdocs_typer2.cli.cli", "mkdocs-typer2", command="nope")


def test_command_threads_through_directive():
    directive = (
        "::: mkdocs-typer2\n"
        "    :module: mkdocs_typer2.cli.cli\n"
        "    :name: mkdocs-typer2\n"
        "    :termynal: true\n"
        "    :command: subapp sub-command\n"
    )
    html = markdown.markdown(
        directive, extensions=["tables", TyperExtension(engine="native")]
    )
    assert "mkdocs-typer2 subapp sub-command --help" in html
    assert html.count("data-termynal") == 1


def test_render_termynal_html_plain_click_monochrome(monkeypatch):
    """A plain ``click.command`` app renders without raising (monochrome)."""
    module = types.ModuleType("_plain_click_app")

    @click.command()
    def cli():
        """A plain click command."""

    module.cli = cli
    monkeypatch.setitem(sys.modules, "_plain_click_app", module)

    html = render_termynal_html("_plain_click_app", "cli")

    assert "data-termynal" in html
    # Plain Click help is not colored.
    assert 'style="color:' not in html


def test_missing_rich_console_hook_renders_without_crash_or_leak(monkeypatch, capsys):
    """The safe-fallback branch: when typer's private console hook is absent,
    rendering must still emit a block via plain ``format_help`` without crashing
    or leaking help to stdout.

    A real typer *rename* also rewrites typer's own ``rich_format_help`` to the
    new name, so it can't be simulated by deleting the symbol (that just breaks
    typer internally). A plain Click command never touches the hook, so it
    exercises the ``else`` branch deterministically: it goes through the
    stdout-redirected path and falls back to the Click formatter.
    """
    import typer.rich_utils as ru

    from mkdocs_typer2.termynal_render import TYPER_RICH_CONSOLE_HOOK

    monkeypatch.delattr(ru, TYPER_RICH_CONSOLE_HOOK, raising=False)

    module = types.ModuleType("_plain_click_fallback_app")

    @click.command()
    def cli():
        """A plain click command."""

    module.cli = cli
    monkeypatch.setitem(sys.modules, "_plain_click_fallback_app", module)

    html = render_termynal_html("_plain_click_fallback_app", "cli")

    # Still a real block, monochrome, and nothing leaked to the console.
    assert "data-termynal" in html
    assert "cli --help" in html
    assert 'style="color:' not in html
    assert capsys.readouterr().out == ""


def test_scheme_changes_colors():
    from mkdocs_typer2.termynal_render import _ansi_to_html

    red = "\x1b[31mred\x1b[0m"
    assert "#cd0000" in _ansi_to_html(red, "xterm", True)
    assert "#c23621" in _ansi_to_html(red, "osx", True)


def test_invalid_scheme_falls_back_to_xterm():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(scheme="not-a-scheme"),
    )
    assert "data-termynal" in html


def test_non_positive_width_falls_back_to_safe_value():
    """A zero/negative width must not reach rich.Console (it would raise)."""
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(width=0),
    )
    assert "data-termynal" in html


def test_buttons_option_selects_window_chrome():
    macos = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions()
    )
    windows = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(buttons="windows"),
    )
    assert "data-ty-macos" in macos and "data-ty-windows" not in macos
    assert "data-ty-windows" in windows and "data-ty-macos" not in windows


def test_invalid_buttons_falls_back_to_macos():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(buttons="bogus"),
    )
    assert "data-ty-macos" in html
    assert "data-ty-bogus" not in html


def test_prompt_option_changes_prompt_attribute():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(prompt=">>>"),
    )
    assert 'data-ty-prompt="&gt;&gt;&gt;"' in html
    assert 'data-ty-prompt="$"' not in html


def test_multi_word_prompt_threads_through_directive():
    directive = (
        "::: mkdocs-typer2\n"
        "    :module: mkdocs_typer2.cli.cli\n"
        "    :name: mkdocs-typer2\n"
        "    :termynal: true\n"
        "    :prompt: my prompt\n"
    )
    html = markdown.markdown(
        directive, extensions=["tables", TyperExtension(engine="native")]
    )
    # The whole prompt is kept, not truncated at the first token.
    assert 'data-ty-prompt="my prompt"' in html


def test_timing_attributes_emitted_only_when_set():
    default = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions()
    )
    # No timing attributes unless explicitly configured (termynal defaults apply).
    assert "data-ty-typeDelay" not in default

    tuned = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(type_delay=10, line_delay=20, start_delay=30),
    )
    assert 'data-ty-typeDelay="10"' in tuned
    assert 'data-ty-lineDelay="20"' in tuned
    assert 'data-ty-startDelay="30"' in tuned


def test_buttons_and_delay_thread_through_directive():
    directive = (
        "::: mkdocs-typer2\n"
        "    :module: mkdocs_typer2.cli.cli\n"
        "    :name: mkdocs-typer2\n"
        "    :termynal: true\n"
        "    :buttons: windows\n"
        "    :type_delay: 5\n"
    )
    html = markdown.markdown(
        directive, extensions=["tables", TyperExtension(engine="native")]
    )
    assert "data-ty-windows" in html
    assert 'data-ty-typeDelay="5"' in html


def test_subcommands_depth_threads_through_directive():
    def render(extra=""):
        directive = (
            "::: mkdocs-typer2\n"
            "    :module: mkdocs_typer2.cli.cli\n"
            "    :name: mkdocs-typer2\n"
            "    :termynal: true\n"
            f"{extra}"
        )
        return markdown.markdown(
            directive, extensions=["tables", TyperExtension(engine="native")]
        )

    # Default (no :subcommands:) is root-only; :subcommands: 1 adds blocks.
    assert render().count("data-termynal") == 1
    assert render("    :subcommands: 1\n").count("data-termynal") >= 2


def test_scheme_option_through_directive():
    def render(extra=""):
        directive = (
            "::: mkdocs-typer2\n"
            "    :module: mkdocs_typer2.cli.cli\n"
            "    :name: mkdocs-typer2\n"
            "    :termynal: true\n"
            f"{extra}"
        )
        return markdown.markdown(
            directive, extensions=["tables", TyperExtension(engine="native")]
        )

    # The :scheme: option must thread through and change the rendered palette.
    assert render() != render("    :scheme: osx\n")


def test_termynal_end_to_end_through_markdown_pipeline():
    directive = (
        "::: mkdocs-typer2\n"
        "    :module: mkdocs_typer2.cli.cli\n"
        "    :name: mkdocs-typer2\n"
        "    :termynal: true\n"
        "    :subcommands: 1\n"
    )

    html = markdown.markdown(
        directive,
        extensions=["tables", TyperExtension(engine="native")],
    )

    assert "data-termynal" in html
    assert 'style="color:' in html
    # The htmlStash placeholder must be swapped back out (no leak).
    assert "wzxhzdk" not in html
