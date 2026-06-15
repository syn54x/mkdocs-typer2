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
    html = render_termynal_html("mkdocs_typer2.cli.cli", "mkdocs-typer2")

    # It is a termynal block.
    assert "data-termynal" in html
    # The fork's CLI is a Typer/rich app, so the help is colored.
    assert 'style="color:' in html
    # Colored spans must be balanced.
    assert html.count("<span") == html.count("</span>")


def test_render_termynal_html_recurses_into_subcommands():
    html = render_termynal_html("mkdocs_typer2.cli.cli", "mkdocs-typer2")

    # The root block plus one block per direct subcommand.
    assert html.count("data-termynal") >= 2
    # A known subcommand prompt line is present (recursion happened).
    assert "mkdocs-typer2 docs --help" in html


def test_render_termynal_html_plain_click_monochrome(monkeypatch):
    """A plain ``click.command`` app renders without raising (monochrome)."""
    module = types.ModuleType("_plain_click_app")

    @click.command()
    def cli():
        """A plain click command."""

    module.cli = cli
    monkeypatch.setitem(sys.modules, "_plain_click_app", module)

    html = render_termynal_html("_plain_click_app", "cli", recurse=False)

    assert "data-termynal" in html
    # Plain Click help is not colored.
    assert 'style="color:' not in html


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
        recurse=False,
    )
    assert "data-termynal" in html


def test_buttons_option_selects_window_chrome():
    macos = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(), recurse=False
    )
    windows = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(buttons="windows"),
        recurse=False,
    )
    assert "data-ty-macos" in macos and "data-ty-windows" not in macos
    assert "data-ty-windows" in windows and "data-ty-macos" not in windows


def test_invalid_buttons_falls_back_to_macos():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(buttons="bogus"),
        recurse=False,
    )
    assert "data-ty-macos" in html
    assert "data-ty-bogus" not in html


def test_prompt_option_changes_prompt_attribute():
    html = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(prompt=">>>"),
        recurse=False,
    )
    assert 'data-ty-prompt="&gt;&gt;&gt;"' in html
    assert 'data-ty-prompt="$"' not in html


def test_timing_attributes_emitted_only_when_set():
    default = render_termynal_html(
        "mkdocs_typer2.cli.cli", "mkdocs-typer2", TermynalOptions(), recurse=False
    )
    # No timing attributes unless explicitly configured (termynal defaults apply).
    assert "data-ty-typeDelay" not in default

    tuned = render_termynal_html(
        "mkdocs_typer2.cli.cli",
        "mkdocs-typer2",
        TermynalOptions(type_delay=10, line_delay=20, start_delay=30),
        recurse=False,
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
    )

    html = markdown.markdown(
        directive,
        extensions=["tables", TyperExtension(engine="native")],
    )

    assert "data-termynal" in html
    assert 'style="color:' in html
    # The htmlStash placeholder must be swapped back out (no leak).
    assert "wzxhzdk" not in html
