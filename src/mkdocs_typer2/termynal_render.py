"""Render a Typer/Click app's ``--help`` as termynal HTML blocks.

See the "Termynal Output Mode" section of the README for how this works and the
coupling to termynal's markup contract.
"""

import io
from dataclasses import dataclass, replace
from typing import Dict, List, Literal, Optional, Tuple, get_args

import click

from .pretty import _is_click_group, resolve_click_command

# --- termynal contract --------------------------------------------------------
# All option domains and the ``data-ty-*`` attribute names we emit live here as
# the single source of truth. ``tests/test_termynal_contract.py`` guards the
# attribute names against termynal's own CSS/JS, so they fail loudly if termynal
# ever renames them.

AnsiScheme = Literal[
    "ansi2html",
    "dracula",
    "mint-terminal",
    "osx",
    "osx-basic",
    "osx-solid-colors",
    "solarized",
    "xterm",
]
ANSI_SCHEMES: Tuple[str, ...] = get_args(AnsiScheme)
DEFAULT_ANSI_SCHEME: AnsiScheme = "xterm"

ButtonStyle = Literal["macos", "windows"]
BUTTONS: Tuple[str, ...] = get_args(ButtonStyle)
DEFAULT_BUTTONS: ButtonStyle = "macos"

DEFAULT_PROMPT = "$"

# termynal.js reads these per-element timing attributes at runtime (its
# constructor does ``getAttribute('data-ty-typeDelay')`` etc.). We emit them
# only when explicitly set, otherwise termynal's own defaults apply.
TIMING_ATTRS: Dict[str, str] = {
    "type_delay": "data-ty-typeDelay",
    "line_delay": "data-ty-lineDelay",
    "start_delay": "data-ty-startDelay",
}

# termynal styles ``[data-termynal]`` with padding but no margin, so stacked
# blocks would touch. This spaces them apart without imposing a margin on the
# boundary between the first/last block and surrounding page content.
STACKED_BLOCK_STYLE = "margin-top: 1.5rem;"


@dataclass
class TermynalOptions:
    """Resolved termynal render options (plugin config + per-directive overrides).

    ``scheme`` and ``buttons`` are validated at render time; an out-of-domain
    value (directive input is free text) falls back to its default.
    """

    width: int = 80
    scheme: AnsiScheme = DEFAULT_ANSI_SCHEME
    dark_bg: bool = True
    buttons: ButtonStyle = DEFAULT_BUTTONS
    prompt: str = DEFAULT_PROMPT
    type_delay: Optional[int] = None
    line_delay: Optional[int] = None
    start_delay: Optional[int] = None


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
    title: str,
    prompt: str,
    input_text: str,
    output_html: str,
    *,
    buttons: ButtonStyle = DEFAULT_BUTTONS,
    type_delay: Optional[int] = None,
    line_delay: Optional[int] = None,
    start_delay: Optional[int] = None,
    style: str = "",
) -> str:
    """Wrap a prompt line and output in termynal's ``data-ty`` markup.

    ``style`` is an optional inline style; the renderer uses it only to space
    *stacked* blocks apart (a lone block gets none, so spacing against
    surrounding page content stays the theme's concern). The timing arguments
    emit the matching ``data-ty-*`` attributes only when set, deferring to
    termynal's own defaults otherwise.
    """
    extra = ""
    if style:
        extra += f'style="{_html_escape(style)}" '
    delays = {
        "type_delay": type_delay,
        "line_delay": line_delay,
        "start_delay": start_delay,
    }
    for field, value in delays.items():
        if value is not None:
            extra += f'{TIMING_ATTRS[field]}="{int(value)}" '
    return (
        f'<div class="termy" data-termynal data-ty-{buttons} '
        f"{extra}"
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


def _one_block(
    command: click.core.Command,
    info_name: str,
    options: TermynalOptions,
    style: str = "",
) -> str:
    help_text = _colored_help(command, info_name, width=options.width).rstrip("\n")
    output_html = _ansi_to_html(help_text, options.scheme, options.dark_bg)
    return _termynal_block_html(
        title=info_name,
        prompt=options.prompt,
        input_text=f"{info_name} --help",
        output_html=output_html,
        buttons=options.buttons,
        type_delay=options.type_delay,
        line_delay=options.line_delay,
        start_delay=options.start_delay,
        style=style,
    )


def _normalized(options: TermynalOptions) -> TermynalOptions:
    """Coerce an out-of-domain ``scheme``/``buttons`` back to its default."""
    scheme = options.scheme if options.scheme in ANSI_SCHEMES else DEFAULT_ANSI_SCHEME
    buttons = options.buttons if options.buttons in BUTTONS else DEFAULT_BUTTONS
    if scheme == options.scheme and buttons == options.buttons:
        return options
    return replace(options, scheme=scheme, buttons=buttons)


def render_termynal_html(
    module: str,
    name: str,
    options: Optional[TermynalOptions] = None,
    *,
    recurse: bool = True,
) -> str:
    """Render ``module``'s app help as one or more termynal HTML blocks.

    The root command is always rendered; when ``recurse`` is true and the app is
    a group, each non-hidden direct subcommand is rendered as its own block.
    """
    options = _normalized(options or TermynalOptions())

    command = resolve_click_command(module, name)
    display = name or command.name or ""

    blocks: List[str] = [_one_block(command, display, options)]

    if recurse and _is_click_group(command):
        for sub_name, subcommand in command.commands.items():
            if getattr(subcommand, "hidden", False):
                continue
            blocks.append(
                _one_block(
                    subcommand,
                    f"{display} {sub_name}".strip(),
                    options,
                    style=STACKED_BLOCK_STYLE,
                )
            )

    return "\n".join(blocks)
