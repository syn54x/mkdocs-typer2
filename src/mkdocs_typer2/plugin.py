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
            "termynal_width",
            config_options.Type(int, default=80),
        ),
        (
            "termynal_scheme",
            config_options.Type(str, default="xterm"),
        ),
        (
            "termynal_dark_bg",
            config_options.Type(bool, default=True),
        ),
        (
            "termynal_buttons",
            config_options.Type(str, default="macos"),
        ),
        (
            "termynal_prompt",
            config_options.Type(str, default="$"),
        ),
        (
            "termynal_type_delay",
            config_options.Optional(config_options.Type(int)),
        ),
        (
            "termynal_line_delay",
            config_options.Optional(config_options.Type(int)),
        ),
        (
            "termynal_start_delay",
            config_options.Optional(config_options.Type(int)),
        ),
    )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(
            makeExtension(
                pretty=self.config.get("pretty", False),
                engine=self.config.get("engine", "legacy"),
                termynal=self.config.get("termynal", False),
                width=self.config.get("termynal_width", 80),
                scheme=self.config.get("termynal_scheme", "xterm"),
                dark_bg=self.config.get("termynal_dark_bg", True),
                buttons=self.config.get("termynal_buttons", "macos"),
                prompt=self.config.get("termynal_prompt", "$"),
                type_delay=self.config.get("termynal_type_delay"),
                line_delay=self.config.get("termynal_line_delay"),
                start_delay=self.config.get("termynal_start_delay"),
            )
        )
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
