"""Providers that FastAPI calls to create the dependencies endpoints need."""

from functools import lru_cache
from typing import Annotated

import anthropic
from fastapi import Depends
from sqlalchemy import Engine, create_engine

from app.adapters.llm_extractor import LLMExtractor
from app.adapters.postgres_documents import PostgresDocumentRepository
from app.adapters.retrying_extractor import RetryingExtractor
from app.adapters.rq_queue import RQExtractionQueue
from app.adapters.s3_storage import S3Storage
from app.config import get_settings
from app.domain.ports import DocumentRepository, ExtractionQueue, Extractor, Storage
from app.services.retry import RetryService
from app.services.review import ReviewService
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
    return RetryingExtractor(LLMExtractor(client, model=settings.llm_model))


@lru_cache
def get_queue() -> ExtractionQueue:
    return RQExtractionQueue.connect(get_settings().redis_url)


def get_upload_service(
    storage: Annotated[Storage, Depends(get_storage)],
    documents: Annotated[DocumentRepository, Depends(get_documents)],
    queue: Annotated[ExtractionQueue, Depends(get_queue)],
) -> UploadService:
    return UploadService(storage, documents, queue)


def get_review_service(
    documents: Annotated[DocumentRepository, Depends(get_documents)],
) -> ReviewService:
    return ReviewService(documents)


def get_retry_service(
    documents: Annotated[DocumentRepository, Depends(get_documents)],
    queue: Annotated[ExtractionQueue, Depends(get_queue)],
) -> RetryService:
    return RetryService(documents, queue)
