import re
from pydantic import BaseModel
from typing import List, Optional


class Option(BaseModel):
    name: str
    description: str
    type: Optional[str] = None
    required: bool = False
    default: Optional[str] = None


class Argument(BaseModel):
    name: str
    description: str
    required: bool = False


class CommandNode(BaseModel):
    name: str
    description: str = ""
    usage: Optional[str] = None
    arguments: List[Argument] = []
    options: List[Option] = []
    subcommands: List["CommandNode"] = []


def parse_markdown_to_tree(content: str) -> CommandNode:
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            root = CommandNode(name=lines[i].replace("# ", ""))
            break

    current_command = root
    current_section = None

    for line in lines[1:]:
        if line.startswith("## `"):
            # New subcommand
            cmd_name = line.replace("## `", "").replace("`", "")
            new_cmd = CommandNode(name=cmd_name)
            root.subcommands.append(new_cmd)
            current_command = new_cmd

        elif line.startswith("```console"):
            # Usage section
            usage_line = next(lines[i] for i, line in enumerate(lines) if "$ " in line)
            current_command.usage = usage_line.replace("$ ", "")

        elif line.startswith("**Arguments**:"):
            current_section = "arguments"

        elif line.startswith("**Options**:"):
            current_section = "options"

        elif line.startswith("* `") and current_section == "options":
            # Parse option
            match = re.match(r"\* `(.*?)`: (.*?)(?:\s+\[(\w+)\])?$", line)
            if match:
                name, desc, modifier = match.groups()
                option = Option(
                    name=name,
                    description=desc.strip(),
                    required=modifier == "required",
                    default="no-caps" if "default: no-caps" in desc else None,
                )
                current_command.options.append(option)

        elif line.startswith("* `") and current_section == "arguments":
            # Parse argument
            match = re.match(r"\* `(.*?)`: (.*?)(?:\s+\[(\w+)\])?$", line)
            if match:
                name, desc, modifier = match.groups()
                argument = Argument(
                    name=name, description=desc.strip(), required=modifier == "required"
                )
                current_command.arguments.append(argument)

    return root


def tree_to_markdown(command_node: CommandNode) -> str:
    def format_table_row(*cells):
        return f"| {' | '.join(cells)} |"

    def format_arguments_table(arguments: list[Argument]) -> str:
        if not arguments:
            return "*No arguments available*"

        rows = [format_table_row("Name", "Description", "Required")]
        rows.append(format_table_row("---", "---", "---"))

        for arg in arguments:
            rows.append(
                format_table_row(
                    f"`{arg.name}`", arg.description, "Yes" if arg.required else "No"
                )
            )

        return "\n".join(rows)

    def format_options_table(options: list[Option]) -> str:
        if not options:
            return "*No options available*"

        rows = [format_table_row("Name", "Description", "Required", "Default")]
        rows.append(format_table_row("---", "---", "---", "---"))

        for opt in options:
            rows.append(
                format_table_row(
                    f"`{opt.name}`",
                    opt.description,
                    "Yes" if opt.required else "No",
                    f"`{opt.default}`" if opt.default else "-",
                )
            )

        return "\n".join(rows)

    def format_usage(cmd_name: str, usage: Optional[str]) -> str:
        if not usage:
            return "*No usage specified*"

        return f"`{usage}`"

    # Build the markdown content
    parts = [
        f"# {command_node.name}",
        "",
        command_node.description
        if command_node.description
        else "*No description available*",
        "",
        "## Usage\n",
        format_usage(command_node.name, command_node.usage),
        "",
        "## Arguments\n",
        format_arguments_table(command_node.arguments),
        "",
        "## Options\n",
        format_options_table(command_node.options),
    ]

    # Add subcommands if they exist
    if command_node.subcommands:
        parts.extend(["", "## Sub Commands"])

        for subcmd in command_node.subcommands:
            parts.extend(
                [
                    "",
                    f"### {subcmd.name}",
                    "",
                    subcmd.description
                    if subcmd.description
                    else "*No description available*",
                    "",
                    "#### Usage",
                    format_usage(f"{command_node.name} {subcmd.name}", subcmd.usage),
                    "",
                    "#### Arguments",
                    format_arguments_table(subcmd.arguments),
                    "",
                    "#### Options",
                    format_options_table(subcmd.options),
                ]
            )

    return "\n".join(parts)
