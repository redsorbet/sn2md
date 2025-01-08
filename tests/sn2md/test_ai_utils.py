from unittest.mock import patch

from sn2md.ai_utils import image_to_markdown
from llm import Attachment


@patch("sn2md.ai_utils.convert_image")
def test_image_to_markdown(convert_mock):
    convert_mock.return_value = "dummy_result"
    result = image_to_markdown("dummy_path", "dummy_context", "dummy_key", "dummy_model", "some prompt: {context}")
    image = Attachment(path="dummy_path")
    convert_mock.assert_called_once_with("some prompt: dummy_context", image, "dummy_key", "dummy_model")
    assert result == "dummy_result"
