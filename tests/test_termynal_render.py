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
from mkdocs_typer2.termynal_render import render_termynal_html  # noqa: E402


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
