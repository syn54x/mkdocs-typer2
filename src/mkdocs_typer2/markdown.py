import re
import markdown
import subprocess
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor


class TyperExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.parser.blockprocessors.register(TyperProcessor(md.parser), "typer", 175)


class TyperProcessor(BlockProcessor):
    def test(self, parent, block):
        return block.strip().startswith(":::") and "mkdocs-typer2" in block

    def run(self, parent, blocks):
        block = blocks.pop(0)
        print("Processing block:", block)

        # Extract options from the block
        module_match = re.search(r":module:\s*(\S+)", block)
        name_match = re.search(r":name:\s*(\S+)", block)

        if not module_match:
            raise ValueError("Module is required")

        module = module_match.group(1)
        name = name_match.group(1) if name_match else ""

        # Run typer command
        cmd = f"typer {module} utils docs --name {name}"
        print(cmd)
        result = subprocess.run(cmd.split(), capture_output=True, text=True)

        if result.returncode == 0:
            html_output = markdown.markdown(result.stdout)
            div = etree.SubElement(parent, "div")
            div.set("class", "typer-docs")
            div.extend(etree.fromstring(f"<div>{html_output}</div>"))

        return True


def makeExtension(**kwargs):
    return TyperExtension(**kwargs)
