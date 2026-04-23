__all__ = ("MkdocsTyper",)


def __getattr__(name: str):
    if name == "MkdocsTyper":
        from .plugin import MkdocsTyper

        return MkdocsTyper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals(), "MkdocsTyper"})
