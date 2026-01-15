# Pretty Output

`pretty` controls formatting. `engine` selects how we build the object tree:

- `legacy`: parse Typer-generated markdown (deprecated)
- `native`: walk the Click command tree

## Engine Matrix

| pretty | engine | behavior |
| --- | --- | --- |
| false | legacy | emit Typer markdown as-is |
| true | legacy | legacy pretty output |
| false | native | native output with list items |
| true | native | native output with tables |

## Example

::: mkdocs-typer2
    :module: mkdocs_typer2.cli.cli
    :name: mkdocs-typer2
    :pretty: true
    :engine: native
