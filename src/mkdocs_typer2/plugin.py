from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

from .markdown import makeExtension


class MkdocsTyper(BasePlugin):
    config_scheme = (
        (
            "pretty",
            config_options.Type(bool, default=False),
        ),
    )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(
            makeExtension(pretty=self.config.get("pretty", False))
        )
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
