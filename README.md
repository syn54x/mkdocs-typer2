# mkdocs-typer2

A MkDocs plugin that automatically generates beautiful documentation for your Typer CLI applications.

## Features

- Seamlessly integrates with MkDocs and Material theme
- Automatically generates CLI documentation from your Typer commands
- Supports all Typer command features including arguments, options, and help text
- Easy to configure and use

## Installation

Install using pip:

```bash
pip install mkdocs-typer2
```

## Usage

1. Add the plugin to your `mkdocs.yml` file:

```yaml
plugins:
  - mkdocs-typer2
```

2. In your Markdown files, use the `:::typer` directive to generate documentation for your Typer CLI

```markdown
::: mkdocs-typer2
    :module: my_module
    :name: mycli
```

- The `:module:` option is required and specifies the module containing your Typer CLI application.  This is the *installed* module, not the directory.  I.e: If you app is located in `src/my_module/cli.py`, your `:module:` should typically be `my_module.cli`.
- The `:name:` option is optional and specifies the name of the CLI.  If left blank, your CLI will simply be named `CLI` in your documentation.

## Example

This repository is a good example of how to use the plugin.  We have a simple CLI located in `src/mkdocs_typer2/cli.py`.

The CLI's documentation is automatically generated using the block level directive in `docs/cli.md`:

```markdown
::: mkdocs-typer2
    :module: mkdocs_typer2.cli
    :name: mkdocs-typer2
```
