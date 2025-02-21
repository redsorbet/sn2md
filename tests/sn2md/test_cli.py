import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sn2md.cli import cli, get_config, logger, setup_logging
from sn2md.types import DEFAULT_MD_TEMPLATE, TO_MARKDOWN_TEMPLATE, TO_TEXT_TEMPLATE


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING"])
def test_setup_logging_sets_debug_level(level):
    setup_logging(level)
    assert logger.level == getattr(logging, level)


def test_get_config():
    config = get_config("no-file")
    assert config.prompt == TO_MARKDOWN_TEMPLATE
    assert config.title_prompt == TO_TEXT_TEMPLATE
    assert config.template == DEFAULT_MD_TEMPLATE
    assert config.model == "gpt-4o-mini"


@pytest.mark.parametrize(
    "path, api_key",
    [
        (Path(__file__).parent / "fixtures/test_config.toml", "test_api_key"),
        (
            Path(__file__).parent / "fixtures/test_legacy_config.toml",
            "test_open_api_key",
        ),
    ],
)
def test_get_config_from_file(path, api_key):
    config = get_config(path)
    assert config.prompt == "custom-prompt"
    assert config.title_prompt == TO_TEXT_TEMPLATE
    assert config.template == "custom-template"
    assert config.model == "gemini-1.5-pro-latest"
    assert config.api_key == api_key


@pytest.mark.parametrize("extractor, output", [
  ("NotebookExtractor", "test.note"),
  ("PDFExtractor", "test.pdf"),
  ("PNGExtractor", "test.png"),
])
def test_import_supernote_file(extractor, output):
    cli_runner = CliRunner()
    with patch("sn2md.cli.import_supernote_file_core") as mock_import_file:
        result = cli_runner.invoke(cli, ["file", output])
        assert result.exit_code == 0
        mock_import_file.assert_called_once()
        assert mock_import_file.call_args[0][0].__class__.__name__ == extractor
        assert mock_import_file.call_args[0][1] == output


def test_import_supernote_file_unsupported():
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli, ["file", "test.txt"])
    assert result.exit_code == 1
    assert "Unsupported file format" in result.output


def test_import_supernote_file_error():
    cli_runner = CliRunner()
    with patch("sn2md.cli.import_supernote_file_core") as mock_import_file:
        mock_import_file.side_effect = ValueError("Test error")
        result = cli_runner.invoke(cli, ["file", "test.note"])
        assert result.exit_code == 1
        assert "Test error" in result.output
