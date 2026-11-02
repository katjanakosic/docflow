"""Storage in an S3-compatible service: MinIO locally, Amazon S3 in the cloud."""

import boto3
from botocore.exceptions import ClientError

from app.domain.ports import ObjectNotFoundError

MISSING_CODES = {"404", "NoSuchKey", "NotFound"}


class S3Storage:
    def __init__(self, client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    @classmethod
    def connect(
        cls, endpoint_url: str | None, access_key: str, secret_key: str, bucket: str
    ) -> "S3Storage":
        """Create a storage with its own boto3 client. endpoint_url=None means AWS."""
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
        return cls(client, bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
        )

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response["Error"]["Code"] in MISSING_CODES:
                raise ObjectNotFoundError(key) from None
            raise
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response["Error"]["Code"] in MISSING_CODES:
                return False
            raise
        return True
