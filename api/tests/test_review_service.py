from uuid import uuid4

import pytest

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.domain.models import Document
from app.domain.ports import DocumentNotFoundError
from app.domain.state_machine import InvalidTransitionError, Status
from app.services.review import InvalidReviewError, ReviewService


def make(status: Status = Status.NEEDS_REVIEW):
    documents = InMemoryDocumentRepository()
    document = Document(
        id=uuid4(),
        file_name="order.pdf",
        sha256="abc",
        size_bytes=1024,
        storage_key="documents/abc.pdf",
        uploaded_by="kati",
        status=status,
    )
    documents.add(document)
    return ReviewService(documents), documents, document.id


def test_approving_records_who_and_when():
    service, documents, document_id = make()
    service.approve(document_id, reviewer="reviewer")

    saved = documents.get(document_id)
    assert saved.status == Status.APPROVED
    assert saved.reviewed_by == "reviewer"
    assert saved.reviewed_at is not None


def test_rejecting_records_the_reason():
    service, documents, document_id = make()
    service.reject(document_id, reviewer="reviewer", reason="Unreadable or incomplete")

    saved = documents.get(document_id)
    assert saved.status == Status.REJECTED
    assert saved.rejection_reason == "Unreadable or incomplete"


def test_rejecting_without_a_reason_changes_nothing():
    service, documents, document_id = make()
    with pytest.raises(InvalidReviewError):
        service.reject(document_id, reviewer="reviewer", reason="   ")
    assert documents.get(document_id).status == Status.NEEDS_REVIEW


def test_only_documents_in_review_can_be_approved():
    service, _, document_id = make(status=Status.UPLOADED)
    with pytest.raises(InvalidTransitionError):
        service.approve(document_id, reviewer="reviewer")


def test_approving_an_unknown_document_raises():
    service, _, _ = make()
    with pytest.raises(DocumentNotFoundError):
        service.approve(uuid4(), reviewer="reviewer")
