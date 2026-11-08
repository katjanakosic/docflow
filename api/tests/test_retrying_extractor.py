import json
from pathlib import Path

import pytest

from app.adapters.retrying_extractor import RetryingExtractor
from app.domain.models import ExtractedData
from app.domain.ports import ExtractionError

LABELS_PATH = Path(__file__).parents[2] / "evals" / "labels.json"
DATA = ExtractedData.model_validate(
    json.loads(LABELS_PATH.read_text(encoding="utf-8"))["00_de_purchase_order.pdf"]
)
PDF = b"%PDF-1.4 test"


class ScriptedExtractor:
    """Returns or raises the given outcomes in order, and counts its calls."""

    def __init__(self, *outcomes) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0

    def extract(self, pdf_bytes: bytes) -> ExtractedData:
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make(inner):
    waits = []
    return RetryingExtractor(inner, delays=(10, 40), sleep=waits.append), waits


def test_a_first_success_needs_no_retry():
    inner = ScriptedExtractor(DATA)
    extractor, waits = make(inner)
    assert extractor.extract(PDF) == DATA
    assert inner.calls == 1
    assert waits == []


def test_temporary_failures_are_retried_with_growing_waits():
    inner = ScriptedExtractor(
        ExtractionError("overloaded"), ExtractionError("timeout"), DATA
    )
    extractor, waits = make(inner)
    assert extractor.extract(PDF) == DATA
    assert inner.calls == 3
    assert waits == [10, 40]


def test_it_gives_up_after_the_last_attempt():
    inner = ScriptedExtractor(*[ExtractionError("down")] * 3)
    extractor, waits = make(inner)
    with pytest.raises(ExtractionError, match="Failed after 3 attempts"):
        extractor.extract(PDF)
    assert inner.calls == 3
    assert waits == [10, 40]


def test_other_errors_are_not_retried():
    inner = ScriptedExtractor(RuntimeError("bug in our code"))
    extractor, waits = make(inner)
    with pytest.raises(RuntimeError):
        extractor.extract(PDF)
    assert inner.calls == 1
    assert waits == []
