from supernotelib import Notebook
from abc import ABC, abstractmethod
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
    # The API KEY for the model selected.
    api_key: str | None


class ImageExtractor(ABC):
    @abstractmethod
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        pass

    @abstractmethod
    def get_notebook(self, filename: str) -> Notebook | None:
        pass


