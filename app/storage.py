from __future__ import annotations

import asyncio
from typing import Optional

import boto3

import app.settings

s3_client = boto3.client(
    "s3",
    endpoint_url=app.settings.S3_ENDPOINT,
    aws_access_key_id=app.settings.S3_ACCESS_KEY,
    aws_secret_access_key=app.settings.S3_SECRET_KEY,
    region_name=app.settings.S3_REGION,
)

async def upload(bucket: str, key: str, data: bytes) -> None:
    await asyncio.to_thread(
        s3_client.put_object, Bucket=bucket, Key=key, Body=data
    )

async def download(bucket: str, key: str) -> Optional[bytes]:
    def _get() -> bytes:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    try:
        return await asyncio.to_thread(_get)
    except s3_client.exceptions.ClientError as exc:  # type: ignore[attr-defined]
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            return None
        raise

async def exists(bucket: str, key: str) -> bool:
    try:
        await asyncio.to_thread(
            s3_client.head_object, Bucket=bucket, Key=key
        )
        return True
    except s3_client.exceptions.ClientError as exc:  # type: ignore[attr-defined]
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise
