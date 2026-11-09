"""Storage in an S3-compatible service: MinIO locally, Amazon S3 in the cloud."""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.domain.ports import ObjectNotFoundError

MISSING_CODES = {"404", "NoSuchKey", "NotFound"}


class S3Storage:
    def __init__(self, client, bucket: str, presign_client=None) -> None:
        self._client = client
        self._bucket = bucket
        # Signs links for the address browsers use, which can differ from ours (Docker).
        self._presign_client = presign_client or client

    @classmethod
    def connect(
        cls,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_endpoint_url: str | None = None,
    ) -> "S3Storage":
        """endpoint_url=None means real AWS. public_endpoint_url defaults to endpoint_url."""

        def make_client(url: str | None):
            return boto3.client(
                "s3",
                endpoint_url=url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="us-east-1",
                config=Config(
                    signature_version="s3v4", s3={"addressing_style": "path"}
                ),
            )

        client = make_client(endpoint_url)
        presign_client = (
            make_client(public_endpoint_url) if public_endpoint_url else client
        )
        return cls(client, bucket, presign_client)

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

    def presigned_url(self, key: str, expires_in_seconds: int) -> str:
        return self._presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ResponseContentType": "application/pdf",
                "ResponseContentDisposition": "inline",
            },
            ExpiresIn=expires_in_seconds,
        )
