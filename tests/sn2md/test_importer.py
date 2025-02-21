import base64
import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from sn2md.importer import (
    import_supernote_directory_core,
    import_supernote_file_core,
)
from sn2md.importers.note import NotebookExtractor
from sn2md.types import Config

# Mock functions from other modules


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_import_supernote_file_core(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    with (
        patch("sn2md.importer.check_metadata_file") as mock_check_metadata,
        patch("sn2md.importer.image_to_markdown") as mock_image_to_md,
        patch("sn2md.importer.write_metadata_file") as mock_write_metadata,
        patch("builtins.open", mock_open()) as mock_file,
        patch("uuid.uuid4") as mock_uuid,
        patch("os.rename") as mock_rename,
        patch("os.rename") as mock_rename,
    ):
        mock_uuid.return_value.hex = "test-uuid"
        mock_extractor = Mock()
        mock_notebook = Mock()
        mock_keyword = Mock()
        mock_keyword.get_page_number.return_value = 0
        mock_keyword.get_content.return_value = b"some keyword"
        mock_notebook.keywords = [mock_keyword]
        mock_notebook.titles = []
        mock_notebook.links = []

        mock_image_to_md.side_effect = ["markdown1", "markdown2"]

        config = Config(
            output_path_template="{{file_basename}}",
            output_filename_template="{{file_basename}}.md",
            prompt="TO_MARKDOWN_TEMPLATE",
            title_prompt="TO_TEXT_TEMPLATE",
            template="{{markdown}}",
            model="mock-model",
            api_key="mock-key"
        )

        mock_extractor.get_notebook.return_value = mock_notebook
        mock_extractor.extract_images.return_value = ["page1.png", "page2.png"]

        import_supernote_file_core(
            mock_extractor, filename, output, config, force=True, progress=False
        )

        mock_check_metadata.assert_not_called()
        assert mock_image_to_md.call_count == 2
        mock_write_metadata.assert_called_once()
        assert mock_rename.call_count == 2
        assert mock_rename.call_count == 2
        assert mock_rename.call_count == 2


def test_import_supernote_file_core_non_notebook(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    with (
        patch("sn2md.importer.check_metadata_file") as mock_check_metadata,
        patch("sn2md.importer.image_to_markdown") as mock_image_to_md,
        patch("sn2md.importer.write_metadata_file") as mock_write_metadata,
        patch("builtins.open", mock_open()) as mock_file,
        patch("uuid.uuid4") as mock_uuid,
    ):
        mock_uuid.return_value.hex = "test-uuid"
        mock_extractor = Mock()
        mock_image_to_md.side_effect = ["markdown1", "markdown2"]

        config = Config(
            output_path_template="{{file_basename}}",
            output_filename_template="{{file_basename}}.md",
            prompt="TO_MARKDOWN_TEMPLATE",
            title_prompt="TO_TEXT_TEMPLATE",
            template="{{markdown}}",
            model="mock-model",
            api_key="mock-key"
        )

        mock_extractor.get_notebook.return_value = None
        mock_extractor.extract_images.return_value = ["page1.png", "page2.png"]

        import_supernote_file_core(
            mock_extractor, filename, output, config, force=True, progress=False
        )

        mock_check_metadata.assert_not_called()
        assert mock_image_to_md.call_count == 2
        mock_write_metadata.assert_called_once()


@pytest.mark.parametrize(
    "progress, force", [(True, True), (True, False), (False, True), (False, False)]
)
def test_import_supernote_directory_core(temp_dir, progress, force):
    directory = temp_dir
    output = temp_dir
    config = None

    note_file = os.path.join(directory, "test.note")
    with open(note_file, "w") as f:
        f.write("test content")

    with (
        patch("sn2md.importer.import_supernote_file_core") as mock_import_file,
        patch("sn2md.importer.tqdm") as mock_tqdm,
    ):
        import_supernote_directory_core(
            directory, output, config, force=force, progress=progress
        )
        assert mock_import_file.call_count == 1
        assert mock_import_file.call_args_list[0][0][1:] == (
            note_file,
            output,
            config,
            force,
            progress,
            None,
        )
        assert mock_tqdm.called == progress


@pytest.mark.parametrize("progress", [True, False])
def test_import_supernote_directory_core(temp_dir, progress):
    directory = temp_dir
    output = temp_dir
    config = None

    note_file = os.path.join(directory, "test.note")
    with open(note_file, "w") as f:
        f.write("test content")

    with (
        patch("sn2md.importer.import_supernote_file_core") as mock_import_file,
        patch("sn2md.importer.tqdm") as mock_tqdm,
    ):
        mock_tqdm.return_value = [note_file]
        import_supernote_directory_core(
            directory, output, config, force=True, progress=progress
        )
        assert mock_import_file.call_count == 1
        assert mock_import_file.call_args_list[0][0][1:] == (
            note_file,
            output,
            config,
            True,
            progress,
            None,
        )
        assert mock_tqdm.called == progress
