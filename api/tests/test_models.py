import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.models import ExtractedData

LABELS_PATH = Path(__file__).parents[2] / "evals" / "labels.json"


def test_every_sample_label_matches_the_schema():
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    assert len(labels) == 20
    for label in labels.values():
        ExtractedData.model_validate(label)  # raises if a label doesn't fit


def test_text_is_converted_to_exact_types():
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    data = ExtractedData.model_validate(labels["00_de_purchase_order.pdf"])
    assert str(data.total) == "2136.05"
    assert data.issue_date.isoformat() == "2026-02-27"


def test_document_without_line_items_is_rejected():
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    label = labels["00_de_purchase_order.pdf"] | {"line_items": []}
    with pytest.raises(ValidationError):
        ExtractedData.model_validate(label)
