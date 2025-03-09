@default:
    just --list

sync *ARGS:
    uv sync {{ARGS}}
    pre-commit install

rm:
    rm -rf .venv
    rm uv.lock

test *ARGS:
    uv run pytest {{ARGS}}

serve:
    uv run mkdocs serve

test-with-version VERSION:
    just rm
    just sync -p {{VERSION}}
    uv run -p {{VERSION}} pytest

test-py:
    just test-with-version 3.10
    just test-with-version 3.11
    just test-with-version 3.12
    just test-with-version 3.13
    just rm
    just sync
