import hashlib
from pathlib import Path

import pytest

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_storage import InMemoryStorage
from app.domain.state_machine import Action, Status
from app.services.upload import MAX_UPLOAD_BYTES, InvalidUploadError, UploadService

SAMPLE_PDF = (
    Path(__file__).parents[2] / "evals" / "samples" / "00_de_purchase_order.pdf"
).read_bytes()


def make_service():
    storage = InMemoryStorage()
    documents = InMemoryDocumentRepository()
    return UploadService(storage, documents), storage, documents


def test_upload_stores_the_file_and_creates_a_record():
    service, storage, documents = make_service()
    result = service.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati")

    assert result.duplicate is False
    assert result.document.status == Status.UPLOADED
    assert result.document.sha256 == hashlib.sha256(SAMPLE_PDF).hexdigest()
    assert storage.get(result.document.storage_key) == SAMPLE_PDF
    assert documents.get(result.document.id) == result.document


def test_uploading_the_same_file_twice_returns_the_existing_document():
    service, _, documents = make_service()
    first = service.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati")
    second = service.upload("copy.pdf", SAMPLE_PDF, uploaded_by="kati")

    assert second.duplicate is True
    assert second.document.id == first.document.id
    assert len(documents.find_by_sha256(first.document.sha256)) == 1


def test_a_rejected_file_can_be_uploaded_again():
    service, _, documents = make_service()
    first = service.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati")

    rejected = documents.get(first.document.id)
    for action in (Action.START_EXTRACTION, Action.EXTRACTION_SUCCEEDED, Action.REJECT):
        rejected.apply(action)
    documents.update(rejected)

    second = service.upload("order.pdf", SAMPLE_PDF, uploaded_by="kati")
    assert second.duplicate is False
    assert second.document.id != first.document.id


def test_a_file_that_is_not_a_pdf_is_refused():
    service, _, documents = make_service()
    with pytest.raises(InvalidUploadError):
        service.upload("notes.txt", b"just some text", uploaded_by="kati")
    assert documents.find_by_sha256(hashlib.sha256(b"just some text").hexdigest()) == []


def test_a_file_over_20_mb_is_refused():
    service, _, _ = make_service()
    too_large = b"%PDF-" + bytes(MAX_UPLOAD_BYTES)
    with pytest.raises(InvalidUploadError):
        service.upload("huge.pdf", too_large, uploaded_by="kati")
