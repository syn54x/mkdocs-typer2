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
    )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(
            makeExtension(
                pretty=self.config.get("pretty", False),
                engine=self.config.get("engine", "legacy"),
                termynal=self.config.get("termynal", False),
                width=self.config.get("width", 80),
            )
        )
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
