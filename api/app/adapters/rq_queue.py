"""Extraction jobs in a Redis queue, run by an RQ worker."""

from uuid import UUID

from redis import Redis
from rq import Queue

QUEUE_NAME = "extraction"
JOB_FUNCTION = "app.workers.extraction.run_extraction"


class RQExtractionQueue:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue

    @classmethod
    def connect(cls, redis_url: str) -> "RQExtractionQueue":
        return cls(Queue(QUEUE_NAME, connection=Redis.from_url(redis_url)))

    def enqueue(self, document_id: UUID) -> None:
        self._queue.enqueue(JOB_FUNCTION, str(document_id), job_timeout=120)
