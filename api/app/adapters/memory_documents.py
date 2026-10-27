"""Document records kept in memory. For tests only: everything is lost on exit."""

from dataclasses import replace
from uuid import UUID

from app.domain.models import Document
from app.domain.ports import DocumentNotFoundError


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self._documents: dict[UUID, Document] = {}

    def add(self, document: Document) -> None:
        self._documents[document.id] = replace(document)

    def get(self, document_id: UUID) -> Document:
        try:
            return replace(self._documents[document_id])
        except KeyError:
            raise DocumentNotFoundError(document_id) from None

    def update(self, document: Document) -> None:
        if document.id not in self._documents:
            raise DocumentNotFoundError(document.id)
        self._documents[document.id] = replace(document)

    def find_by_sha256(self, sha256: str) -> list[Document]:
        return [replace(d) for d in self._documents.values() if d.sha256 == sha256]
