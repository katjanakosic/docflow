from pathlib import Path

import pytest

from app.adapters.fake_extractor import FakeExtractor
from app.domain.ports import ExtractionError, Extractor

EVALS_DIR = Path(__file__).parents[2] / "evals"


def make_extractor() -> Extractor:
    return FakeExtractor(EVALS_DIR / "samples", EVALS_DIR / "labels.json")


def test_known_sample_returns_its_label():
    pdf_bytes = (EVALS_DIR / "samples" / "00_de_purchase_order.pdf").read_bytes()
    data = make_extractor().extract(pdf_bytes)
    assert data.supplier_name == "Weber AG"
    assert str(data.total) == "2136.05"


def test_every_sample_is_recognised():
    extractor = make_extractor()
    for pdf_path in sorted((EVALS_DIR / "samples").glob("*.pdf")):
        data = extractor.extract(pdf_path.read_bytes())
        assert data.doc_type in pdf_path.name


def test_unknown_pdf_raises():
    with pytest.raises(ExtractionError):
        make_extractor().extract(b"%PDF-1.4 not one of the samples")
