"""Render a Typer/Click app's ``--help`` as termynal HTML blocks.

See the "Termynal Output Mode" section of the README for how this works and the
coupling to termynal's markup contract.
"""

import importlib
import io
from typing import List

import click

from .pretty import _is_click_group, _resolve_click_command


def _html_escape(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text.replace('"', "&quot;")


def _ansi_to_html(text: str, scheme: str, dark_bg: bool) -> str:
    """Convert ANSI output to balanced inline HTML spans joined with ``<br>``."""
    converter = None
    lines: List[str] = []
    for line in text.split("\n"):
        if "\x1b" not in line:
            lines.append(_html_escape(line))
            continue
        if converter is None:
            try:
                from ansi2html import Ansi2HTMLConverter
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Termynal output mode requires the 'termynal' extra. "
                    "Install it with: pip install 'mkdocs-typer2[termynal]'"
                ) from exc

            converter = Ansi2HTMLConverter(inline=True, scheme=scheme, dark_bg=dark_bg)
        lines.append(converter.convert(line, full=False))
    return "<br>".join(lines)


def _termynal_block_html(
    title: str, prompt: str, input_text: str, output_html: str, buttons: str = "macos"
) -> str:
    """Wrap a prompt line and output in termynal's ``data-ty`` markup."""
    return (
        f'<div class="termy" data-termynal data-ty-{buttons} '
        f'data-ty-title="{_html_escape(title)}">'
        f'<span data-ty="input" data-ty-prompt="{_html_escape(prompt)}">'
        f"{_html_escape(input_text)}</span>"
        f"<span data-ty>{output_html}</span>"
        f"</div>"
    )


def _colored_help(command: click.core.Command, info_name: str, width: int = 80) -> str:
    """Return the command's ``--help`` text, colored when the app uses rich."""
    formatter = None
    buf = io.StringIO()

    import typer.rich_utils as ru
    from rich.console import Console

    original = ru._get_rich_console
    ru._get_rich_console = lambda stderr=False: Console(  # noqa: ARG005
        force_terminal=True,
        color_system="standard",
        width=width,
        file=buf,
        highlight=False,
    )
    try:
        ctx = click.Context(command, info_name=info_name)
        formatter = ctx.make_formatter()
        command.format_help(ctx, formatter)
    finally:
        ru._get_rich_console = original

    rich_text = buf.getvalue()
    if rich_text.strip():
        return rich_text
    return formatter.getvalue() if formatter is not None else ""


def _resolve_app(module: str, name: str) -> click.core.Command:
    module_ref = importlib.import_module(module)
    app = getattr(module_ref, name, None) if name else None
    if app is None:
        app = getattr(module_ref, "app", None)
    if app is None:
        raise ValueError(f"Unable to resolve Typer/Click app from module '{module}'.")
    return _resolve_click_command(app)


def _one_block(
    command: click.core.Command,
    info_name: str,
    *,
    width: int,
    ansi_scheme: str,
    ansi_dark_bg: bool,
    prompt: str,
) -> str:
    help_text = _colored_help(command, info_name, width=width).rstrip("\n")
    output_html = _ansi_to_html(help_text, ansi_scheme, ansi_dark_bg)
    return _termynal_block_html(
        title=info_name,
        prompt=prompt,
        input_text=f"{info_name} --help",
        output_html=output_html,
    )


def render_termynal_html(
    module: str,
    name: str,
    *,
    width: int = 80,
    ansi_scheme: str = "xterm",
    ansi_dark_bg: bool = True,
    prompt: str = "$",
    recurse: bool = True,
) -> str:
    """Render ``module``'s app help as one or more termynal HTML blocks.

    The root command is always rendered; when ``recurse`` is true and the app is
    a group, each non-hidden direct subcommand is rendered as its own block.
    """
    command = _resolve_app(module, name)
    display = name or command.name or ""

    blocks: List[str] = [
        _one_block(
            command,
            display,
            width=width,
            ansi_scheme=ansi_scheme,
            ansi_dark_bg=ansi_dark_bg,
            prompt=prompt,
        )
    ]

    if recurse and _is_click_group(command):
        for sub_name, subcommand in command.commands.items():
            if getattr(subcommand, "hidden", False):
                continue
            blocks.append(
                _one_block(
                    subcommand,
                    f"{display} {sub_name}".strip(),
                    width=width,
                    ansi_scheme=ansi_scheme,
                    ansi_dark_bg=ansi_dark_bg,
                    prompt=prompt,
                )
            )

    return "\n".join(blocks)
