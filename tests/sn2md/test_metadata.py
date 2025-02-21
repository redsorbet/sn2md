import os
import pytest
import yaml
from sn2md.metadata import check_metadata_file, write_metadata_file
from sn2md.types import ConversionMetadata


@pytest.fixture
def temp_files(tmp_path):
    # Create test files
    source_file = tmp_path / "source.txt"
    output_file = tmp_path / "output.md"
    metadata_dir = tmp_path
    
    # Write initial content
    source_file.write_text("original content")
    output_file.write_text("# Original markdown")
    
    return {
        "source_file": str(source_file),
        "output_file": str(output_file),
        "metadata_dir": str(metadata_dir)
    }


def test_write_metadata_file(temp_files):
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])
    
    metadata_path = os.path.join(os.path.dirname(temp_files["output_file"]), ".sn2md.metadata.yaml")
    assert os.path.exists(metadata_path)
    
    with open(metadata_path) as f:
        data = yaml.safe_load(f)
        assert data["input_file"] == temp_files["source_file"]
        assert data["output_file"] == temp_files["output_file"]
        assert "input_hash" in data
        assert "output_hash" in data


def test_check_metadata_file_modified_input(temp_files):
    # First write initial metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])
    
    # Modify source file
    with open(temp_files["source_file"], "w") as f:
        f.write("modified content")
    
    # Should return metadata since input changed
    metadata = check_metadata_file(temp_files["metadata_dir"])
    assert isinstance(metadata, ConversionMetadata)
    assert metadata.input_file == temp_files["source_file"]


def test_check_metadata_file_unmodified_input(temp_files):
    # Write metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])
    
    # Should raise error since input hasn't changed
    with pytest.raises(ValueError, match="has NOT changed"):
        check_metadata_file(temp_files["metadata_dir"])


def test_check_metadata_file_modified_output(temp_files):
    # Write initial metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])
    
    # Modify source and output
    with open(temp_files["source_file"], "w") as f:
        f.write("modified content")
    with open(temp_files["output_file"], "w") as f:
        f.write("# Modified markdown")
    
    # Should raise error since output was modified
    with pytest.raises(ValueError, match="HAS been changed"):
        check_metadata_file(temp_files["metadata_dir"])


def test_check_metadata_file_missing(temp_files):
    # No metadata file exists
    result = check_metadata_file(temp_files["metadata_dir"])
    assert result is None
