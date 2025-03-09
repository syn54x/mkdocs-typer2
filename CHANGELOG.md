# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
