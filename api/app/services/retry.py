"""Use case: send a document whose extraction failed back to the queue (workflow W7)."""

from uuid import UUID

from app.domain.models import Document
from app.domain.ports import DocumentRepository, ExtractionQueue
from app.domain.state_machine import Action


class RetryService:
    def __init__(self, documents: DocumentRepository, queue: ExtractionQueue) -> None:
        self._documents = documents
        self._queue = queue

    def retry_extraction(self, document_id: UUID) -> Document:
        document = self._documents.get(document_id)
        document.apply(Action.RETRY)  # raises unless the extraction failed
        document.last_error = None
        self._documents.update(document)
        self._queue.enqueue(document.id)  # saved first, then queued
        return document
