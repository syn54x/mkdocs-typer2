"""Render a Typer/Click app's ``--help`` as termynal HTML blocks.

See the "Termynal Output Mode" section of the README for how this works and the
coupling to termynal's markup contract.
"""

import contextlib
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

    ``subcommands`` is a recursion depth: 0 renders only the root command's
    ``--help`` (the default), 1 adds its direct subcommands, 2 adds their
    subcommands, and so on; -1 renders every level (the full tree).
    """

    width: int = 80
    scheme: AnsiScheme = DEFAULT_ANSI_SCHEME
    dark_bg: bool = True
    buttons: ButtonStyle = DEFAULT_BUTTONS
    prompt: str = DEFAULT_PROMPT
    type_delay: Optional[int] = None
    line_delay: Optional[int] = None
    start_delay: Optional[int] = None
    subcommands: int = 0


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


#: Name of the private typer factory we swap to capture colored ``--help``.
#: Typer exposes no public injection point (see ``_colored_help``), so this is
#: guarded by ``test_typer_rich_console_hook_present`` in the contract tests.
TYPER_RICH_CONSOLE_HOOK = "_get_rich_console"


def _colored_help(command: click.core.Command, info_name: str, width: int = 80) -> str:
    """Return the command's ``--help`` text, colored when the app uses rich.

    Typer has no public API to render colored ``--help`` to a string: its
    ``rich_format_help()`` hardcodes ``console = _get_rich_console()`` with no
    console/file parameter to inject (``CliRunner`` drops rich color, and the
    env-var knobs are import-time + process-global). So we swap that private
    factory for a buffer-backed ``Console``. That console sets
    ``no_color=False`` so the captured help keeps its color even when
    ``NO_COLOR`` is set in the environment (e.g. ReadTheDocs): this is a build
    artifact converted to HTML, not interactive terminal output.

    If that private hook ever disappears (a future typer rename), we degrade
    safely: ``format_help`` runs with stdout redirected into the same buffer, so
    its output is captured monochrome instead of leaking to the console or
    crashing the build. ``test_typer_rich_console_hook_present`` fails loudly in
    CI when the hook is gone, and the colored-render test catches the silent
    drop to monochrome.
    """
    import typer.rich_utils as ru
    from rich.console import Console

    buf = io.StringIO()
    ctx = click.Context(command, info_name=info_name)
    formatter = ctx.make_formatter()

    original = getattr(ru, TYPER_RICH_CONSOLE_HOOK, None)
    if original is not None:
        setattr(
            ru,
            TYPER_RICH_CONSOLE_HOOK,
            lambda stderr=False: Console(  # noqa: ARG005
                force_terminal=True,
                color_system="standard",
                no_color=False,
                width=width,
                file=buf,
                highlight=False,
            ),
        )
        try:
            command.format_help(ctx, formatter)
        finally:
            setattr(ru, TYPER_RICH_CONSOLE_HOOK, original)
    else:
        # Hook gone: render without it, but redirect stdout so any rich output
        # that bypasses our buffer is captured (monochrome) rather than leaked.
        with contextlib.redirect_stdout(buf):
            command.format_help(ctx, formatter)

    rich_text = buf.getvalue()
    if rich_text.strip():
        return rich_text
    return formatter.getvalue()


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
    """Coerce out-of-domain ``scheme``/``buttons``/``width``/``subcommands``.

    ``scheme``/``buttons`` are free-text directive input, so an unknown value
    falls back to its default; ``width`` is floored at 1 since a non-positive
    value would make ``rich.Console`` raise or render nothing; ``subcommands``
    (a recursion depth) keeps any negative value as the -1 "all levels" sentinel.
    """
    scheme = options.scheme if options.scheme in ANSI_SCHEMES else DEFAULT_ANSI_SCHEME
    buttons = options.buttons if options.buttons in BUTTONS else DEFAULT_BUTTONS
    width = max(1, options.width)
    subcommands = options.subcommands if options.subcommands >= 0 else -1
    if (
        scheme == options.scheme
        and buttons == options.buttons
        and width == options.width
        and subcommands == options.subcommands
    ):
        return options
    return replace(
        options, scheme=scheme, buttons=buttons, width=width, subcommands=subcommands
    )


def _subcommand_blocks(
    command: click.core.Command,
    display: str,
    options: TermynalOptions,
    depth: int,
) -> List[str]:
    """Render up to ``depth`` levels of non-hidden subcommands, depth-first.

    Each subcommand is emitted as its own stacked block before its own children,
    so the output reads parent-then-descendants. Hidden commands are skipped at
    every level, matching ``--help``. A negative ``depth`` recurses without limit
    (it never decrements to 0, so it stops only at leaf commands).
    """
    if depth == 0 or not _is_click_group(command):
        return []
    blocks: List[str] = []
    for sub_name, subcommand in command.commands.items():
        if getattr(subcommand, "hidden", False):
            continue
        sub_display = f"{display} {sub_name}".strip()
        blocks.append(
            _one_block(subcommand, sub_display, options, style=STACKED_BLOCK_STYLE)
        )
        blocks.extend(_subcommand_blocks(subcommand, sub_display, options, depth - 1))
    return blocks


def _select_command(root: click.core.Command, path: str) -> click.core.Command:
    """Walk ``path`` (space-separated subcommand names) down from ``root``.

    ``"plot"`` selects the ``plot`` subcommand; ``"plot sub"`` selects ``sub``
    under it. Explicit selection renders the command even if it is hidden.
    """
    command = root
    for part in path.split():
        commands = getattr(command, "commands", None)
        if not isinstance(commands, dict) or part not in commands:
            raise ValueError(
                f"Unknown termynal :command: path {path!r}: "
                f"{command.name or 'the root command'!r} has no subcommand "
                f"{part!r}."
            )
        command = commands[part]
    return command


def render_termynal_html(
    module: str,
    name: str,
    options: Optional[TermynalOptions] = None,
    *,
    command: str = "",
) -> str:
    """Render ``module``'s app help as one or more termynal HTML blocks.

    By default the resolved app's ``--help`` is rendered as a single block. When
    ``command`` is given (a space-separated subcommand path, e.g. ``"plot"`` or
    ``"plot sub"``), that subcommand is selected as the block's command instead,
    and ``options.subcommands`` recursion applies relative to it. Each extra
    level of ``options.subcommands`` adds a stacked block per non-hidden
    subcommand at that depth; at the default of 0 only the selected block is
    emitted (matching a bare ``<cmd> --help``).
    """
    options = _normalized(options or TermynalOptions())

    root = resolve_click_command(module, name)
    display = name or root.name or ""

    selected = root
    if command:
        selected = _select_command(root, command)
        display = f"{display} {command}".strip()

    blocks: List[str] = [_one_block(selected, display, options)]
    blocks.extend(_subcommand_blocks(selected, display, options, options.subcommands))

    return "\n".join(blocks)
