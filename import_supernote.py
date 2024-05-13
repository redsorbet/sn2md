import os
import hashlib
import yaml

import click
import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay


def load_notebook(path):
    return sn.load_notebook(path)


def convert_all(converter, total, file_name, save_func, visibility_overlay):
    basename, extension = os.path.splitext(file_name)
    max_digits = len(str(total))
    files = []
    for i in range(total):
        # append page number between filename and extention
        numbered_filename = basename + "_" + str(i).zfill(max_digits) + extension
        img = converter.convert(i, visibility_overlay)
        files.append(save_func(img, numbered_filename))
    return files


def convert_to_png(notebook, path):
    # Compute the hash of the notebook
    notebook_hash = hashlib.sha256(notebook.encode()).hexdigest()

    # Check if the hash already exists in the metadata
    metadata_path = os.path.join(path, 'metadata.yaml')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
            if 'notebook_hash' in metadata and metadata['notebook_hash'] == notebook_hash:
                raise ValueError("The notebook hasn't been modified.")
    else:
        # Store the notebook_hash in the metadata
        with open(metadata_path, 'w') as f:
            yaml.dump({'notebook_hash': notebook_hash}, f)

    converter = ImageConverter(notebook)
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)

    def save(img, file_name):
        img.save(file_name, format="PNG")

    total = notebook.get_total_pages()
    return convert_all(converter, total, path, save, vo)


@click.command()
@click.argument("filename", type=click.Path(readable=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    help="Output directory for images.",
)
def import_supernote(filename, output):
    click.echo("Importing file %s" % filename)
    # TODO check the destination directory - does it already exist? If so quit.

    # Export images of the note file into a directory with the same basename as the file.
    notebook = load_notebook(filename)
    image_output_path = os.path.join(output, os.path.splitext(os.path.basename(filename))[0])
    os.makedirs(image_output_path, exist_ok=True)

    try:
        pages = convert_to_png(notebook, image_output_path + "/page.png")
        # TODO Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.
    except ValueError as e:
        click.echo("Notebook hasn't been modified.")

    # TODO if the path already exists, check to see if the sha of the note has changed.


if __name__ == "__main__":
    import_supernote()
