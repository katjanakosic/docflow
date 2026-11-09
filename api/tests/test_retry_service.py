from uuid import uuid4

import pytest

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_queue import InMemoryQueue
from app.domain.models import Document
from app.domain.ports import DocumentNotFoundError
from app.domain.state_machine import InvalidTransitionError, Status
from app.services.retry import RetryService


def make(status: Status = Status.EXTRACTION_FAILED):
    documents = InMemoryDocumentRepository()
    queue = InMemoryQueue()
    document = Document(
        id=uuid4(),
        file_name="order.pdf",
        sha256="abc",
        size_bytes=1024,
        storage_key="documents/abc.pdf",
        uploaded_by="kati",
        status=status,
        last_error="The AI service could not be reached.",
    )
    documents.add(document)
    return RetryService(documents, queue), documents, queue, document.id


def test_a_failed_document_goes_back_into_the_queue():
    service, documents, queue, document_id = make()
    service.retry_extraction(document_id)

    saved = documents.get(document_id)
    assert saved.status == Status.UPLOADED
    assert saved.last_error is None
    assert queue.enqueued == [document_id]


def test_only_failed_documents_can_be_retried():
    service, documents, queue, document_id = make(status=Status.NEEDS_REVIEW)
    with pytest.raises(InvalidTransitionError):
        service.retry_extraction(document_id)
    assert queue.enqueued == []  # nothing queued
    assert documents.get(document_id).status == Status.NEEDS_REVIEW  # nothing changed


def test_retrying_an_unknown_document_raises():
    service, _, queue, _ = make()
    with pytest.raises(DocumentNotFoundError):
        service.retry_extraction(uuid4())
    assert queue.enqueued == []
