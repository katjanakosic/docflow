"""Providers that FastAPI calls to create the dependencies endpoints need."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_storage import InMemoryStorage
from app.domain.ports import DocumentRepository, Storage
from app.services.upload import UploadService


@lru_cache
def get_storage() -> Storage:
    return InMemoryStorage()  # replaced by S3/MinIO storage later


@lru_cache
def get_documents() -> DocumentRepository:
    return InMemoryDocumentRepository()  # replaced by Postgres later


def get_upload_service(
    storage: Annotated[Storage, Depends(get_storage)],
    documents: Annotated[DocumentRepository, Depends(get_documents)],
) -> UploadService:
    return UploadService(storage, documents)
