import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from app.adapters.llm_extractor import TOOL_NAME, LLMExtractor
from app.domain.models import ExtractedData
from app.domain.ports import ExtractionError

LABELS_PATH = Path(__file__).parents[2] / "evals" / "labels.json"
LABEL = json.loads(LABELS_PATH.read_text(encoding="utf-8"))["00_de_purchase_order.pdf"]
PDF = b"%PDF-1.4 test document"


def tool_call(arguments: dict) -> SimpleNamespace:
    """A pretend response block, shaped like the SDK's tool_use block."""
    return SimpleNamespace(type="tool_use", input=arguments)


def make_client(content: list) -> MagicMock:
    """A pretend Anthropic client whose messages.create returns the given content."""
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(content=content)
    return client


def test_a_valid_answer_becomes_extracted_data():
    client = make_client([tool_call(LABEL)])
    data = LLMExtractor(client).extract(PDF)
    assert data == ExtractedData.model_validate(LABEL)


def test_the_request_sends_the_pdf_and_forces_the_tool():
    client = make_client([tool_call(LABEL)])
    LLMExtractor(client).extract(PDF)

    request = client.messages.create.call_args.kwargs
    assert request["tool_choice"] == {"type": "tool", "name": TOOL_NAME}
    document = request["messages"][0]["content"][0]
    assert document["source"]["data"] == base64.standard_b64encode(PDF).decode("ascii")


def test_an_answer_without_a_tool_call_raises():
    client = make_client(
        [SimpleNamespace(type="text", text="Sorry, I cannot read this.")]
    )
    with pytest.raises(ExtractionError):
        LLMExtractor(client).extract(PDF)


def test_an_answer_that_breaks_the_schema_raises():
    client = make_client([tool_call({"doc_type": "receipt"})])
    with pytest.raises(ExtractionError):
        LLMExtractor(client).extract(PDF)


def test_an_api_failure_raises_extraction_error():
    client = MagicMock()
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    client.messages.create.side_effect = anthropic.APIConnectionError(request=request)
    with pytest.raises(ExtractionError):
        LLMExtractor(client).extract(PDF)
