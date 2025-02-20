import logging

from pathlib import Path
import pytest

from sn2md.cli import get_config, logger, setup_logging
from sn2md.types import DEFAULT_MD_TEMPLATE,TO_MARKDOWN_TEMPLATE, TO_TEXT_TEMPLATE


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
