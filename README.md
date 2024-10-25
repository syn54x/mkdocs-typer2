# mkdocs-typer2

A MkDocs plugin that automatically generates beautiful documentation for your Typer CLI applications.

You might be wondering why there are two plugins for Typer.  The [`mkdocs-typer`](https://github.com/bruce-szalwinski/mkdocs-typer) plugin is great, but it hasn't been updated in over a year, and there have been a number of changes to Typer since then.  One important change is that Typer now has it's own documentation generation system via the `typer <module> utils docs` command.  This plugin simply leverages that system to generate the documentation for your Typer CLIs.

I created this plugin because the original plugin was no longer working for me, and I wanted to have a simple plugin that would work with the latest version of Typer.  If the original `mkdocs-typer` plugin still works for you, there probably isn't a reason to switch.  However, if you are looking for a plugin that will work with the latest version of Typer, this plugin is for you!

- [Read The Docs](https://syn54x.github.io/mkdocs-typer2/)
- [Check out a demo](https://syn54x.github.io/mkdocs-typer2/cli)

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
