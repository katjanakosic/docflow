from typing import Protocol


class ObjectNotFoundError(Exception):
    """Raised when no file is stored under the requested key."""

    def __init__(self, key: str) -> None:
        super().__init__(f"No object stored under key {key!r}")
        self.key = key


class Storage(Protocol):
    """Stores files, such as uploaded PDFs, under a key like 'documents/abc.pdf'."""

    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...
