import re
import markdown
import subprocess
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor

from .pretty import parse_markdown_to_tree, tree_to_markdown


class TyperExtension(markdown.Extension):
    def __init__(self, *args, pretty: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pretty = pretty

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.parser.blockprocessors.register(
            TyperProcessor(md.parser, pretty=self.pretty), "typer", 175
        )


class TyperProcessor(BlockProcessor):
    def __init__(self, *args, pretty: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pretty = pretty

    def test(self, parent, block):
        return block.strip().startswith(":::") and "mkdocs-typer2" in block

    def run(self, parent, blocks):
        block = blocks.pop(0)
        print("Processing block:", block)

        # Extract options from the block
        module_match = re.search(r":module:\s*(\S+)", block)
        name_match = re.search(r":name:\s*(\S+)", block)
        pretty_match = re.search(r":pretty:\s*(\S+)", block)
        if not module_match:
            raise ValueError("Module is required")

        module = module_match.group(1)
        name = name_match.group(1) if name_match else ""

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

        # Run typer command
        cmd = f"typer {module} utils docs --name {name}"
        # print(cmd)
        result = subprocess.run(cmd.split(), capture_output=True, text=True)

        if result.returncode == 0:
            if use_pretty:
                md_content = self.pretty_output(result.stdout)
            else:
                md_content = result.stdout

            html_output = markdown.markdown(md_content, extensions=["tables"])

            div = etree.SubElement(parent, "div")
            div.set("class", "typer-docs")
            div.extend(etree.fromstring(f"<div>{html_output}</div>"))

        return True

    def pretty_output(self, md_content: str) -> str:
        tree = parse_markdown_to_tree(md_content)
        return tree_to_markdown(tree)


def makeExtension(**kwargs):
    return TyperExtension(**kwargs)
