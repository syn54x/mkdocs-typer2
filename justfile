@default:
    just --list

sync:
    uv sync
    pre-commit install

rm:
    rm -rf .venv

test *ARGS:
    uv run pytest {{ARGS}}

serve:
    uv run mkdocs serve
