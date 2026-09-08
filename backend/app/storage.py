from __future__ import annotations
from pathlib import Path
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from .config import settings


class Storage:
    def __init__(self):
        settings.local_storage_path.mkdir(parents=True, exist_ok=True)

    def _client(self, public: bool = False):
        endpoint = settings.storage_public_endpoint if public else settings.storage_endpoint
        return boto3.client(
            "s3", endpoint_url=endpoint,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            region_name=settings.storage_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def ensure_ready(self) -> None:
        if settings.storage_mode != "s3":
            return
        client = self._client()
        try:
            client.head_bucket(Bucket=settings.storage_bucket)
        except ClientError as exc:
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if status != 404 and code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            client.create_bucket(Bucket=settings.storage_bucket)

    def upload_spec(self, key: str, mime_type: str) -> dict:
        if settings.storage_mode == "s3":
            url = self._client(public=True).generate_presigned_url(
                "put_object",
                Params={"Bucket": settings.storage_bucket, "Key": key, "ContentType": mime_type},
                ExpiresIn=900,
            )
            return {"mode": "presigned", "method": "PUT", "url": url, "headers": {"Content-Type": mime_type}}
        return {"mode": "direct", "method": "POST", "url": "/api/v1/documents/upload-local"}

    def put_local(self, key: str, data: bytes) -> None:
        path = settings.local_storage_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read(self, key: str) -> bytes:
        if settings.storage_mode == "s3":
            return self._client().get_object(Bucket=settings.storage_bucket, Key=key)["Body"].read()
        return (settings.local_storage_path / key).read_bytes()

    def delete(self, key: str) -> None:
        if settings.storage_mode == "s3":
            self._client().delete_object(Bucket=settings.storage_bucket, Key=key)
        else:
            (settings.local_storage_path / key).unlink(missing_ok=True)


storage = Storage()
