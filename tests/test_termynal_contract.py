"""Drift guard: every ``data-ty`` token we emit must also appear in termynal's
own output, so a future termynal markup change fails loudly here.
"""

import pytest

from mkdocs_typer2.termynal_render import (
    BUTTONS,
    TIMING_ATTRS,
    _termynal_block_html,
)

pytest.importorskip("termynal.markdown")

CONTRACT_TOKENS = [
    'class="termy"',
    "data-termynal",
    "data-ty-macos",
    "data-ty-title=",
    'data-ty="input"',
    'data-ty-prompt="$"',
    "<span data-ty>",
]


def _termynal_reference_markup() -> str:
    from termynal.markdown import Termynal, escape, parse_config_from_dict

    termynal = Termynal(parse_config_from_dict({"title": "demo"}))
    return termynal.convert(escape("$ demo --help\nhello"))


@pytest.mark.parametrize("token", CONTRACT_TOKENS)
def test_emitted_markup_matches_termynal_contract(token: str) -> None:
    ours = _termynal_block_html("demo", "$", "demo --help", "hello")
    reference = _termynal_reference_markup()

    assert token in ours, f"our renderer stopped emitting {token!r}"
    assert token in reference, (
        f"termynal no longer emits {token!r} — its markup contract drifted; "
        "update _termynal_block_html in termynal_render.py to match."
    )


@pytest.mark.parametrize("buttons", BUTTONS)
def test_button_attrs_match_termynal_css(buttons: str) -> None:
    """The window-chrome attributes we emit must be the ones termynal styles."""
    from termynal.markdown import get_default_css

    attr = f"data-ty-{buttons}"
    assert attr in get_default_css(), (
        f"termynal CSS no longer styles {attr!r}; the button contract drifted — "
        "update BUTTONS in termynal_render.py to match."
    )


@pytest.mark.parametrize("attr", sorted(TIMING_ATTRS.values()))
def test_timing_attrs_match_termynal_js(attr: str) -> None:
    """The timing attributes we emit must be the ones termynal.js reads."""
    from termynal.markdown import get_default_js

    # termynal.js reads these via getAttribute(`data-ty-typeDelay`) etc., built
    # from a `data-ty` prefix + the suffix; the suffix is the literal in source.
    suffix = attr[len("data-ty") :]
    assert suffix in get_default_js(), (
        f"termynal.js no longer reads {attr!r}; the timing contract drifted — "
        "update TIMING_ATTRS in termynal_render.py to match."
    )
