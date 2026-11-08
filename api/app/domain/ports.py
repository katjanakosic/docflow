from typing import Protocol
from uuid import UUID

from app.domain.models import Document, ExtractedData


class ObjectNotFoundError(Exception):
    """Raised when no file is stored under the requested key."""

    def __init__(self, key: str) -> None:
        super().__init__(f"No object stored under key {key!r}")
        self.key = key


class Storage(Protocol):
    """Stores files, such as uploaded PDFs, under a key like 'documents/abc.pdf'."""

    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class ExtractionError(Exception):
    """Raised when a document cannot be turned into ExtractedData."""


class Extractor(Protocol):
    """Reads a PDF and returns the data found in it."""

    def extract(self, pdf_bytes: bytes) -> ExtractedData: ...


class DocumentNotFoundError(Exception):
    """Raised when no document record exists with the requested id."""

    def __init__(self, document_id: UUID) -> None:
        super().__init__(f"No document with id {document_id}")
        self.document_id = document_id


class DocumentRepository(Protocol):
    """Saves and loads document records."""

    def add(self, document: Document) -> None: ...

    def get(self, document_id: UUID) -> Document: ...

    def update(self, document: Document) -> None: ...

    def find_by_sha256(
        self, sha256: str
    ) -> list[
        Document
    ]: ...  # same file can exist several times, e.g. after a rejected upload is uploaded again

    def list_recent(self, limit: int) -> list[Document]: ...


class ExtractionQueue(Protocol):
    """Hands documents to a background worker for extraction."""

    def enqueue(self, document_id: UUID) -> None: ...
