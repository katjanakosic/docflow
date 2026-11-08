"""A queue that only remembers what was queued."""

from uuid import UUID


class InMemoryQueue:
    def __init__(self) -> None:
        self.enqueued: list[UUID] = []

    def enqueue(self, document_id: UUID) -> None:
        self.enqueued.append(document_id)
