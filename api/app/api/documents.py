"""HTTP endpoints for documents."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.api.deps import get_documents, get_extraction_service, get_upload_service
from app.domain.models import Document, ExtractedData
from app.domain.ports import DocumentNotFoundError, DocumentRepository
from app.domain.state_machine import InvalidTransitionError, Status
from app.services.extraction import ExtractionService
from app.services.upload import InvalidUploadError, UploadService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

DEMO_USER = "demo-user"  # replaced by the logged-in user


class DocumentOut(BaseModel):
    """What the API shows about a document. Internal fields stay hidden."""

    id: UUID
    file_name: str
    status: Status
    size_bytes: int
    created_at: datetime
    extracted_data: ExtractedData | None
    last_error: str | None

    @classmethod
    def from_document(cls, document: Document) -> "DocumentOut":
        return cls(
            id=document.id,
            file_name=document.file_name,
            status=document.status,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            extracted_data=document.extracted_data,
            last_error=document.last_error,
        )


class UploadOut(BaseModel):
    document: DocumentOut
    duplicate: bool


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": UploadOut,
            "description": "Duplicate: the existing document is returned",
        },
        400: {"description": "The file is not an acceptable PDF"},
    },
)
async def upload_document(
    file: UploadFile,
    response: Response,
    service: Annotated[UploadService, Depends(get_upload_service)],
) -> UploadOut:
    data = await file.read()
    try:
        result = service.upload(
            file.filename or "upload.pdf", data, uploaded_by=DEMO_USER
        )
    except InvalidUploadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None

    if result.duplicate:
        response.status_code = status.HTTP_200_OK  # nothing new was created
    return UploadOut(
        document=DocumentOut.from_document(result.document), duplicate=result.duplicate
    )


@router.get("/{document_id}")
def get_document(
    document_id: UUID,
    documents: Annotated[DocumentRepository, Depends(get_documents)],
) -> DocumentOut:
    try:
        return DocumentOut.from_document(documents.get(document_id))
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None


@router.post(
    "/{document_id}/extract",
    responses={
        404: {"description": "Document not found"},
        409: {"description": "The document's status does not allow extraction"},
    },
)
def extract_document(
    document_id: UUID,
    service: Annotated[ExtractionService, Depends(get_extraction_service)],
) -> DocumentOut:
    try:
        return DocumentOut.from_document(service.extract_document(document_id))
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    except InvalidTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
