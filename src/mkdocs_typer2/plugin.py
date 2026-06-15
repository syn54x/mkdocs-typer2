from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

from .markdown import makeExtension


class MkdocsTyper(BasePlugin):
    config_scheme = (
        (
            "pretty",
            config_options.Type(bool, default=False),
        ),
        (
            "engine",
            config_options.Type(str, default="legacy"),
        ),
        (
            "termynal",
            config_options.Type(bool, default=False),
        ),
        (
            "width",
            config_options.Type(int, default=80),
        ),
        (
            "scheme",
            config_options.Type(str, default="xterm"),
        ),
        (
            "dark_bg",
            config_options.Type(bool, default=True),
        ),
    )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(
            makeExtension(
                pretty=self.config.get("pretty", False),
                engine=self.config.get("engine", "legacy"),
                termynal=self.config.get("termynal", False),
                width=self.config.get("width", 80),
                scheme=self.config.get("scheme", "xterm"),
                dark_bg=self.config.get("dark_bg", True),
            )
        )
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
