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


class TyperExtension(markdown.Extension):
    def __init__(
        self,
        *args,
        pretty: bool | None = None,
        engine: str = "legacy",
        termynal: bool = False,
        width: int = 80,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretty = pretty
        self.engine = engine
        self.termynal = termynal
        self.width = width

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.parser.blockprocessors.register(
            TyperProcessor(
                md.parser,
                pretty=self.pretty,
                engine=self.engine,
                termynal=self.termynal,
                width=self.width,
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
        width: int = 80,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretty = pretty
        self.engine = engine
        self.termynal = termynal
        self.width = width

    def test(self, parent, block):
        return block.strip().startswith(":::") and "mkdocs-typer2" in block

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

        termynal_match = re.search(r":termynal:\s*(\S+)", block)
        width_match = re.search(r":width:\s*(\S+)", block)
        use_termynal = self.termynal
        if termynal_match:
            value = termynal_match.group(1).lower()
            if value in ["true", "1", "yes"]:
                use_termynal = True
            elif value in ["false", "0", "no"]:
                use_termynal = False
        width = self.width
        if width_match:
            try:
                width = int(width_match.group(1))
            except ValueError:
                pass

        if use_termynal:
            from .termynal_render import render_termynal_html

            html = render_termynal_html(module, name, width=width)
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
