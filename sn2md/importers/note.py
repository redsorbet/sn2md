import base64
import logging
import os
from typing import Callable
from unittest.mock import patch

import supernotelib as sn
from jinja2 import Template
from sn2md.ai_utils import image_to_markdown, image_to_text
from sn2md.importer import DEFAULT_MD_TEMPLATE, compute_and_check_notebook_hash
from sn2md.types import Config
from supernotelib.converter import ImageConverter, VisibilityOverlay

logger = logging.getLogger(__name__)


def load_notebook(path: str) -> sn.Notebook:
    return sn.load_notebook(path)


def convert_pages_to_pngs(
    converter: ImageConverter,
    total: int,
    path: str,
    save_func: Callable,
    visibility_overlay: dict[str, VisibilityOverlay],
) -> list[str]:
    file_name = path + "/" + os.path.basename(path) + ".png"
    basename, extension = os.path.splitext(file_name)
    max_digits = len(str(total))
    files = []
    for i in range(total):
        numbered_filename = basename + "_" + str(i).zfill(max_digits) + extension
        img = converter.convert(i, visibility_overlay)
        save_func(img, numbered_filename)
        files.append(numbered_filename)
    return files


def convert_notebook_to_pngs(notebook: sn.Notebook, path: str) -> list[str]:
    converter = ImageConverter(notebook)
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)

    def save(img, file_name):
        img.save(file_name, format="PNG")

    return convert_pages_to_pngs(converter, notebook.get_total_pages(), path, save, vo)


def convert_binary_to_image(notebook, title):
    page = notebook.get_page(title.get_page_number())
    binary = title.get_content()

    image_converter = sn.converter.ImageConverter(notebook)
    decoder = image_converter.find_decoder(page)
    titlerect = title.metadata["TITLERECT"].split(",")
    # TODO ideally decoder would support decoding these titles directly - make a PR on supernotelib!
    with (
        patch.object(notebook, "get_width") as width_mock,
        patch.object(notebook, "get_height") as height_mock,
    ):
        width_mock.return_value = int(titlerect[2])
        height_mock.return_value = int(titlerect[3])
        return image_converter._create_image_from_decoder(decoder, binary)


def import_supernote_file_core(
    filename: str,
    output: str,
    config: Config,
    force: bool = False,
    model: str | None = None,
) -> None:
    global DEFAULT_MD_TEMPLATE
    template = DEFAULT_MD_TEMPLATE

    if config["template"]:
        template = config["template"]

    jinja_template = Template(template)

    # Export images of the note file into a directory with the same basename as the file.
    notebook = load_notebook(filename)

    notebook_name = os.path.splitext(os.path.basename(filename))[0]
    image_output_path = os.path.join(output, notebook_name)
    os.makedirs(image_output_path, exist_ok=True)
    try:
        compute_and_check_notebook_hash(filename, image_output_path)
    except ValueError as e:
        if not force:
            raise e
        else:
            print(f"Reprocessing {filename}")

    # the notebook_name is YYYYMMDD_HHMMSS
    year_month_day = f"{notebook_name[:4]}-{notebook_name[4:6]}-{notebook_name[6:8]}"
    # Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.

    pngs = convert_notebook_to_pngs(notebook, image_output_path)
    markdown = ""
    for i, page in enumerate(pngs):
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
            "name": f"{notebook_name}_{i}.png",
            "rel_path": os.path.join(image_output_path, f"{notebook_name}_{i}.png"),
            "abs_path": os.path.abspath(
                os.path.join(image_output_path, f"{notebook_name}_{i}.png")
            ),
        }
        for i in range(len(pngs))
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
            for link in notebook.links
        ],
        keywords=[
            {
                "page_number": keyword.get_page_number(),
                "content": keyword.get_content().decode("utf-8"),
            }
            for keyword in notebook.keywords
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
            for title in notebook.titles
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
    model: str | None = None,
) -> None:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, config, force, model)
                except ValueError as e:
                    logger.debug(f"Skipping {filename}: {e}")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, config, force, model)
                except ValueError as e:
                    logger.debug(f"Skipping {filename}: {e}")
