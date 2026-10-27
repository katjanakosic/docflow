from uuid import uuid4

import pytest

from app.domain.models import Document
from app.domain.state_machine import Action, InvalidTransitionError, Status


def make_document() -> Document:
    return Document(
        id=uuid4(),
        file_name="invoice.pdf",
        sha256="abc123",
        size_bytes=1024,
        storage_key="documents/abc123.pdf",
        uploaded_by="kati",
    )


def test_new_document_starts_as_uploaded():
    assert make_document().status == Status.UPLOADED


def test_apply_moves_the_status_through_the_state_machine():
    document = make_document()
    document.apply(Action.START_EXTRACTION)
    assert document.status == Status.EXTRACTING


def test_forbidden_action_raises_and_keeps_the_status():
    document = make_document()
    with pytest.raises(InvalidTransitionError):
        document.apply(Action.APPROVE)
    assert document.status == Status.UPLOADED
