# Changelog

## v2.0.0

### Added

- Support for [any plugin supported by the llm](https://llm.datasette.io/en/stable/plugins/directory.html#remote-apis)  library (gemini, ollama, etc)
- Adds `--model` option to set a specific model
- Adds `api_key` configuration option (replaces `openai_api_key`).

### Changed

- The `openai_api_key` configuration has been deprecated in favor of `api_key`

## v1.0.1

### Changed

- Updates supernotlib (adds support for Manta)
- Bugfix: ensure `prompt` in configuration file is used over the defaults.

## v1.0.0

### Added

- Adds support for a configuration file (thanks @atisharma)
- Adds support for keywords, titles, and links to output template
- Adds unit tests and CI to project.

### Changed

- The order of command line switches has changed (most options go before the file/directory command)

### Removed

- Removes langchain dependency.
- Removes `--template` option (use configuration file instead).

## v0.1.0

### Added

Initial release:
- Add support for supernotes .note format
- Supports conversion of images to markdown
- Can customize the template with --template option.

# About

https://keepachangelog.com/en/1.1.0/
