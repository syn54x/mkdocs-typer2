import importlib
import re
from typing import List, Optional

import click
import typer
from pydantic import BaseModel, Field


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


class CommandEntry(BaseModel):
    name: str
    description: str = ""


class CommandNode(BaseModel):
    name: str
    description: str = ""
    usage: Optional[str] = None
    arguments: List[Argument] = Field(default_factory=list)
    options: List[Option] = Field(default_factory=list)
    subcommands: List["CommandNode"] = Field(default_factory=list)
    commands: List[CommandEntry] = Field(default_factory=list)


def build_tree_from_click_app(module: str, name: str) -> CommandNode:
    module_ref = importlib.import_module(module)
    app = None
    display_name = None
    if name:
        display_name = name
        app = getattr(module_ref, name, None)
    if app is None:
        app = getattr(module_ref, "app", None)
    if app is None:
        raise ValueError(f"Unable to resolve Typer app from module '{module}'.")
    command = _resolve_click_command(app)
    return _build_tree_from_click_command(command, display_name=display_name)


def _resolve_click_command(app: object) -> click.core.Command:
    if isinstance(app, click.core.Command):
        return app
    if isinstance(app, typer.Typer):
        return typer.main.get_command(app)
    raise ValueError("Resolved object is not a Typer or Click command.")


def _format_usage(usage_text: str) -> Optional[str]:
    if not usage_text:
        return None
    first_line = usage_text.splitlines()[0]
    if first_line.startswith("Usage: "):
        return first_line.replace("Usage: ", "", 1).strip()
    return first_line.strip()


def _format_option_name(option: click.Option) -> str:
    primary = ", ".join(option.opts)
    if option.secondary_opts:
        secondary = " / ".join(option.secondary_opts)
        return f"{primary} / {secondary}"
    return primary


def _format_option_default(option: click.Option) -> Optional[str]:
    if option.default is None:
        return None
    if isinstance(option.default, bool) and option.secondary_opts:
        if option.default is False:
            return option.secondary_opts[0].lstrip("-")
        return option.opts[0].lstrip("-") if option.opts else None
    return str(option.default)


def _get_short_help(command: click.core.Command) -> str:
    short_help = command.get_short_help_str()
    return short_help.strip() if short_help else ""


def _build_tree_from_click_command(
    command: click.core.Command,
    parent_ctx: Optional[click.Context] = None,
    display_name: Optional[str] = None,
) -> CommandNode:
    info_name = display_name or command.name or ""
    ctx = click.Context(command, info_name=info_name, parent=parent_ctx)
    node = CommandNode(
        name=info_name,
        description=(command.help or "").strip(),
        usage=_format_usage(ctx.get_usage()),
    )

    for param in command.params:
        if isinstance(param, click.Argument):
            arg_name = getattr(param, "human_readable_name", None) or param.name
            node.arguments.append(
                Argument(
                    name=arg_name,
                    description=(getattr(param, "help", "") or "").strip(),
                    required=param.required,
                )
            )
        elif isinstance(param, click.Option):
            node.options.append(
                Option(
                    name=_format_option_name(param),
                    description=(param.help or "").strip(),
                    required=param.required,
                    default=_format_option_default(param),
                    type=str(param.type) if param.type else None,
                )
            )

    if isinstance(command, click.core.Group):
        for subcommand in command.commands.values():
            node.commands.append(
                CommandEntry(
                    name=subcommand.name, description=_get_short_help(subcommand)
                )
            )
        for subcommand in command.commands.values():
            node.subcommands.append(
                _build_tree_from_click_command(subcommand, parent_ctx=ctx)
            )

    return node


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
                # Preserve the original line content, including empty lines for line breaks
                desc_lines.append(lines[j])
                j += 1

            if desc_lines:
                # Join with newlines to preserve line breaks, then strip trailing whitespace
                root.description = "\n".join(desc_lines)

            break

    if not root:
        # If no root command was found, create a default one
        root = CommandNode(name="Unknown Command")

    current_command = root
    current_section = None
    in_description = False
    desc_lines = []
    in_commands_section = False
    current_subcommand_parent = (
        None  # Track the parent subcommand for nested subcommands
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("## `"):
            # New subcommand (level 2)
            cmd_name = line.replace("##", "")
            new_cmd = CommandNode(name=cmd_name)
            root.subcommands.append(new_cmd)
            current_command = new_cmd
            current_subcommand_parent = (
                new_cmd  # This becomes the parent for nested subcommands
            )
            in_description = True  # Start capturing description for this command
            desc_lines = []
            in_commands_section = False

        elif line.startswith("### `"):
            # End description collection for parent subcommand if in progress
            if in_description and desc_lines and current_subcommand_parent:
                current_subcommand_parent.description = "\n".join(desc_lines).rstrip()
                in_description = False
            # New nested subcommand (level 3) - belongs to the most recent ## subcommand
            cmd_name = line.replace("###", "")
            new_cmd = CommandNode(name=cmd_name)
            if current_subcommand_parent:
                current_subcommand_parent.subcommands.append(new_cmd)
            else:
                # Fallback: if no parent, add to root (shouldn't happen in typer output)
                root.subcommands.append(new_cmd)
            current_command = new_cmd
            in_description = True  # Start capturing description for this command
            desc_lines = []
            in_commands_section = False

        elif (
            in_description
            and not line.startswith("**")
            and not line.startswith("```")
            and not line.startswith("#")
            and i > 0
        ):
            # We're in description mode and not at a section marker yet
            # Preserve the original line content, including empty lines for line breaks
            desc_lines.append(line)

        elif line.startswith("```console"):
            # Usage section - end of description
            if in_description and desc_lines:
                # Join with newlines to preserve line breaks, then strip trailing whitespace
                current_command.description = "\n".join(desc_lines).rstrip()
            in_description = False
            in_commands_section = False
            # Find the line with usage example
            j = i
            while j < len(lines) and "$ " not in lines[j]:
                j += 1
            if j < len(lines):
                current_command.usage = lines[j].replace("$ ", "")

        elif line.startswith("**Arguments**:"):
            # End of description section
            if in_description and desc_lines:
                # Join with newlines to preserve line breaks, then strip trailing whitespace
                current_command.description = "\n".join(desc_lines).rstrip()
            in_description = False
            current_section = "arguments"
            in_commands_section = False

        elif line.startswith("**Options**:"):
            # End of description section
            if in_description and desc_lines:
                # Join with newlines to preserve line breaks, then strip trailing whitespace
                current_command.description = "\n".join(desc_lines).rstrip()
            in_description = False
            current_section = "options"
            in_commands_section = False

        elif line.startswith("**Commands**:"):
            # End of description section, start commands section
            if in_description and desc_lines:
                # Join with newlines to preserve line breaks, then strip trailing whitespace
                current_command.description = "\n".join(desc_lines).rstrip()
            in_description = False
            current_section = None
            in_commands_section = True

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

        elif line.startswith("* `") and in_commands_section:
            # Parse command name and description
            match = re.match(r"\* `(.*?)`: (.*)", line)
            if match:
                cmd_name, cmd_desc = match.groups()
                current_command.commands.append(
                    CommandEntry(name=cmd_name, description=cmd_desc.strip())
                )
            else:
                # Fallback: just the name
                match = re.match(r"\* `(.*?)`:?", line)
                if match:
                    cmd_name = match.group(1)
                    current_command.commands.append(
                        CommandEntry(name=cmd_name, description="")
                    )

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

    def format_commands_table(commands: list[CommandEntry]) -> str:
        if not commands:
            return "*No commands available*"
        rows = [format_table_row("Name", "Description"), format_table_row("---", "---")]
        for cmd in commands:
            rows.append(format_table_row(f"`{cmd.name}`", cmd.description))
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
        "",
        "## Commands\n",
        format_commands_table(command_node.commands),
    ]

    # Add subcommands if they exist
    if command_node.subcommands:
        parts.extend(["", "## Subcommands"])

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
            # Recursively render nested subcommands
            if subcmd.subcommands:
                parts.extend(["", "#### Subcommands"])
                for nested_subcmd in subcmd.subcommands:
                    parts.extend(
                        [
                            "",
                            f"##### {nested_subcmd.name}",
                            "",
                            nested_subcmd.description
                            if nested_subcmd.description
                            else "*No description available*",
                            "",
                            "###### Usage",
                            format_usage(
                                f"{command_node.name} {subcmd.name} {nested_subcmd.name}",
                                nested_subcmd.usage,
                            ),
                            "",
                            "###### Arguments",
                            format_arguments_table(nested_subcmd.arguments),
                            "",
                            "###### Options",
                            format_options_table(nested_subcmd.options),
                        ]
                    )

    return "\n".join(parts)


def tree_to_markdown_list(command_node: CommandNode) -> str:
    def format_arguments_list(arguments: list[Argument]) -> str:
        if not arguments:
            return "*No arguments available*"
        lines = []
        for arg in arguments:
            line = f"* `{arg.name}`"
            if arg.description:
                line += f": {arg.description}"
            if arg.required:
                line += "  [required]"
            lines.append(line)
        return "\n".join(lines)

    def format_options_list(options: list[Option]) -> str:
        if not options:
            return "*No options available*"
        lines = []
        for opt in options:
            line = f"* `{opt.name}`"
            if opt.description:
                line += f": {opt.description}"
            if opt.required:
                line += "  [required]"
            elif opt.default:
                line += f"  [default: {opt.default}]"
            lines.append(line)
        return "\n".join(lines)

    def format_commands_list(commands: list[CommandEntry]) -> str:
        if not commands:
            return "*No commands available*"
        lines = []
        for cmd in commands:
            line = f"* `{cmd.name}`"
            if cmd.description:
                line += f": {cmd.description}"
            lines.append(line)
        return "\n".join(lines)

    def format_usage(usage: Optional[str]) -> str:
        if not usage:
            return "*No usage specified*"
        return f"`{usage}`"

    parts = [
        f"# {command_node.name}",
        "",
        command_node.description
        if command_node.description
        else "*No description available*",
        "",
        "## Usage\n",
        format_usage(command_node.usage),
        "",
        "## Arguments\n",
        format_arguments_list(command_node.arguments),
        "",
        "## Options\n",
        format_options_list(command_node.options),
        "",
        "## Commands\n",
        format_commands_list(command_node.commands),
    ]

    if command_node.subcommands:
        parts.extend(["", "## Subcommands"])

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
                    format_usage(subcmd.usage),
                    "",
                    "#### Arguments",
                    format_arguments_list(subcmd.arguments),
                    "",
                    "#### Options",
                    format_options_list(subcmd.options),
                ]
            )
            if subcmd.subcommands:
                parts.extend(["", "#### Subcommands"])
                for nested_subcmd in subcmd.subcommands:
                    parts.extend(
                        [
                            "",
                            f"##### {nested_subcmd.name}",
                            "",
                            nested_subcmd.description
                            if nested_subcmd.description
                            else "*No description available*",
                            "",
                            "###### Usage",
                            format_usage(nested_subcmd.usage),
                            "",
                            "###### Arguments",
                            format_arguments_list(nested_subcmd.arguments),
                            "",
                            "###### Options",
                            format_options_list(nested_subcmd.options),
                        ]
                    )

    return "\n".join(parts)
