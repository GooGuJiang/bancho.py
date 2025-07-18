"""自定义谱面的数据库操作"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from typing import cast

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

import app.state.services
from app.models.custom_beatmaps import CustomMap
from app.models.custom_beatmaps import CustomMapFile
from app.models.custom_beatmaps import CustomMapFilesTable
from app.models.custom_beatmaps import CustomMapsTable

# 查询参数
READ_PARAMS = (
    CustomMapsTable.id,
    CustomMapsTable.mapset_id,
    CustomMapsTable.md5,
    CustomMapsTable.difficulty_name,
    CustomMapsTable.filename,
    CustomMapsTable.mode,
    CustomMapsTable.status,
    CustomMapsTable.audio_filename,
    CustomMapsTable.audio_lead_in,
    CustomMapsTable.preview_time,
    CustomMapsTable.countdown,
    CustomMapsTable.sample_set,
    CustomMapsTable.stack_leniency,
    CustomMapsTable.letterbox_in_breaks,
    CustomMapsTable.story_fire_in_front,
    CustomMapsTable.use_skin_sprites,
    CustomMapsTable.always_show_playfield,
    CustomMapsTable.overlay_position,
    CustomMapsTable.skin_preference,
    CustomMapsTable.epilepsy_warning,
    CustomMapsTable.countdown_offset,
    CustomMapsTable.special_style,
    CustomMapsTable.widescreen_storyboard,
    CustomMapsTable.samples_match_playback_rate,
    CustomMapsTable.distance_spacing,
    CustomMapsTable.beat_divisor,
    CustomMapsTable.grid_size,
    CustomMapsTable.timeline_zoom,
    CustomMapsTable.title_unicode,
    CustomMapsTable.artist_unicode,
    CustomMapsTable.creator,
    CustomMapsTable.version,
    CustomMapsTable.source,
    CustomMapsTable.tags,
    CustomMapsTable.beatmap_id,
    CustomMapsTable.beatmapset_id,
    CustomMapsTable.hp_drain_rate,
    CustomMapsTable.circle_size,
    CustomMapsTable.overall_difficulty,
    CustomMapsTable.approach_rate,
    CustomMapsTable.slider_multiplier,
    CustomMapsTable.slider_tick_rate,
    CustomMapsTable.total_length,
    CustomMapsTable.hit_length,
    CustomMapsTable.max_combo,
    CustomMapsTable.bpm,
    CustomMapsTable.star_rating,
    CustomMapsTable.aim_difficulty,
    CustomMapsTable.speed_difficulty,
    CustomMapsTable.plays,
    CustomMapsTable.passes,
    CustomMapsTable.created_at,
    CustomMapsTable.updated_at,
)


async def create(
    mapset_id: int,
    md5: str,
    difficulty_name: str,
    filename: str,
    mode: int,
    creator: str,
    version: str,
    **kwargs,
) -> CustomMap:
    """创建新的自定义谱面难度"""
    insert_data = {
        "mapset_id": mapset_id,
        "md5": md5,
        "difficulty_name": difficulty_name,
        "filename": filename,
        "mode": mode,
        "creator": creator,
        "version": version,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        **kwargs,
    }

    insert_stmt = insert(CustomMapsTable).values(**insert_data)
    rec_id = await app.state.services.database.execute(insert_stmt)

    select_stmt = select(*READ_PARAMS).where(CustomMapsTable.id == rec_id)
    beatmap = await app.state.services.database.fetch_one(select_stmt)
    assert beatmap is not None
    return cast(CustomMap, beatmap)


async def fetch_one(
    id: int | None = None,
    md5: str | None = None,
    mapset_id: int | None = None,
    filename: str | None = None,
) -> CustomMap | None:
    """获取单个自定义谱面"""
    select_stmt = select(*READ_PARAMS)

    if id is not None:
        select_stmt = select_stmt.where(CustomMapsTable.id == id)
    if md5 is not None:
        select_stmt = select_stmt.where(CustomMapsTable.md5 == md5)
    if mapset_id is not None:
        select_stmt = select_stmt.where(CustomMapsTable.mapset_id == mapset_id)
    if filename is not None:
        select_stmt = select_stmt.where(CustomMapsTable.filename == filename)

    beatmap = await app.state.services.database.fetch_one(select_stmt)
    return cast(CustomMap, beatmap) if beatmap else None


async def fetch_many(
    mapset_id: int | None = None,
    mode: int | None = None,
    status: str | None = None,
    creator: str | None = None,
    star_rating_min: float | None = None,
    star_rating_max: float | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[CustomMap]:
    """获取多个自定义谱面"""
    select_stmt = select(*READ_PARAMS)

    if mapset_id is not None:
        select_stmt = select_stmt.where(CustomMapsTable.mapset_id == mapset_id)
    if mode is not None:
        select_stmt = select_stmt.where(CustomMapsTable.mode == mode)
    if status is not None:
        select_stmt = select_stmt.where(CustomMapsTable.status == status)
    if creator is not None:
        select_stmt = select_stmt.where(CustomMapsTable.creator.like(f"%{creator}%"))
    if star_rating_min is not None:
        select_stmt = select_stmt.where(CustomMapsTable.star_rating >= star_rating_min)
    if star_rating_max is not None:
        select_stmt = select_stmt.where(CustomMapsTable.star_rating <= star_rating_max)

    # 分页
    offset = (page - 1) * page_size
    select_stmt = select_stmt.order_by(CustomMapsTable.star_rating.asc())
    select_stmt = select_stmt.offset(offset).limit(page_size)

    beatmaps = await app.state.services.database.fetch_all(select_stmt)
    return [cast(CustomMap, beatmap) for beatmap in beatmaps]


async def update_statistics(
    map_id: int,
    star_rating: float | None = None,
    max_combo: int | None = None,
    total_length: int | None = None,
    hit_length: int | None = None,
    bpm: float | None = None,
    aim_difficulty: float | None = None,
    speed_difficulty: float | None = None,
) -> None:
    """更新谱面统计信息"""
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}

    if star_rating is not None:
        update_data["star_rating"] = star_rating
    if max_combo is not None:
        update_data["max_combo"] = max_combo
    if total_length is not None:
        update_data["total_length"] = total_length
    if hit_length is not None:
        update_data["hit_length"] = hit_length
    if bpm is not None:
        update_data["bpm"] = bpm
    if aim_difficulty is not None:
        update_data["aim_difficulty"] = aim_difficulty
    if speed_difficulty is not None:
        update_data["speed_difficulty"] = speed_difficulty

    update_stmt = (
        update(CustomMapsTable)
        .where(CustomMapsTable.id == map_id)
        .values(**update_data)
    )
    await app.state.services.database.execute(update_stmt)


async def increment_plays(map_id: int) -> None:
    """增加游玩次数"""
    update_stmt = (
        update(CustomMapsTable)
        .where(CustomMapsTable.id == map_id)
        .values(plays=CustomMapsTable.plays + 1)
    )
    await app.state.services.database.execute(update_stmt)


async def increment_passes(map_id: int) -> None:
    """增加通过次数"""
    update_stmt = (
        update(CustomMapsTable)
        .where(CustomMapsTable.id == map_id)
        .values(passes=CustomMapsTable.passes + 1)
    )
    await app.state.services.database.execute(update_stmt)


async def update_status(map_id: int, status: str) -> None:
    """更新谱面状态"""
    update_stmt = (
        update(CustomMapsTable)
        .where(CustomMapsTable.id == map_id)
        .values(status=status, updated_at=datetime.now(timezone.utc))
    )
    await app.state.services.database.execute(update_stmt)


async def delete_map(map_id: int) -> None:
    """删除谱面（级联删除相关数据）"""
    delete_stmt = delete(CustomMapsTable).where(CustomMapsTable.id == map_id)
    await app.state.services.database.execute(delete_stmt)


# 谱面文件相关操作
FILE_READ_PARAMS = (
    CustomMapFilesTable.id,
    CustomMapFilesTable.map_id,
    CustomMapFilesTable.file_type,
    CustomMapFilesTable.filename,
    CustomMapFilesTable.file_hash,
    CustomMapFilesTable.file_size,
    CustomMapFilesTable.mime_type,
    CustomMapFilesTable.storage_path,
    CustomMapFilesTable.created_at,
)


async def create_map_file(
    map_id: int,
    file_type: str,
    filename: str,
    file_hash: str,
    file_size: int,
    storage_path: str,
    mime_type: str = "",
) -> CustomMapFile:
    """创建谱面文件记录"""
    insert_stmt = insert(CustomMapFilesTable).values(
        map_id=map_id,
        file_type=file_type,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        mime_type=mime_type,
        storage_path=storage_path,
        created_at=datetime.now(timezone.utc),
    )
    rec_id = await app.state.services.database.execute(insert_stmt)

    select_stmt = select(*FILE_READ_PARAMS).where(CustomMapFilesTable.id == rec_id)
    file_record = await app.state.services.database.fetch_one(select_stmt)
    assert file_record is not None
    return cast(CustomMapFile, file_record)


async def fetch_map_files(
    map_id: int,
    file_type: str | None = None,
) -> list[CustomMapFile]:
    """获取谱面的文件列表"""
    select_stmt = select(*FILE_READ_PARAMS).where(CustomMapFilesTable.map_id == map_id)

    if file_type is not None:
        select_stmt = select_stmt.where(CustomMapFilesTable.file_type == file_type)

    select_stmt = select_stmt.order_by(CustomMapFilesTable.created_at.asc())

    files = await app.state.services.database.fetch_all(select_stmt)
    return [cast(CustomMapFile, file) for file in files]


async def fetch_map_file_by_hash(file_hash: str) -> CustomMapFile | None:
    """根据文件哈希获取文件记录"""
    select_stmt = select(*FILE_READ_PARAMS).where(
        CustomMapFilesTable.file_hash == file_hash,
    )

    file_record = await app.state.services.database.fetch_one(select_stmt)
    return cast(CustomMapFile, file_record) if file_record else None


async def delete_map_files(map_id: int) -> None:
    """删除谱面的所有文件记录"""
    delete_stmt = delete(CustomMapFilesTable).where(
        CustomMapFilesTable.map_id == map_id,
    )
    await app.state.services.database.execute(delete_stmt)
