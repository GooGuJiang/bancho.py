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


async def upload(
    bucket: str,
    key: str,
    data: bytes,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
) -> None:
    """上传文件到对象存储，带有适当的元数据以避免未命名对象问题"""
    upload_args = {
        "Bucket": bucket,
        "Key": key,
        "Body": data,
    }

    # 设置内容类型
    if content_type:
        upload_args["ContentType"] = content_type
    elif key.endswith(".osr"):
        upload_args["ContentType"] = "application/octet-stream"
    elif key.endswith(".osu"):
        upload_args["ContentType"] = "text/plain; charset=utf-8"
    else:
        upload_args["ContentType"] = "application/octet-stream"

    # 添加基本元数据
    base_metadata = {
        "uploaded-by": "bancho.py",
        "file-type": key.split(".")[-1] if "." in key else "unknown",
    }

    if metadata:
        base_metadata.update(metadata)

    upload_args["Metadata"] = base_metadata

    await asyncio.to_thread(r2_client.put_object, **upload_args)


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
    """确保对象存储中存在必要的文件夹结构"""
    for folder in (
        app.settings.R2_REPLAY_FOLDER,
        app.settings.R2_OSU_FOLDER,
    ):
        # 创建文件夹标记对象，添加适当的元数据以避免"未命名对象"问题
        await asyncio.to_thread(
            r2_client.put_object,
            Bucket=app.settings.R2_BUCKET,
            Key=f"{folder}/",
            Body=b"",
            ContentType="application/x-directory",
            Metadata={
                "purpose": "folder-marker",
                "folder-name": folder,
                "created-by": "bancho.py",
            },
        )


async def fix_unnamed_objects() -> None:
    """修复对象存储中的未命名对象问题"""
    try:
        # 列出存储桶中的所有对象
        response = await asyncio.to_thread(
            r2_client.list_objects_v2,
            Bucket=app.settings.R2_BUCKET,
        )

        if "Contents" not in response:
            return

        for obj in response["Contents"]:
            key = obj["Key"]

            # 检查是否是文件夹标记对象但缺少元数据
            if key.endswith("/"):
                try:
                    # 获取对象元数据
                    head_response = await asyncio.to_thread(
                        r2_client.head_object,
                        Bucket=app.settings.R2_BUCKET,
                        Key=key,
                    )

                    # 如果没有适当的元数据，重新创建
                    if "purpose" not in head_response.get("Metadata", {}):
                        folder_name = key.rstrip("/")
                        await asyncio.to_thread(
                            r2_client.put_object,
                            Bucket=app.settings.R2_BUCKET,
                            Key=key,
                            Body=b"",
                            ContentType="application/x-directory",
                            Metadata={
                                "purpose": "folder-marker",
                                "folder-name": folder_name,
                                "created-by": "bancho.py",
                                "fixed": "true",
                            },
                        )

                except Exception as e:
                    print(f"修复文件夹对象 {key} 时出错: {e}")

            # 检查文件对象是否缺少元数据
            elif not key.endswith("/"):
                try:
                    head_response = await asyncio.to_thread(
                        r2_client.head_object,
                        Bucket=app.settings.R2_BUCKET,
                        Key=key,
                    )

                    # 如果文件没有基本元数据，添加元数据
                    if "uploaded-by" not in head_response.get("Metadata", {}):
                        # 获取原始对象数据
                        get_response = await asyncio.to_thread(
                            r2_client.get_object,
                            Bucket=app.settings.R2_BUCKET,
                            Key=key,
                        )

                        data = get_response["Body"].read()

                        # 重新上传带有元数据的对象
                        upload_args = {
                            "Bucket": app.settings.R2_BUCKET,
                            "Key": key,
                            "Body": data,
                        }

                        # 设置适当的内容类型和元数据
                        if key.endswith(".osr"):
                            upload_args["ContentType"] = "application/octet-stream"
                        elif key.endswith(".osu"):
                            upload_args["ContentType"] = "text/plain; charset=utf-8"
                        else:
                            upload_args["ContentType"] = "application/octet-stream"

                        upload_args["Metadata"] = {
                            "uploaded-by": "bancho.py",
                            "file-type": (
                                key.split(".")[-1] if "." in key else "unknown"
                            ),
                            "fixed": "true",
                        }

                        await asyncio.to_thread(r2_client.put_object, **upload_args)

                except Exception as e:
                    print(f"修复文件对象 {key} 时出错: {e}")

    except Exception as e:
        print(f"修复未命名对象时出错: {e}")
