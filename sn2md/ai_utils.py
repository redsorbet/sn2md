from PIL.Image import Image

import llm

TO_MARKDOWN_TEMPLATE = """###
Context (the last few lines of markdown from the previous page):
{context}
###
Convert the image to markdown:
- If there is a simple diagram that the mermaid syntax can achieve, create a mermaid codeblock of it.
- When it is unclear what an image is, don't output anything for it.
- Use $$, $ latex math blocks for math equations.
- Support Obsidian syntaxes and dataview "field:: value" syntax.
- Do not wrap text in codeblocks.
"""

TO_TEXT_TEMPLATE = """
Convert the following image to text.
- If the image does not appear to be text, output a brief description (no more than 4 words), prepended with "Image: "
"""


def convert_image(
    text: str, attachment: llm.Attachment, api_key: str, model: str
) -> str:
    # TODO handle no such model
    llm_model = llm.get_model(model)
    if api_key:
        llm_model.key = api_key
    response = llm_model.prompt(text, attachments=[attachment])
    return response.text()


def image_to_markdown(
    path: str, context: str, api_key: str, model: str, prompt: str
) -> str:
    return convert_image(
        prompt.format(context=context), llm.Attachment(path=path), api_key, model
    )


def image_to_text(image: Image, api_key: str, model: str) -> str:
    return convert_image(
        TO_TEXT_TEMPLATE, llm.Attachment(content=image), api_key, model
    )
