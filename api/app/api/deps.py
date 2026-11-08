"""Providers that FastAPI calls to create the dependencies endpoints need."""

from functools import lru_cache
from typing import Annotated

import anthropic
from fastapi import Depends
from sqlalchemy import Engine, create_engine

from app.adapters.llm_extractor import LLMExtractor
from app.adapters.postgres_documents import PostgresDocumentRepository
from app.adapters.s3_storage import S3Storage
from app.config import get_settings
from app.domain.ports import DocumentRepository, Extractor, Storage
from app.services.extraction import ExtractionService
from app.services.upload import UploadService


@lru_cache
def get_storage() -> Storage:
    settings = get_settings()
    return S3Storage.connect(
        settings.s3_endpoint_url,
        settings.s3_access_key,
        settings.s3_secret_key,
        settings.s3_bucket,
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_documents() -> DocumentRepository:
    return PostgresDocumentRepository(get_engine())


@lru_cache
def get_extractor() -> Extractor:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return LLMExtractor(client, model=settings.llm_model)


def get_upload_service(
    storage: Annotated[Storage, Depends(get_storage)],
    documents: Annotated[DocumentRepository, Depends(get_documents)],
) -> UploadService:
    return UploadService(storage, documents)


def get_extraction_service(
    storage: Annotated[Storage, Depends(get_storage)],
    documents: Annotated[DocumentRepository, Depends(get_documents)],
    extractor: Annotated[Extractor, Depends(get_extractor)],
) -> ExtractionService:
    return ExtractionService(storage, documents, extractor)
