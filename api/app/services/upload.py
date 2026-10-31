import hashlib
from dataclasses import dataclass
from uuid import uuid4

from app.domain.models import Document
from app.domain.ports import DocumentRepository, Storage
from app.domain.state_machine import Status

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB, from the spec
PDF_SIGNATURE = b"%PDF-"


class InvalidUploadError(Exception):
    """Raised when an uploaded file is not acceptable."""


@dataclass(frozen=True)
class UploadResult:
    document: Document
    duplicate: bool  # True if this exact file was already uploaded


class UploadService:
    def __init__(self, storage: Storage, documents: DocumentRepository) -> None:
        self._storage = storage
        self._documents = documents

    def upload(self, file_name: str, data: bytes, uploaded_by: str) -> UploadResult:
        if not data.startswith(PDF_SIGNATURE):
            raise InvalidUploadError("Only PDF files can be uploaded")
        if len(data) > MAX_UPLOAD_BYTES:
            raise InvalidUploadError("File is larger than 20 MB")

        sha256 = hashlib.sha256(data).hexdigest()
        # same file counts as a duplicate, unless the earlier upload was rejected
        existing = [
            d
            for d in self._documents.find_by_sha256(sha256)
            if d.status != Status.REJECTED
        ]
        if existing:
            return UploadResult(document=existing[0], duplicate=True)

        document_id = uuid4()
        storage_key = f"documents/{document_id}.pdf"
        self._storage.put(
            storage_key, data, "application/pdf"
        )  # file first, then record

        document = Document(
            id=document_id,
            file_name=file_name,
            sha256=sha256,
            size_bytes=len(data),
            storage_key=storage_key,
            uploaded_by=uploaded_by,
        )
        self._documents.add(document)
        return UploadResult(document=document, duplicate=False)
