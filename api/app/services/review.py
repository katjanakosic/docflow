"""Use case: a reviewer approves or rejects an extracted document (workflows W4 and W5)."""

from datetime import UTC, datetime
from uuid import UUID

from app.domain.models import Document
from app.domain.ports import DocumentRepository
from app.domain.state_machine import Action


class InvalidReviewError(Exception):
    """Raised when a review decision is incomplete, such as a rejection without a reason."""


class ReviewService:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def approve(self, document_id: UUID, reviewer: str) -> Document:
        document = self._documents.get(document_id)
        document.apply(Action.APPROVE)  # raises unless the document needs review
        document.reviewed_by = reviewer
        document.reviewed_at = datetime.now(UTC)
        self._documents.update(document)
        return document

    def reject(self, document_id: UUID, reviewer: str, reason: str) -> Document:
        reason = reason.strip()
        if not reason:
            raise InvalidReviewError("A reason is required to reject a document")
        document = self._documents.get(document_id)
        document.apply(Action.REJECT)
        document.reviewed_by = reviewer
        document.reviewed_at = datetime.now(UTC)
        document.rejection_reason = reason
        self._documents.update(document)
        return document
