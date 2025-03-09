# mkdocs-typer2

[![PyPI version](https://badge.fury.io/py/mkdocs-typer2.svg)](https://badge.fury.io/py/mkdocs-typer2)
![Python 3.10 | 3.11 | 3.12 | 3.13](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue.svg)
![Ruff](https://img.shields.io/badge/linted%20by-ruff-FFC107.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://static.pepy.tech/badge/mkdocs-typer2)](https://pepy.tech/project/mkdocs-typer2)
[![codecov](https://codecov.io/gh/syn54x/mkdocs-typer2/branch/main/graph/badge.svg)](https://codecov.io/gh/syn54x/mkdocs-typer2)
[![Issues](https://img.shields.io/github/issues/syn54x/mkdocs-typer2)](https://github.com/syn54x/mkdocs-typer2/issues)

A MkDocs plugin that automatically generates beautiful documentation for your Typer CLI applications.

You might be wondering why there are two plugins for Typer. The [`mkdocs-typer`](https://github.com/bruce-szalwinski/mkdocs-typer) plugin is great, but it hasn't been updated in over a year, and there have been a number of changes to Typer since then. One important change is that Typer now has its own documentation generation system via the `typer <module> utils docs` command. This plugin simply leverages that system to generate the documentation for your Typer CLIs.

I created this plugin because the original plugin was no longer working for me, and I wanted to have a simple plugin that would work with the latest version of Typer. If the original `mkdocs-typer` plugin still works for you, there probably isn't a reason to switch. However, if you are looking for a plugin that will work with the latest version of Typer, this plugin is for you!

- [Read The Docs](https://syn54x.github.io/mkdocs-typer2/)
- [Check out a demo](https://syn54x.github.io/mkdocs-typer2/cli)

## Features

- Seamlessly integrates with MkDocs and Material theme
- Automatically generates CLI documentation from your Typer commands
- Supports all Typer command features including arguments, options, and help text
- Easy to configure and use
- `pretty` feature for encapsulating arguments & options inside tables instead of lists
- Global plugin configuration or per-documentation block configuration

## How It Works

The plugin leverages Typer's built-in documentation generation via the `typer <module> utils docs` command to create Markdown documentation. It then processes this Markdown content and integrates it into your MkDocs site.

The plugin works by:

1. Registering a Markdown extension that processes special directive blocks
2. Running the Typer documentation command on your specified module
3. Optionally reformatting the output to use tables for arguments and options (the "pretty" mode)
4. Integrating the resulting HTML into your MkDocs site

## Installation

Install using pip:

```bash
pip install mkdocs-typer2
```

### Requirements

- Python 3.10 or higher
- MkDocs 1.6.1 or higher
- Typer 0.12.5 or higher
- Pydantic 2.9.2 or higher

## Configuration

### Basic Configuration

Add the plugin to your `mkdocs.yml` file:

```yaml
plugins:
  - mkdocs-typer2
```

### Pretty Mode

The plugin offers a `pretty` option that can be set in your `mkdocs.yml` file to enable pretty documentation. This will use markdown tables to format the CLI options and arguments instead of lists:

```yaml
plugins:
  - mkdocs-typer2:
      pretty: true
```

## Usage

### Basic Usage

In your Markdown files, use the `::: mkdocs-typer2` directive to generate documentation for your Typer CLI:

```markdown
::: mkdocs-typer2
    :module: my_module
    :name: mycli
```

### Required Parameters

- `:module:` - The module containing your Typer CLI application. This is the *installed* module, not the directory path. For example, if your app is located in `src/my_module/cli.py`, your `:module:` should typically be `my_module.cli`.

### Optional Parameters

- `:name:` - The name of the CLI. If left blank, your CLI will simply be named `CLI` in your documentation.
- `:pretty:` - Set to `true` to enable pretty formatting for this specific documentation block, overriding the global setting.

## Advanced Usage

### Per-Block Pretty Configuration

You can override the global pretty setting for individual documentation blocks:

```markdown
::: mkdocs-typer2
    :module: my_module.cli
    :name: mycli
    :pretty: true
```

### Multiple CLI Documentation

You can document multiple CLIs in the same MkDocs site by using multiple directive blocks:

```markdown
# Main CLI

::: mkdocs-typer2
    :module: my_module.cli
    :name: mycli

# Admin CLI

::: mkdocs-typer2
    :module: my_module.admin
    :name: admin-cli
```

## Example

This repository is a good example of how to use the plugin. We have a simple CLI located in `src/mkdocs_typer2/cli.py`.

The CLI's documentation is automatically generated using the block level directive in `docs/cli.md`:

```markdown
::: mkdocs-typer2
    :module: mkdocs_typer2.cli
    :name: mkdocs-typer2
```

And the pretty version in `docs/cli-pretty.md`:

```markdown
::: mkdocs-typer2
    :module: mkdocs_typer2.cli
    :name: mkdocs-typer2
    :pretty: true
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
