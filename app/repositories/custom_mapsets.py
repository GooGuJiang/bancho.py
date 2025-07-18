"""自定义谱面集的数据库操作"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import cast

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import join
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import aliased

import app.state.services
from app.models.custom_beatmaps import CustomMapBookmarksTable
from app.models.custom_beatmaps import CustomMapset
from app.models.custom_beatmaps import CustomMapsetsTable

# 查询参数
READ_PARAMS = (
    CustomMapsetsTable.id,
    CustomMapsetsTable.creator_id,
    CustomMapsetsTable.title,
    CustomMapsetsTable.artist,
    CustomMapsetsTable.source,
    CustomMapsetsTable.tags,
    CustomMapsetsTable.description,
    CustomMapsetsTable.status,
    CustomMapsetsTable.upload_date,
    CustomMapsetsTable.last_update,
    CustomMapsetsTable.osz_filename,
    CustomMapsetsTable.osz_hash,
    CustomMapsetsTable.download_count,
    CustomMapsetsTable.favourite_count,
)


async def create(
    creator_id: int,
    title: str,
    artist: str,
    osz_filename: str,
    osz_hash: str,
    source: str = "",
    tags: str = "",
    description: str = "",
) -> CustomMapset:
    """创建新的自定义谱面集"""
    insert_stmt = insert(CustomMapsetsTable).values(
        creator_id=creator_id,
        title=title,
        artist=artist,
        source=source,
        tags=tags,
        description=description,
        osz_filename=osz_filename,
        osz_hash=osz_hash,
        upload_date=datetime.now(timezone.utc),
        last_update=datetime.now(timezone.utc),
    )
    rec_id = await app.state.services.database.execute(insert_stmt)

    select_stmt = select(*READ_PARAMS).where(CustomMapsetsTable.id == rec_id)
    mapset = await app.state.services.database.fetch_one(select_stmt)
    assert mapset is not None
    return cast(CustomMapset, mapset)


async def fetch_one(
    id: int | None = None,
    osz_hash: str | None = None,
    creator_id: int | None = None,
) -> CustomMapset | None:
    """获取单个自定义谱面集"""
    select_stmt = select(*READ_PARAMS)

    if id is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.id == id)
    if osz_hash is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.osz_hash == osz_hash)
    if creator_id is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.creator_id == creator_id)

    mapset = await app.state.services.database.fetch_one(select_stmt)
    return cast(CustomMapset, mapset) if mapset else None


async def fetch_many(
    creator_id: int | None = None,
    status: str | None = None,
    title: str | None = None,
    artist: str | None = None,
    tags: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[CustomMapset]:
    """获取多个自定义谱面集"""
    select_stmt = select(*READ_PARAMS)

    if creator_id is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.creator_id == creator_id)
    if status is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.status == status)
    if title is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.title.like(f"%{title}%"))
    if artist is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.artist.like(f"%{artist}%"))
    if tags is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.tags.like(f"%{tags}%"))

    # 分页
    offset = (page - 1) * page_size
    select_stmt = select_stmt.order_by(CustomMapsetsTable.upload_date.desc())
    select_stmt = select_stmt.offset(offset).limit(page_size)

    mapsets = await app.state.services.database.fetch_all(select_stmt)
    return [cast(CustomMapset, mapset) for mapset in mapsets]


async def update_status(mapset_id: int, status: str) -> None:
    """更新谱面集状态"""
    update_stmt = (
        update(CustomMapsetsTable)
        .where(CustomMapsetsTable.id == mapset_id)
        .values(status=status, last_update=datetime.now(timezone.utc))
    )
    await app.state.services.database.execute(update_stmt)


async def increment_download_count(mapset_id: int) -> None:
    """增加下载计数"""
    update_stmt = (
        update(CustomMapsetsTable)
        .where(CustomMapsetsTable.id == mapset_id)
        .values(download_count=CustomMapsetsTable.download_count + 1)
    )
    await app.state.services.database.execute(update_stmt)


async def update_favourite_count(mapset_id: int) -> None:
    """更新收藏计数"""
    # 统计收藏数
    count_stmt = (
        select(func.count())
        .select_from(CustomMapBookmarksTable)
        .where(CustomMapBookmarksTable.mapset_id == mapset_id)
    )
    count = await app.state.services.database.fetch_val(count_stmt)

    # 更新谱面集的收藏计数
    update_stmt = (
        update(CustomMapsetsTable)
        .where(CustomMapsetsTable.id == mapset_id)
        .values(favourite_count=count)
    )
    await app.state.services.database.execute(update_stmt)


async def delete_mapset(mapset_id: int) -> None:
    """删除谱面集（级联删除相关数据）"""
    delete_stmt = delete(CustomMapsetsTable).where(CustomMapsetsTable.id == mapset_id)
    await app.state.services.database.execute(delete_stmt)


async def search(
    query: str,
    mode: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[CustomMapset]:
    """搜索自定义谱面集"""
    from app.models.custom_beatmaps import CustomMapsTable

    # 关联查询，包含至少一个指定模式的谱面
    join_condition = CustomMapsetsTable.id == CustomMapsTable.mapset_id
    select_stmt = (
        select(*READ_PARAMS)
        .select_from(join(CustomMapsetsTable, CustomMapsTable, join_condition))
        .distinct()
    )

    # 文本搜索：标题、艺术家、创作者、标签
    if query:
        search_filter = (
            CustomMapsetsTable.title.like(f"%{query}%")
            | CustomMapsetsTable.artist.like(f"%{query}%")
            | CustomMapsetsTable.tags.like(f"%{query}%")
            | CustomMapsTable.creator.like(f"%{query}%")
        )
        select_stmt = select_stmt.where(search_filter)

    # 模式过滤
    if mode is not None:
        select_stmt = select_stmt.where(CustomMapsTable.mode == mode)

    # 状态过滤
    if status is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.status == status)

    # 分页和排序
    offset = (page - 1) * page_size
    select_stmt = select_stmt.order_by(CustomMapsetsTable.upload_date.desc())
    select_stmt = select_stmt.offset(offset).limit(page_size)

    mapsets = await app.state.services.database.fetch_all(select_stmt)
    return [cast(CustomMapset, mapset) for mapset in mapsets]


async def get_count(
    creator_id: int | None = None,
    status: str | None = None,
) -> int:
    """获取谱面集数量"""
    select_stmt = select(func.count()).select_from(CustomMapsetsTable)

    if creator_id is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.creator_id == creator_id)
    if status is not None:
        select_stmt = select_stmt.where(CustomMapsetsTable.status == status)

    count = await app.state.services.database.fetch_val(select_stmt)
    return cast(int, count)


async def get_popular(
    limit: int = 10,
    days: int = 30,
) -> list[CustomMapset]:
    """获取热门谱面集（基于下载量和收藏数）"""
    from datetime import timedelta

    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    select_stmt = (
        select(*READ_PARAMS)
        .where(CustomMapsetsTable.upload_date >= since_date)
        .order_by(
            (
                CustomMapsetsTable.download_count
                + CustomMapsetsTable.favourite_count * 3
            ).desc(),
        )
        .limit(limit)
    )

    mapsets = await app.state.services.database.fetch_all(select_stmt)
    return [cast(CustomMapset, mapset) for mapset in mapsets]
