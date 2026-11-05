"""Extract the data from an uploaded document."""

from uuid import UUID

from app.domain.models import Document
from app.domain.ports import DocumentRepository, ExtractionError, Extractor, Storage
from app.domain.state_machine import Action


class ExtractionService:
    def __init__(
        self, storage: Storage, documents: DocumentRepository, extractor: Extractor
    ) -> None:
        self._storage = storage
        self._documents = documents
        self._extractor = extractor

    def extract_document(self, document_id: UUID) -> Document:
        document = self._documents.get(document_id)
        document.apply(
            Action.START_EXTRACTION
        )  # raises unless the document is UPLOADED
        self._documents.update(document)  # others now see it's in progress

        pdf_bytes = self._storage.get(document.storage_key)
        try:
            document.extracted_data = self._extractor.extract(pdf_bytes)
        except ExtractionError as error:
            document.last_error = str(error)
            document.apply(Action.EXTRACTION_FAILED)
        else:
            document.last_error = None
            document.apply(Action.EXTRACTION_SUCCEEDED)

        self._documents.update(document)
        return document
