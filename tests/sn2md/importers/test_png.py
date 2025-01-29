import os
import tempfile

import pytest

from sn2md.importers.png import PNGExtractor


@pytest.fixture
def png_file():
    # Create a temporary PNG file for testing
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(b'fake png content')
        return tmp.name


@pytest.fixture
def output_dir():
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


def test_extract_images(png_file, output_dir):
    # Arrange
    extractor = PNGExtractor()
    filename = png_file
    expected_output = os.path.join(output_dir, os.path.basename(filename))

    # Act
    result = extractor.extract_images(filename, output_dir)

    # Assert
    assert len(result) == 1
    assert result[0] == expected_output
    assert os.path.exists(expected_output)
    assert os.path.isfile(expected_output)

    # Cleanup
    os.unlink(png_file)


def test_get_notebook():
    extractor = PNGExtractor()
    assert extractor.get_notebook("any_file.png") is None
