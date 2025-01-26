from pathlib import Path
from unittest.mock import patch

from PIL import Image

from sn2md.ai_utils import image_to_markdown, image_to_text, _image_to_bytes, convert_image
from llm import Attachment


@patch("sn2md.ai_utils.llm.get_model")
def test_convert_image(get_model_mock):
    get_model_mock("dummy_model").prompt(
        "text",
        attachments=["dummy_attachment"]
    ).text.return_value = "dummy_result"

    assert convert_image("text", "dummy_attachment", "dummy_key", "dummy_model") == "dummy_result"


@patch("sn2md.ai_utils.convert_image")
def test_image_to_markdown(convert_mock):
    convert_mock.return_value = "dummy_result"
    result = image_to_markdown("dummy_path", "dummy_context", "dummy_key", "dummy_model", "some prompt: {context}")
    image = Attachment(path="dummy_path")
    convert_mock.assert_called_once_with("some prompt: dummy_context", image, "dummy_key", "dummy_model")
    assert result == "dummy_result"


@patch("sn2md.ai_utils.convert_image")
def test_image_to_text(convert_mock):
    image_path = Path(__file__).parent / "fixtures/ponder.png"
    image = Image.open(image_path)
    result = image_to_text(image, "dummy_key", "dummy_model", "dummy_prompt")
    convert_mock.assert_called_once_with(
        "dummy_prompt",
        Attachment(content=_image_to_bytes(image)),
        "dummy_key",
        "dummy_model"
    )
    assert result == convert_mock.return_value
