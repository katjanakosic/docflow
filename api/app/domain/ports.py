from typing import Protocol

from app.domain.models import ExtractedData


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
