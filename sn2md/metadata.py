import hashlib
import os
import yaml
from dataclasses import asdict
from .types import ConversionMetadata


def check_metadata_file(metadata_file: str) -> ConversionMetadata | None:
    """Check the hashes of the source file against the metadata.

    Raises a ValueError if the source file hasn't been modified.

    Returns the computed source and output hashes.
    """
    metadata_path = os.path.join(metadata_file, ".sn2md.metadata.yaml")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            data = yaml.safe_load(f)
            metadata = ConversionMetadata(**data)

            with open(metadata.output_file, "rb") as f:
                output_hash = hashlib.sha1(f.read()).hexdigest()

            with open(metadata.input_file, "rb") as f:
                source_hash = hashlib.sha1(f.read()).hexdigest()

            if metadata.input_hash == source_hash:
                raise ValueError(f"Input {metadata.input_file} has NOT changed!")

            if metadata.output_hash != output_hash:
                raise ValueError(f"Output {metadata.output_file} HAS been changed!")

            return metadata


def write_metadata_file(source_file: str, output_file: str) -> None:
    """Write the source hash and path to the metadata file."""
    output_path = os.path.dirname(output_file)
    with open(output_file, "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    with open(source_file, "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()

    metadata_path = os.path.join(output_path, ".sn2md.metadata.yaml")
    with open(metadata_path, "w") as f:
        yaml.dump(
            asdict(ConversionMetadata(
                input_file=source_file,
                input_hash=source_hash,
                output_file=output_file,
                output_hash=output_hash,
            )),
            f,
        )


