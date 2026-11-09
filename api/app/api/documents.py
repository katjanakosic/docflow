"""HTTP endpoints for documents."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.deps import (
    get_documents,
    get_retry_service,
    get_review_service,
    get_storage,
    get_upload_service,
)
from app.domain.models import Document, ExtractedData
from app.domain.ports import DocumentNotFoundError, DocumentRepository, Storage
from app.domain.state_machine import InvalidTransitionError, Status
from app.services.retry import RetryService
from app.services.review import InvalidReviewError, ReviewService
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
    reviewed_by: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None

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
            reviewed_by=document.reviewed_by,
            reviewed_at=document.reviewed_at,
            rejection_reason=document.rejection_reason,
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


@router.get("")
def list_documents(
    documents: Annotated[DocumentRepository, Depends(get_documents)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[DocumentOut]:
    return [
        DocumentOut.from_document(document) for document in documents.list_recent(limit)
    ]


class RejectIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


@router.post(
    "/{document_id}/approve",
    responses={
        404: {"description": "Document not found"},
        409: {"description": "Not in review"},
    },
)
def approve_document(
    document_id: UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> DocumentOut:
    try:
        return DocumentOut.from_document(
            service.approve(document_id, reviewer=DEMO_USER)
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    except InvalidTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.post(
    "/{document_id}/reject",
    responses={
        404: {"description": "Document not found"},
        409: {"description": "Not in review"},
    },
)
def reject_document(
    document_id: UUID,
    body: RejectIn,
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> DocumentOut:
    try:
        rejected = service.reject(document_id, reviewer=DEMO_USER, reason=body.reason)
        return DocumentOut.from_document(rejected)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    except InvalidTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except InvalidReviewError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None


@router.post(
    "/{document_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Document not found"},
        409: {"description": "Not failed"},
    },
)
def retry_extraction(
    document_id: UUID,
    service: Annotated[RetryService, Depends(get_retry_service)],
) -> DocumentOut:
    try:
        return DocumentOut.from_document(service.retry_extraction(document_id))
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    except InvalidTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


FILE_LINK_SECONDS = 300


@router.get(
    "/{document_id}/file",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={404: {"description": "Document not found"}},
)
def get_document_file(
    document_id: UUID,
    documents: Annotated[DocumentRepository, Depends(get_documents)],
    storage: Annotated[Storage, Depends(get_storage)],
) -> RedirectResponse:
    try:
        document = documents.get(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    url = storage.presigned_url(document.storage_key, FILE_LINK_SECONDS)
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
