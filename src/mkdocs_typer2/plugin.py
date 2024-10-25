from mkdocs.plugins import BasePlugin

from .markdown import makeExtension


class MkdocsTyper(BasePlugin):
    # config_scheme = (
    #     (
    #         "cmd",
    #         config_options.Type(str, default="typer . utils docs"),
    #     ),
    # )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(makeExtension())
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
