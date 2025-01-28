import hashlib
import logging
import os

import yaml

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


def compute_and_check_notebook_hash(notebook_path: str, output_path: str) -> None:
    # Compute the hash of the notebook file itself using SHA-1 (same as shasum)
    with open(notebook_path, "rb") as f:
        notebook_hash = hashlib.sha1(f.read()).hexdigest()

    # Check if the hash already exists in the metadata
    metadata_path = os.path.join(output_path, ".sn2md.metadata.yaml")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)
            if (
                "notebook_hash" in metadata
                and metadata["notebook_hash"] == notebook_hash
            ):
                raise ValueError("The notebook hasn't been modified.")

    # Store the notebook_hash in the metadata
    with open(metadata_path, "w") as f:
        yaml.dump({"notebook_hash": notebook_hash, "notebook": notebook_path}, f)
