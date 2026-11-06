import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.postgres_documents import PostgresDocumentRepository
from app.domain.models import Document, ExtractedData
from app.domain.ports import DocumentNotFoundError, DocumentRepository
from app.domain.state_machine import Action, Status

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://docflow:docflow@localhost:5432/docflow_test",
)
LABELS_PATH = Path(__file__).parents[2] / "evals" / "labels.json"


def postgres_repository() -> DocumentRepository:
    """A repository on the empty test database, or skip if it isn't reachable."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"connect_timeout": 1})
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM documents"))
    except SQLAlchemyError:
        pytest.skip("Test database is not reachable or not migrated")
    return PostgresDocumentRepository(engine)


@pytest.fixture(params=["memory", "postgres"])
def repository(request) -> DocumentRepository:
    if request.param == "memory":
        return InMemoryDocumentRepository()
    return postgres_repository()


def make_document(sha256: str = "abc123") -> Document:
    return Document(
        id=uuid4(),
        file_name="invoice.pdf",
        sha256=sha256,
        size_bytes=1024,
        storage_key=f"documents/{sha256}.pdf",
        uploaded_by="kati",
    )


def test_added_document_can_be_read_back(repository):
    document = make_document()
    repository.add(document)
    assert repository.get(document.id) == document


def test_getting_an_unknown_id_raises(repository):
    with pytest.raises(DocumentNotFoundError):
        repository.get(uuid4())


def test_changes_are_only_saved_by_update(repository):
    document = make_document()
    repository.add(document)

    loaded = repository.get(document.id)
    loaded.apply(Action.START_EXTRACTION)
    assert repository.get(document.id).status == Status.UPLOADED  # not saved yet

    repository.update(loaded)
    assert repository.get(document.id).status == Status.EXTRACTING


def test_updating_an_unknown_document_raises(repository):
    with pytest.raises(DocumentNotFoundError):
        repository.update(make_document())


def test_find_by_sha256_returns_all_matching_documents(repository):
    repository.add(make_document("same"))
    repository.add(make_document("same"))
    repository.add(make_document("other"))
    assert len(repository.find_by_sha256("same")) == 2


def test_extracted_data_survives_the_round_trip(repository):
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    document = make_document()
    document.extracted_data = ExtractedData.model_validate(
        labels["00_de_purchase_order.pdf"]
    )
    repository.add(document)

    assert repository.get(document.id).extracted_data == document.extracted_data
