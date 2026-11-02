import os
from uuid import uuid4

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.adapters.memory_storage import InMemoryStorage
from app.adapters.s3_storage import S3Storage
from app.domain.ports import ObjectNotFoundError, Storage


def minio_storage() -> Storage:
    """S3Storage against the local MinIO, or skip the test if MinIO isn't running."""
    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
        config=Config(connect_timeout=1, retries={"max_attempts": 0}),
    )
    bucket = os.environ.get("S3_BUCKET", "docflow-documents")
    try:
        client.head_bucket(Bucket=bucket)
    except (BotoCoreError, ClientError):
        pytest.skip("MinIO is not reachable")
    return S3Storage(client, bucket)


@pytest.fixture(params=["memory", "s3"])
def storage(request) -> Storage:
    if request.param == "memory":
        return InMemoryStorage()
    return minio_storage()


@pytest.fixture
def key() -> str:
    """A unique key per test, so tests never see each other's files."""
    return f"tests/{uuid4()}.pdf"


def test_stored_file_can_be_read_back(storage, key):
    storage.put(key, b"%PDF-1.4 hello", "application/pdf")
    assert storage.get(key) == b"%PDF-1.4 hello"


def test_exists_is_false_before_and_true_after_storing(storage, key):
    assert not storage.exists(key)
    storage.put(key, b"data", "application/pdf")
    assert storage.exists(key)


def test_reading_a_missing_file_raises(storage, key):
    with pytest.raises(ObjectNotFoundError):
        storage.get(key)


def test_storing_again_replaces_the_file(storage, key):
    storage.put(key, b"old", "application/pdf")
    storage.put(key, b"new", "application/pdf")
    assert storage.get(key) == b"new"
