"""Jobs that the RQ worker process runs."""

from uuid import UUID

from app.api.deps import get_documents, get_extractor, get_storage
from app.services.extraction import ExtractionService


def run_extraction(document_id: str) -> str:
    service = ExtractionService(get_storage(), get_documents(), get_extractor())
    document = service.extract_document(UUID(document_id))
    return document.status.value
