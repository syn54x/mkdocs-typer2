from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

from .markdown import makeExtension
from .termynal_render import TermynalOptions


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
            config_options.Type(int, default=TermynalOptions.width),
        ),
        (
            "termynal_scheme",
            config_options.Type(str, default=TermynalOptions.scheme),
        ),
        (
            "termynal_dark_bg",
            config_options.Type(bool, default=TermynalOptions.dark_bg),
        ),
        (
            "termynal_buttons",
            config_options.Type(str, default=TermynalOptions.buttons),
        ),
        (
            "termynal_prompt",
            config_options.Type(str, default=TermynalOptions.prompt),
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
        (
            "termynal_subcommands",
            config_options.Type(int, default=TermynalOptions.subcommands),
        ),
    )

    def on_config(self, config, **kwargs) -> dict:
        config["markdown_extensions"].append(
            makeExtension(
                pretty=self.config["pretty"],
                engine=self.config["engine"],
                termynal=self.config["termynal"],
                width=self.config["termynal_width"],
                scheme=self.config["termynal_scheme"],
                dark_bg=self.config["termynal_dark_bg"],
                buttons=self.config["termynal_buttons"],
                prompt=self.config["termynal_prompt"],
                type_delay=self.config["termynal_type_delay"],
                line_delay=self.config["termynal_line_delay"],
                start_delay=self.config["termynal_start_delay"],
                subcommands=self.config["termynal_subcommands"],
            )
        )
        return config

    def on_pre_build(self, config, **kwargs) -> None:
        pass
