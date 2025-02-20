import base64
import uuid
import hashlib
import logging
import os
from datetime import datetime

import yaml
from jinja2 import Template

from sn2md.ai_utils import image_to_markdown, image_to_text
from sn2md.importers.pdf import PDFExtractor
from sn2md.importers.png import PNGExtractor
from sn2md.types import Config, ImageExtractor
from sn2md.importers.note import NotebookExtractor, convert_binary_to_image
from .types import ConversionMetadata

from tqdm import tqdm

logger = logging.getLogger(__name__)


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
                raise ValueError(f"{metadata.input_file} hasn't changed!")

            if metadata.output_hash != output_hash:
                raise ValueError(f"{metadata.output_file} has been changed!")

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
            ConversionMetadata(
                input_file=source_file,
                input_hash=source_hash,
                output_file=output_file,
                output_hash=output_hash,
            ),
            f,
        )


def import_supernote_file_core(
    image_extractor: ImageExtractor,
    file_name: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    jinja_template = Template(config.template)

    file_basename = os.path.splitext(os.path.basename(file_name))[0]
    # use a random name for the output directory
    image_output_path = os.path.join(output, uuid.uuid4().hex)
    os.makedirs(image_output_path, exist_ok=True)

    logger.debug("Storing images in %s", image_output_path)
    try:
        check_metadata_file(file_name)
    except ValueError as e:
        if not force:
            raise e
        else:
            print(f"Reprocessing {file_name}")

    # Get file creation time using os.path
    creation_time = datetime.fromtimestamp(os.path.getctime(file_name))
    year_month_day = creation_time.strftime("%Y-%m-%d")
    # Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.

    notebook = image_extractor.get_notebook(file_name)
    pngs = image_extractor.extract_images(file_name, image_output_path)
    markdown = ""
    page_list = tqdm(pngs, desc="Processing pages", unit="page") if progress else pngs
    for i, page in enumerate(page_list):
        context = ""
        if i > 0 and len(markdown) > 0:
            # include the last 50 characters...for continuity of the transcription:
            context = markdown[-50:]
        markdown = (
            markdown
            + "\n"
            + image_to_markdown(
                page,
                context,
                config.api_key,
                model if model else config.model,
                config.prompt,
            )
        )

    images = [
        {
            "name": os.path.basename(png_path),
            "rel_path": png_path,
            "abs_path": os.path.abspath(png_path),
        }
        for png_path in pngs
    ]

    # Codes:
    # TODO add a pull request for this feature:
    # https://github.com/jya-dev/supernote-tool/blob/807d5fa4bf524fdb1f9c7f1c67ed66ea96a49db5/supernotelib/fileformat.py#L236
    def get_link_str(type_code: int) -> str:
        if type_code == 0:
            return "page"
        elif type_code == 1:
            return "file"
        elif type_code == 2:
            return "web"

        return "unknown"

    def get_inout_str(type_code: int) -> str:
        if type_code == 0:
            return "out"
        elif type_code == 1:
            return "in"

        return "unknown"

    # TODO add pages - for each page include keywords and titles
    context = {
        "file_basename": file_basename,
        "file_name": file_name,
        "year_month_day": year_month_day,
        "markdown": markdown,
        "images": images,
        "links": [
            {
                "page_number": link.get_page_number(),
                "type": get_link_str(link.get_type()),
                "name": os.path.basename(
                    base64.standard_b64decode(link.get_filepath())
                ).decode("utf-8"),
                "device_path": base64.standard_b64decode(link.get_filepath()),
                "inout": get_inout_str(link.get_inout()),
            }
            for link in (notebook.links if notebook else [])
        ],
        "keywords": [
            {
                "page_number": keyword.get_page_number(),
                "content": keyword.get_content().decode("utf-8"),
            }
            for keyword in (notebook.keywords if notebook else [])
        ],
        "titles": [
            {
                "page_number": title.get_page_number(),
                "content": image_to_text(
                    convert_binary_to_image(notebook, title),
                    config.api_key,
                    config.model,
                    config.title_prompt,
                ),
                "level": title.metadata["TITLELEVEL"],
            }
            for title in (notebook.titles if notebook else [])
        ],
    }

    jinja_markdown = jinja_template.render(context)

    output_filename_template = Template(config.output_filename_template)
    output_filename = output_filename_template.render(context)

    output_path_template = Template(config.output_path_template)
    output_path = output_path_template.render(context)
    output_path = os.path.join(output, output_path)
    os.makedirs(output_path, exist_ok=True)

    output_path_and_file = os.path.join(output_path, output_filename)
    with open(output_path_and_file, "w") as f:
        _ = f.write(jinja_markdown)
    logger.debug("Wrote output to %s", output_path_and_file)

    # copy everything from image_output_path to output_path:
    for png_path in pngs:
        png_name = os.path.basename(png_path)
        os.rename(png_path, os.path.join(output_path, png_name))

    write_metadata_file(file_name, output_path_and_file)
    # TODO create the cache file

    os.removedirs(image_output_path)
    logger.debug("Moved images to %s", output_path)

    print(os.path.join(output_path, f"{file_basename}.md"))


def import_supernote_directory_core(
    directory: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    for root, _, files in os.walk(directory):
        file_list = (
            tqdm(files, desc="Processing files", unit="file") if progress else files
        )
        for file in file_list:
            filename = os.path.join(root, file)
            try:
                if file.lower().endswith(".note"):
                    import_supernote_file_core(
                        NotebookExtractor(),
                        filename,
                        output,
                        config,
                        force,
                        progress,
                        model,
                    )
                if file.lower().endswith(".pdf"):
                    import_supernote_file_core(
                        PDFExtractor(), filename, output, config, force, progress, model
                    )
                if file.lower().endswith(".png"):
                    import_supernote_file_core(
                        PNGExtractor(), filename, output, config, force, progress, model
                    )
            except ValueError as e:
                logger.debug(f"Skipping {filename}: {e}")
