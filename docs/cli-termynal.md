# CLI (Termynal)

This page renders the CLI's `--help` as an animated, colored
[termynal](https://github.com/termynal/termynal.py) terminal instead of Markdown
tables. The root command is rendered first, followed by one block per direct
subcommand.

Enable it per block with `:termynal: true` (or globally via the plugin's
`termynal: true`). The optional `:width:`, `:scheme:`, and `:dark_bg:` options
control the captured terminal width and color palette.

::: mkdocs-typer2
    :module: mkdocs_typer2.cli.cli
    :name: mkdocs-typer2
    :termynal: true
