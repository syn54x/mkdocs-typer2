# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-06-16

### Added

- `termynal` output mode: render a CLI's `--help` as an animated, colored [termynal](https://github.com/termynal/termynal.py) terminal instead of Markdown tables, enabled per block (`:termynal: true`) or globally (`termynal: true`). The app is introspected in-process (no subprocess) and its colored `--help` is converted to termynal markup; by default only the root command is rendered. Requires the optional `[termynal]` extra (`pip install "mkdocs-typer2[termynal]"`); using the mode without it raises a clear install hint ([#35](https://github.com/syn54x/mkdocs-typer2/pull/35)).
- Termynal `:command:` directive option: render a specific subcommand's `--help` instead of the root, selected by a space-separated path (e.g. `:command: subapp sub-command`); `:subcommands:` recursion applies relative to it. Block-level only.
- Termynal options, each available per block (`:option:`) and globally (`termynal_`-prefixed, e.g. `termynal_width`): `subcommands` (recursion depth: `0` root only, `N` levels, `-1` full tree), `width`, `scheme`, `dark_bg`, `buttons` (`macos`/`windows`), `prompt`, and `type_delay`/`line_delay`/`start_delay` animation timings. Invalid `scheme`/`buttons` values fall back to their defaults.
- `CLI (Termynal)` documentation page demonstrating the new mode.
- Documentation for serving termynal blocks under Zensical: register `termynal.css` / `termynal.js` via `extra_css` / `extra_javascript` (CDN one-liner or self-hosted), since Zensical does not run the `termynal` MkDocs plugin.

## [0.3.1] - 2026-05-27

### Fixed

- Native engine docs now show `click.Choice`, `Enum`, and type metvars in option names (e.g. `--mode [a|b|c]`), including Typer 0.26 `FuncParamType` wrappers ([#32](https://github.com/syn54x/mkdocs-typer2/pull/32), [#31](https://github.com/syn54x/mkdocs-typer2/issues/31)).
- Legacy pretty mode populates the Default column from Typer markdown suffixes (`[default: …]`, `[required]`) instead of leaving defaults in descriptions ([#33](https://github.com/syn54x/mkdocs-typer2/pull/33), [#30](https://github.com/syn54x/mkdocs-typer2/issues/30)).

### Added

- Sample CLI `export` command demonstrating Choice, Enum, type metvars, and custom metavar in generated docs.

## [0.3.0] - 2026-04-22

### Added

- Optional dependency extra `[zensical]` to install Zensical alongside this package.

### Changed

- **Breaking:** MkDocs is no longer a default dependency. Install `mkdocs-typer2[mkdocs]` (or add MkDocs separately) to use the `mkdocs-typer2` MkDocs plugin entry point.
- Declared **Python-Markdown** (`markdown` on PyPI) as a direct runtime dependency so the Typer directive works without MkDocs installed.
- `MkdocsTyper` is loaded lazily from `mkdocs_typer2` so `import mkdocs_typer2` succeeds when only the Markdown extension is needed.

### Removed

- Debug `print` from the Markdown block processor.

## [0.2.1] - 2026-04-02

### Changed
- Constrained the MkDocs dependency to `>=1.6.1,<2` (runtime and dev) so installs stay on the 1.x line until this plugin is validated against MkDocs 2.0.

## [0.2.0] - 2026-01-14

### Added
- Added `engine` option (global + block-level) to select legacy vs native rendering.
- Added Click-based native renderer with list/table output based on `pretty`.

### Changed
- Deprecated legacy markdown-parsing pretty implementation in favor of native engine.
- Increased test coverage to 99% with new engine and CLI subcommand tests.

## [0.1.8] - 2026-01-13

### Fixed
- Standardized subcommand headings in markdown output for consistency
- Changed headings from "Sub Commands" to "Subcommands" in generated documentation
- Adjusted hierarchy of nested subcommand headings for improved clarity and uniformity

## [0.1.7] - 2026-01-13

### Fixed
- Fixed issue where nested subcommands (sub-app commands added via `add_typer()`) were not being properly parsed and rendered in the generated CLI documentation when using `pretty=True`
- Nested subcommands are now correctly detected and rendered with proper hierarchy in the generated documentation

### Changed
- Refactored CLI code structure by moving CLI modules into a `cli/` package for better organization
- Updated entry points in `pyproject.toml` to reflect the new CLI module path
- Enhanced markdown parsing to support level 3 headings (`###`) for nested subcommands in addition to level 2 headings (`##`) for subcommands

## [0.1.6] - 2025-09-01

### Fixed
- Fixed issue where line breaks in help text weren't preserved when using `pretty` formatting option
- Line breaks in CLI help messages and docstrings are now properly rendered in the generated documentation

## [0.1.4] - 2025-03-15

### Added
- Added support for Python 3.13
- Added per-block configuration for `pretty` option in documentation directives
- Added justfile for common development tasks
- Added docs/cli-pretty.md example for pretty-formatted CLI documentation
- Added docs/changelog.md that includes the project's CHANGELOG

### Changed
- Enhanced documentation with more detailed usage instructions and examples
- Updated navigation structure in mkdocs.yaml
- Improved TyperProcessor to support overriding global `pretty` setting at the block level

## [0.1.3] - 2025-03-09

### Fixed
- Fixed issue where docstrings weren't displayed in the generated documentation when `pretty` option was enabled
- Command names are now wrapped in backticks (`) when using `pretty` option
- Show `help` and docstring(s) in generated docs when `pretty` is enabled

## [0.1.2] - 2025-03-05

### Added
- Added Pydantic as a dependency

### Changed
- Updated logo and branding colors
- Added new logo variants in SVG and PNG formats

## [0.1.1] - 2024-10-25

### Added
- Pretty output formatting option for CLI documentation
    - Support for table-based documentation layout
- Automatic command parsing and documentation generation
- Integration with Typer's built-in documentation system

### Changed
- Improved documentation rendering with markdown tables
- Enhanced support for command arguments and options display

### Fixed
- Proper handling of optional and required parameters
- Correct parsing of default values in CLI options

## [0.1.0] - 2024-10-24

### Added
- Initial release of mkdocs-typer2
- Basic MkDocs plugin functionality
- Support for Typer CLI documentation generation
- Integration with MkDocs Material theme
- GitHub Actions for testing and deployment
- Basic test coverage
