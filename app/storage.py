from __future__ import annotations

import asyncio

import boto3

import app.settings

r2_client = boto3.client(
    "s3",
    endpoint_url=app.settings.R2_ENDPOINT,
    aws_access_key_id=app.settings.R2_ACCESS_KEY,
    aws_secret_access_key=app.settings.R2_SECRET_KEY,
    region_name=app.settings.R2_REGION,
)


async def upload(bucket: str, key: str, data: bytes) -> None:
    await asyncio.to_thread(r2_client.put_object, Bucket=bucket, Key=key, Body=data)


async def download(bucket: str, key: str) -> bytes | None:
    def _get() -> bytes:
        resp = r2_client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    try:
        return await asyncio.to_thread(_get)
    except r2_client.exceptions.ClientError as exc:  # type: ignore[attr-defined]
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            return None
        raise


async def exists(bucket: str, key: str) -> bool:
    try:
        await asyncio.to_thread(r2_client.head_object, Bucket=bucket, Key=key)
        return True
    except r2_client.exceptions.ClientError as exc:  # type: ignore[attr-defined]
        if exc.response.get("Error", {}).get("Code") in {
            "404",
            "NoSuchKey",
            "NotFound",
        }:
            return False
        raise


async def ensure_folders() -> None:
    for folder in (
        app.settings.R2_REPLAY_FOLDER,
        app.settings.R2_OSU_FOLDER,
    ):
        await asyncio.to_thread(
            r2_client.put_object,
            Bucket=app.settings.R2_BUCKET,
            Key=f"{folder}/",
            Body=b"",
        )
