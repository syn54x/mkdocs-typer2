import re
import subprocess
import xml.etree.ElementTree as etree

import markdown
from markdown.blockprocessors import BlockProcessor

from .pretty import (
    build_tree_from_click_app,
    parse_markdown_to_tree,
    tree_to_markdown,
    tree_to_markdown_list,
)
from .termynal_render import TermynalOptions, render_termynal_html


def _directive_value(block: str, key: str) -> str | None:
    match = re.search(rf":{key}:\s*(\S+)", block)
    return match.group(1) if match else None


def _directive_line(block: str, key: str) -> str | None:
    """Like ``_directive_value`` but captures the rest of the line.

    Used for values that may contain spaces, such as a ``:command:`` path
    (``plot sub``).
    """
    match = re.search(rf":{key}:\s*(.+)", block)
    return match.group(1).strip() if match else None


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.lower()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    return default


def _as_int(value: str | None, default: int | None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class TyperExtension(markdown.Extension):
    def __init__(
        self,
        *args,
        pretty: bool | None = None,
        engine: str = "legacy",
        termynal: bool = False,
        width: int = TermynalOptions.width,
        scheme: str = TermynalOptions.scheme,
        dark_bg: bool = TermynalOptions.dark_bg,
        buttons: str = TermynalOptions.buttons,
        prompt: str = TermynalOptions.prompt,
        type_delay: int | None = TermynalOptions.type_delay,
        line_delay: int | None = TermynalOptions.line_delay,
        start_delay: int | None = TermynalOptions.start_delay,
        subcommands: int = TermynalOptions.subcommands,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretty = pretty
        self.engine = engine
        self.termynal = termynal
        # Termynal render options are bundled so they thread through as one
        # object instead of a kwarg list duplicated across Extension/Processor.
        self.termynal_options = TermynalOptions(
            width=width,
            scheme=scheme,
            dark_bg=dark_bg,
            buttons=buttons,
            prompt=prompt,
            type_delay=type_delay,
            line_delay=line_delay,
            start_delay=start_delay,
            subcommands=subcommands,
        )

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.parser.blockprocessors.register(
            TyperProcessor(
                md.parser,
                pretty=self.pretty,
                engine=self.engine,
                termynal=self.termynal,
                options=self.termynal_options,
            ),
            "typer",
            175,
        )


class TyperProcessor(BlockProcessor):
    def __init__(
        self,
        *args,
        pretty: bool | None = None,
        engine: str = "legacy",
        termynal: bool = False,
        options: TermynalOptions | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretty = pretty
        self.engine = engine
        self.termynal = termynal
        self.options = options or TermynalOptions()

    def test(self, parent, block):
        return block.strip().startswith(":::") and "mkdocs-typer2" in block

    def _resolve_termynal_options(self, block: str) -> TermynalOptions:
        """Build per-block options from the globals plus directive overrides."""
        base = self.options
        return TermynalOptions(
            width=_as_int(_directive_value(block, "width"), base.width),
            scheme=_directive_value(block, "scheme") or base.scheme,
            dark_bg=_as_bool(_directive_value(block, "dark_bg"), base.dark_bg),
            buttons=_directive_value(block, "buttons") or base.buttons,
            # Capture the rest of the line so a multi-word prompt (e.g. ``my $``)
            # is kept whole rather than truncated at the first token.
            prompt=_directive_line(block, "prompt") or base.prompt,
            type_delay=_as_int(_directive_value(block, "type_delay"), base.type_delay),
            line_delay=_as_int(_directive_value(block, "line_delay"), base.line_delay),
            start_delay=_as_int(
                _directive_value(block, "start_delay"), base.start_delay
            ),
            subcommands=_as_int(
                _directive_value(block, "subcommands"), base.subcommands
            ),
        )

    def run(self, parent, blocks):
        block = blocks.pop(0)

        # Extract options from the block
        module_match = re.search(r":module:\s*(\S+)", block)
        name_match = re.search(r":name:\s*(\S+)", block)
        pretty_match = re.search(r":pretty:\s*(\S+)", block)
        engine_match = re.search(r":engine:\s*(\S+)", block)
        if not module_match:
            raise ValueError("Module is required")

        module = module_match.group(1)
        name = name_match.group(1) if name_match else ""

        use_termynal = _as_bool(_directive_value(block, "termynal"), self.termynal)
        if use_termynal:
            html = render_termynal_html(
                module,
                name,
                self._resolve_termynal_options(block),
                command=_directive_line(block, "command") or "",
            )
            placeholder = self.parser.md.htmlStash.store(html)
            div = etree.SubElement(parent, "div")
            div.set("class", "termynal-typer-docs")
            div.text = placeholder
            return True

        # Determine if pretty formatting should be used
        # Block-level setting overrides global setting if present
        use_pretty = self.pretty  # Start with global setting
        if pretty_match:
            # Parse the block-level setting as a boolean
            block_pretty_value = pretty_match.group(1).lower()
            if block_pretty_value in ["true", "1", "yes"]:
                use_pretty = True
            elif block_pretty_value in ["false", "0", "no"]:
                use_pretty = False

        # Determine engine (legacy or native)
        use_engine = self.engine or "legacy"
        if engine_match:
            block_engine_value = engine_match.group(1).lower()
            if block_engine_value in ["legacy", "native"]:
                use_engine = block_engine_value
            else:
                raise ValueError("Engine must be 'legacy' or 'native'")

        if use_engine == "legacy":
            # Run typer command
            cmd = f"typer {module} utils docs --name {name}"
            # print(cmd)
            result = subprocess.run(cmd.split(), capture_output=True, text=True)

            if result.returncode == 0:
                if use_pretty:
                    md_content = self.pretty_output(result.stdout)
                else:
                    md_content = result.stdout
            else:
                return True
        else:
            md_content = self.native_output(module, name, use_pretty)

        html_output = markdown.markdown(md_content, extensions=["tables"])

        div = etree.SubElement(parent, "div")
        div.set("class", "typer-docs")
        div.extend(etree.fromstring(f"<div>{html_output}</div>"))

        return True

    def pretty_output(self, md_content: str) -> str:
        tree = parse_markdown_to_tree(md_content)
        return tree_to_markdown(tree)

    def native_output(self, module: str, name: str, pretty: bool) -> str:
        tree = build_tree_from_click_app(module, name)
        if pretty:
            return tree_to_markdown(tree)
        return tree_to_markdown_list(tree)


def makeExtension(**kwargs):
    return TyperExtension(**kwargs)
