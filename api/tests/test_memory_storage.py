import pytest

from app.adapters.memory_storage import InMemoryStorage
from app.domain.ports import ObjectNotFoundError, Storage


def make_storage() -> Storage:
    return InMemoryStorage()


def test_stored_file_can_be_read_back():
    storage = make_storage()
    storage.put("documents/a.pdf", b"%PDF-1.4 hello", "application/pdf")
    assert storage.get("documents/a.pdf") == b"%PDF-1.4 hello"


def test_exists_is_false_before_and_true_after_storing():
    storage = make_storage()
    assert not storage.exists("documents/a.pdf")
    storage.put("documents/a.pdf", b"data", "application/pdf")
    assert storage.exists("documents/a.pdf")


def test_reading_a_missing_file_raises():
    storage = make_storage()
    with pytest.raises(ObjectNotFoundError):
        storage.get("documents/missing.pdf")


def test_storing_again_replaces_the_file():
    storage = make_storage()
    storage.put("documents/a.pdf", b"old", "application/pdf")
    storage.put("documents/a.pdf", b"new", "application/pdf")
    assert storage.get("documents/a.pdf") == b"new"
