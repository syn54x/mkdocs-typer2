import re
from typing import List, Optional

from pydantic import BaseModel


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
    root = None

    # Find the root command name (# heading)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            root = CommandNode(name=line.replace("# ", "").replace("`", ""))

            # Capture description for root command
            desc_lines = []
            j = i + 1

            # Skip empty lines
            while j < len(lines) and not lines[j].strip():
                j += 1

            # Collect description lines until we hit a section marker or subcommand
            while (
                j < len(lines)
                and not lines[j].startswith("#")
                and not lines[j].startswith("**")
                and not lines[j].startswith("```")
            ):
                if lines[j].strip():  # Only add non-empty lines
                    desc_lines.append(lines[j].strip())
                j += 1

            if desc_lines:
                root.description = "\n".join(desc_lines)

            break

    if not root:
        # If no root command was found, create a default one
        root = CommandNode(name="Unknown Command")

    current_command = root
    current_section = None
    in_description = False
    desc_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("## `"):
            # New subcommand
            cmd_name = line.replace("##", "")
            new_cmd = CommandNode(name=cmd_name)
            root.subcommands.append(new_cmd)
            current_command = new_cmd
            in_description = True  # Start capturing description for this command
            desc_lines = []

        elif (
            in_description
            and not line.startswith("**")
            and not line.startswith("```")
            and i > 0
        ):
            # We're in description mode and not at a section marker yet
            if line.strip():  # Only add non-empty lines
                desc_lines.append(line.strip())

        elif line.startswith("```console"):
            # Usage section - end of description
            if in_description and desc_lines:
                current_command.description = "\n".join(desc_lines)
            in_description = False
            # Find the line with usage example
            j = i
            while j < len(lines) and "$ " not in lines[j]:
                j += 1
            if j < len(lines):
                current_command.usage = lines[j].replace("$ ", "")

        elif line.startswith("**Arguments**:"):
            # End of description section
            if in_description and desc_lines:
                current_command.description = "\n".join(desc_lines)
            in_description = False
            current_section = "arguments"

        elif line.startswith("**Options**:"):
            # End of description section
            if in_description and desc_lines:
                current_command.description = "\n".join(desc_lines)
            in_description = False
            current_section = "options"

        elif line.startswith("**Commands**:"):
            # End of description section
            if in_description and desc_lines:
                current_command.description = "\n".join(desc_lines)
            in_description = False

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

        i += 1

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
