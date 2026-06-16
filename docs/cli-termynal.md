# CLI (Termynal)

This page renders the CLI's `--help` as an animated, colored
[termynal](https://github.com/termynal/termynal.py) terminal instead of Markdown
tables. By default only the root command is rendered; the `:subcommands:` option
sets how many levels of subcommands to stack below it (`-1` for the full tree).

Enable it per block with `:termynal: true` (or globally via the plugin's
`termynal: true`). Use `:command:` to render a specific subcommand instead of
the root (e.g. `:command: export`, or `:command: subapp sub-command` for a
nested one). The optional `:width:`, `:scheme:`, and `:dark_bg:` options control
the captured terminal width and color palette.

::: mkdocs-typer2
    :module: mkdocs_typer2.cli.cli
    :name: mkdocs-typer2
    :termynal: true
    :subcommands: 1
