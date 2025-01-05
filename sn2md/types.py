from typing import TypedDict


class Config(TypedDict):
    # The prompt used to convert an image to markdown.
    prompt: str
    # The prompt used to convert some image to plain text (used for header highlights (H1, H2, etc.))
    title_prompt: str
    # The jinja template used to output markdown files.
    template: str
    # The LLM model to use for conversion (e.g. gpt-4o-mini). Can be any model installed in the environment (https://llm.datasette.io/en/stable/plugins/index.html)
    model: str
    # Deprecated: Use `api_key` instead of `openai_api_key`
    openai_api_key: str
    # The API KEY for the model selected.
    api_key: str
