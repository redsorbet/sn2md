import base64
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

from tqdm import tqdm

logger = logging.getLogger(__name__)


DEFAULT_MD_TEMPLATE = """---
created: {{year_month_day}}
tags: supernote
---

{{markdown}}

# Images
{% for image in images %}
- ![{{ image.name }}]({{image.name}})
{%- endfor %}

{% if keywords %}
# Keywords
{% for keyword in keywords %}
- Page {{ keyword.page_number }}: {{ keyword.content }}
{%- endfor %}
{%- endif %}

{% if links %}
# Links
{% for link in links %}
- Page {{ link.page_number }}: {{ link.type }} {{ link.inout }} [[{{ link.name | replace('.note', '')}}]]
{%- endfor %}
{%- endif %}

{% if titles %}
# Titles
{% for title in titles %}
- Page {{ title.page_number }}: Level {{ title.level }} "{{ title.content }}"
{%- endfor %}
{%- endif %}
"""


def compute_and_check_source_hash(source_path: str, output_path: str) -> None:
    """ Compute and check the hash of the source file against the metadata.

    Raises a ValueError if the source file hasn't been modified.

    Side effect: creates a metadata file in the output directory.
    """
    with open(source_path, "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()

    # Check if the hash already exists in the metadata
    metadata_path = os.path.join(output_path, ".sn2md.metadata.yaml")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)
            if (
                "notebook_hash" in metadata
                and metadata["notebook_hash"] == source_hash
            ):
                raise ValueError("The notebook hasn't been modified.")

    # Store the notebook_hash in the metadata
    with open(metadata_path, "w") as f:
        yaml.dump({"notebook_hash": source_hash, "notebook": source_path}, f)


def import_supernote_file_core(
    image_extractor: ImageExtractor,
    filename: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    global DEFAULT_MD_TEMPLATE
    template = DEFAULT_MD_TEMPLATE

    if config["template"]:
        template = config["template"]

    jinja_template = Template(template)

    notebook_name = os.path.splitext(os.path.basename(filename))[0]
    image_output_path = os.path.join(output, notebook_name)
    os.makedirs(image_output_path, exist_ok=True)
    try:
        compute_and_check_source_hash(filename, image_output_path)
    except ValueError as e:
        if not force:
            raise e
        else:
            print(f"Reprocessing {filename}")

    # Get file creation time using os.path
    creation_time = datetime.fromtimestamp(os.path.getctime(filename))
    year_month_day = creation_time.strftime("%Y-%m-%d")
    # Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.

    notebook = image_extractor.get_notebook(filename)
    pngs = image_extractor.extract_images(filename, image_output_path)
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
                config.get("api_key", None),
                model if model else config.get("model", "gpt-4o-mini"),
                config["prompt"],
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
    jinja_markdown = jinja_template.render(
        year_month_day=year_month_day,
        markdown=markdown,
        images=images,
        links=[
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
        keywords=[
            {
                "page_number": keyword.get_page_number(),
                "content": keyword.get_content().decode("utf-8"),
            }
            for keyword in (notebook.keywords if notebook else [])
        ],
        titles=[
            {
                "page_number": title.get_page_number(),
                "content": image_to_text(
                    convert_binary_to_image(notebook, title),
                    config["api_key"],
                    config["model"],
                    config["title_prompt"],
                ),
                "level": title.metadata["TITLELEVEL"],
            }
            for title in (notebook.titles if notebook else [])
        ],
    )

    with open(os.path.join(image_output_path, f"{notebook_name}.md"), "w") as f:
        _ = f.write(jinja_markdown)

    print(os.path.join(image_output_path, f"{notebook_name}.md"))


def import_supernote_directory_core(
    directory: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    for root, _, files in os.walk(directory):
        file_list = tqdm(files, desc="Processing files", unit="file") if progress else files
        for file in file_list:
            filename = os.path.join(root, file)
            try:
                if file.lower().endswith(".note"):
                    import_supernote_file_core(NotebookExtractor(), filename, output, config, force, progress, model)
                if file.lower().endswith(".pdf"):
                    import_supernote_file_core(PDFExtractor(), filename, output, config, force, progress, model)
                if file.lower().endswith(".png"):
                    import_supernote_file_core(PNGExtractor(), filename, output, config, force, progress, model)
            except ValueError as e:
                logger.debug(f"Skipping {filename}: {e}")
