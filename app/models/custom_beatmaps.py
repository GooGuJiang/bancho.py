"""自定义谱面相关的数据模型"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from sqlalchemy import DECIMAL
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects.mysql import FLOAT
from sqlalchemy.dialects.mysql import TINYINT

from app.repositories import Base


# 自定义谱面集表
class CustomMapsetsTable(Base):
    __tablename__ = "custom_mapsets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    source = Column(String(255), default="")
    tags = Column(Text, default="")
    description = Column(Text, default="")
    status = Column(Enum("pending", "approved", "rejected", "loved"), default="pending")
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    osz_filename = Column(String(255), nullable=False)
    osz_hash = Column(CHAR(32), nullable=False, unique=True)
    download_count = Column(Integer, default=0)
    favourite_count = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_custom_mapsets_creator", "creator_id"),
        Index("idx_custom_mapsets_status", "status"),
        Index("idx_custom_mapsets_upload_date", "upload_date"),
        Index("idx_custom_mapsets_osz_hash", "osz_hash", unique=True),
    )


# 自定义谱面难度表
class CustomMapsTable(Base):
    __tablename__ = "custom_maps"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mapset_id = Column(
        BigInteger,
        ForeignKey("custom_mapsets.id", ondelete="CASCADE"),
        nullable=False,
    )
    md5 = Column(CHAR(32), nullable=False, unique=True)
    difficulty_name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    mode = Column(TINYINT, default=0, nullable=False)
    status = Column(Enum("pending", "approved", "rejected", "loved"), default="pending")

    # osu!文件基本信息
    audio_filename = Column(String(255), default="")
    audio_lead_in = Column(Integer, default=0)
    preview_time = Column(Integer, default=-1)
    countdown = Column(TINYINT, default=1)
    sample_set = Column(String(16), default="Normal")
    stack_leniency = Column(DECIMAL(3, 2), default=0.70)
    letterbox_in_breaks = Column(Boolean, default=False)
    story_fire_in_front = Column(Boolean, default=True)
    use_skin_sprites = Column(Boolean, default=False)
    always_show_playfield = Column(Boolean, default=False)
    overlay_position = Column(String(16), default="NoChange")
    skin_preference = Column(String(255), default="")
    epilepsy_warning = Column(Boolean, default=False)
    countdown_offset = Column(Integer, default=0)
    special_style = Column(Boolean, default=False)
    widescreen_storyboard = Column(Boolean, default=False)
    samples_match_playback_rate = Column(Boolean, default=False)

    # 编辑器信息
    distance_spacing = Column(DECIMAL(6, 3), default=1.000)
    beat_divisor = Column(TINYINT, default=4)
    grid_size = Column(TINYINT, default=4)
    timeline_zoom = Column(DECIMAL(6, 3), default=1.000)

    # 谱面元数据
    title_unicode = Column(String(255), default="")
    artist_unicode = Column(String(255), default="")
    creator = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    source = Column(String(255), default="")
    tags = Column(Text, default="")
    beatmap_id = Column(BigInteger, default=0)
    beatmapset_id = Column(BigInteger, default=0)

    # 难度设定
    hp_drain_rate = Column(DECIMAL(3, 1), default=5.0)
    circle_size = Column(DECIMAL(3, 1), default=5.0)
    overall_difficulty = Column(DECIMAL(3, 1), default=5.0)
    approach_rate = Column(DECIMAL(3, 1), default=5.0)
    slider_multiplier = Column(DECIMAL(6, 3), default=1.400)
    slider_tick_rate = Column(DECIMAL(3, 1), default=1.0)

    # 计算得出的信息
    total_length = Column(Integer, default=0)
    hit_length = Column(Integer, default=0)
    max_combo = Column(Integer, default=0)
    bpm = Column(DECIMAL(8, 3), default=0.000)
    star_rating = Column(DECIMAL(6, 3), default=0.000)
    aim_difficulty = Column(DECIMAL(6, 3), default=0.000)
    speed_difficulty = Column(DECIMAL(6, 3), default=0.000)

    # 统计信息
    plays = Column(Integer, default=0)
    passes = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_custom_maps_md5", "md5", unique=True),
        Index("idx_custom_maps_mapset", "mapset_id"),
        Index("idx_custom_maps_mode", "mode"),
        Index("idx_custom_maps_status", "status"),
        Index("idx_custom_maps_creator", "creator"),
        Index("idx_custom_maps_star_rating", "star_rating"),
        Index("idx_custom_maps_plays", "plays"),
    )


# 自定义谱面书签表
class CustomMapBookmarksTable(Base):
    __tablename__ = "custom_map_bookmarks"

    user_id = Column(Integer, primary_key=True)
    mapset_id = Column(
        BigInteger,
        ForeignKey("custom_mapsets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)


# 自定义谱面评分表
class CustomMapRatingsTable(Base):
    __tablename__ = "custom_map_ratings"

    user_id = Column(Integer, primary_key=True)
    map_id = Column(
        BigInteger,
        ForeignKey("custom_maps.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rating = Column(TINYINT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 自定义谱面成绩表
class CustomScoresTable(Base):
    __tablename__ = "custom_scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    map_id = Column(
        BigInteger,
        ForeignKey("custom_maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    map_md5 = Column(CHAR(32), nullable=False)
    user_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    pp = Column(FLOAT(7, 3), nullable=False)
    acc = Column(FLOAT(6, 3), nullable=False)
    max_combo = Column(Integer, nullable=False)
    mods = Column(Integer, nullable=False)
    n300 = Column(Integer, nullable=False)
    n100 = Column(Integer, nullable=False)
    n50 = Column(Integer, nullable=False)
    nmiss = Column(Integer, nullable=False)
    ngeki = Column(Integer, nullable=False)
    nkatu = Column(Integer, nullable=False)
    grade = Column(String(2), default="N", nullable=False)
    status = Column(TINYINT, nullable=False)
    mode = Column(TINYINT, nullable=False)
    play_time = Column(DateTime, nullable=False)
    time_elapsed = Column(Integer, nullable=False)
    client_flags = Column(Integer, nullable=False)
    perfect = Column(Boolean, nullable=False)
    online_checksum = Column(CHAR(32), nullable=False)

    __table_args__ = (
        Index("idx_custom_scores_map_id", "map_id"),
        Index("idx_custom_scores_map_md5", "map_md5"),
        Index("idx_custom_scores_user_id", "user_id"),
        Index("idx_custom_scores_score", "score"),
        Index("idx_custom_scores_pp", "pp"),
        Index("idx_custom_scores_mods", "mods"),
        Index("idx_custom_scores_status", "status"),
        Index("idx_custom_scores_mode", "mode"),
        Index("idx_custom_scores_play_time", "play_time"),
        Index("idx_custom_scores_online_checksum", "online_checksum"),
        Index("idx_custom_scores_leaderboard", "map_md5", "status", "mode"),
    )


# 自定义谱面文件存储表
class CustomMapFilesTable(Base):
    __tablename__ = "custom_map_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    map_id = Column(
        BigInteger,
        ForeignKey("custom_maps.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_type = Column(
        Enum("osu", "audio", "image", "video", "storyboard"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    file_hash = Column(CHAR(32), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), default="")
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_custom_map_files_map_id", "map_id"),
        Index("idx_custom_map_files_type", "file_type"),
        Index("idx_custom_map_files_hash", "file_hash"),
    )


# TypedDict 类型定义
class CustomMapset(TypedDict):
    id: int
    creator_id: int
    title: str
    artist: str
    source: str
    tags: str
    description: str
    status: str
    upload_date: datetime
    last_update: datetime
    osz_filename: str
    osz_hash: str
    download_count: int
    favourite_count: int


class CustomMap(TypedDict):
    id: int
    mapset_id: int
    md5: str
    difficulty_name: str
    filename: str
    mode: int
    status: str

    # osu!文件基本信息
    audio_filename: str
    audio_lead_in: int
    preview_time: int
    countdown: int
    sample_set: str
    stack_leniency: float
    letterbox_in_breaks: bool
    story_fire_in_front: bool
    use_skin_sprites: bool
    always_show_playfield: bool
    overlay_position: str
    skin_preference: str
    epilepsy_warning: bool
    countdown_offset: int
    special_style: bool
    widescreen_storyboard: bool
    samples_match_playback_rate: bool

    # 编辑器信息
    distance_spacing: float
    beat_divisor: int
    grid_size: int
    timeline_zoom: float

    # 谱面元数据
    title_unicode: str
    artist_unicode: str
    creator: str
    version: str
    source: str
    tags: str
    beatmap_id: int
    beatmapset_id: int

    # 难度设定
    hp_drain_rate: float
    circle_size: float
    overall_difficulty: float
    approach_rate: float
    slider_multiplier: float
    slider_tick_rate: float

    # 计算得出的信息
    total_length: int
    hit_length: int
    max_combo: int
    bpm: float
    star_rating: float
    aim_difficulty: float
    speed_difficulty: float

    # 统计信息
    plays: int
    passes: int

    # 时间戳
    created_at: datetime
    updated_at: datetime


class CustomScore(TypedDict):
    id: int
    map_id: int
    map_md5: str
    user_id: int
    score: int
    pp: float
    acc: float
    max_combo: int
    mods: int
    n300: int
    n100: int
    n50: int
    nmiss: int
    ngeki: int
    nkatu: int
    grade: str
    status: int
    mode: int
    play_time: datetime
    time_elapsed: int
    client_flags: int
    perfect: bool
    online_checksum: str


class CustomMapFile(TypedDict):
    id: int
    map_id: int
    file_type: str
    filename: str
    file_hash: str
    file_size: int
    mime_type: str
    storage_path: str
    created_at: datetime
