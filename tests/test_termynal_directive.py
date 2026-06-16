"""Tests for the termynal directive-parsing helpers.

These coerce free-text directive values (``:width:``, ``:dark_bg:`` …) for the
termynal output mode and need no optional extra, so they run unconditionally.
"""

import pytest

from mkdocs_typer2.markdown import _as_bool, _as_int


@pytest.mark.parametrize(
    "value, expected",
    [("true", True), ("YES", True), ("0", False), ("no", False)],
)
def test_as_bool_recognized_values(value, expected):
    assert _as_bool(value, default=not expected) is expected


@pytest.mark.parametrize("value", [None, "maybe", ""])
def test_as_bool_falls_back_to_default(value):
    # Unrecognized (or missing) input keeps the supplied default.
    assert _as_bool(value, default=True) is True
    assert _as_bool(value, default=False) is False


def test_as_int_parses_and_falls_back():
    assert _as_int("42", default=1) == 42
    assert _as_int("-1", default=0) == -1
    # Non-integer and missing input keep the default.
    assert _as_int("abc", default=7) == 7
    assert _as_int(None, default=7) == 7
    assert _as_int("abc", default=None) is None
