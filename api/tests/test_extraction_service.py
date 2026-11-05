from pathlib import Path

import pytest

from app.adapters.fake_extractor import FakeExtractor
from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_storage import InMemoryStorage
from app.domain.state_machine import InvalidTransitionError, Status
from app.services.extraction import ExtractionService
from app.services.upload import UploadService

EVALS_DIR = Path(__file__).parents[2] / "evals"
SAMPLE_PDF = (EVALS_DIR / "samples" / "00_de_purchase_order.pdf").read_bytes()
UNKNOWN_PDF = b"%PDF-1.4 not one of the samples"


def make_services():
    storage = InMemoryStorage()
    documents = InMemoryDocumentRepository()
    extractor = FakeExtractor(EVALS_DIR / "samples", EVALS_DIR / "labels.json")
    upload = UploadService(storage, documents)
    extraction = ExtractionService(storage, documents, extractor)
    return upload, extraction, documents


def test_a_successful_extraction_saves_the_data_and_waits_for_review():
    upload, extraction, documents = make_services()
    document_id = upload.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati").document.id

    document = extraction.extract_document(document_id)

    assert document.status == Status.NEEDS_REVIEW
    assert document.extracted_data.supplier_name == "Weber AG"
    assert (
        documents.get(document_id).status == Status.NEEDS_REVIEW
    )  # saved, not just returned


def test_a_failed_extraction_marks_the_document_and_keeps_the_error():
    upload, extraction, _ = make_services()
    document_id = upload.upload(
        "other.pdf", UNKNOWN_PDF, uploaded_by="kati"
    ).document.id

    document = extraction.extract_document(document_id)

    assert document.status == Status.EXTRACTION_FAILED
    assert document.extracted_data is None
    assert "Unknown document" in document.last_error


def test_a_document_cannot_be_extracted_twice():
    upload, extraction, _ = make_services()
    document_id = upload.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati").document.id
    extraction.extract_document(document_id)

    with pytest.raises(InvalidTransitionError):
        extraction.extract_document(document_id)
