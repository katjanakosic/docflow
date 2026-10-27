from uuid import uuid4

import pytest

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.domain.models import Document
from app.domain.ports import DocumentNotFoundError, DocumentRepository
from app.domain.state_machine import Action, Status


def make_repository() -> DocumentRepository:
    return InMemoryDocumentRepository()


def make_document(sha256: str = "abc123") -> Document:
    return Document(
        id=uuid4(),
        file_name="invoice.pdf",
        sha256=sha256,
        size_bytes=1024,
        storage_key=f"documents/{sha256}.pdf",
        uploaded_by="kati",
    )


def test_added_document_can_be_read_back():
    repository = make_repository()
    document = make_document()
    repository.add(document)
    assert repository.get(document.id) == document


def test_getting_an_unknown_id_raises():
    with pytest.raises(DocumentNotFoundError):
        make_repository().get(uuid4())


def test_changes_are_only_saved_by_update():
    repository = make_repository()
    document = make_document()
    repository.add(document)

    loaded = repository.get(document.id)
    loaded.apply(Action.START_EXTRACTION)
    assert repository.get(document.id).status == Status.UPLOADED  # not saved yet

    repository.update(loaded)
    assert repository.get(document.id).status == Status.EXTRACTING


def test_updating_an_unknown_document_raises():
    with pytest.raises(DocumentNotFoundError):
        make_repository().update(make_document())


def test_find_by_sha256_returns_all_matching_documents():
    repository = make_repository()
    repository.add(make_document("same"))
    repository.add(make_document("same"))
    repository.add(make_document("other"))
    assert len(repository.find_by_sha256("same")) == 2
