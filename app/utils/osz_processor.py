"""OSZ文件处理器
处理.osz文件的上传、解压、解析和存储
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from .osu_parser import OsuMapData
from .osu_parser import parse_osu_content


@dataclass
class OszFileInfo:
    """OSZ文件中的文件信息"""

    filename: str
    size: int
    md5_hash: str
    content: bytes
    file_type: str  # 'osu', 'audio', 'image', 'video', 'storyboard', 'other'


@dataclass
class OszMapset:
    """解析后的OSZ谱面集信息"""

    title: str
    artist: str
    creator: str
    source: str = ""
    tags: str = ""
    description: str = ""

    # 文件信息
    osz_filename: str = ""
    osz_hash: str = ""
    osz_size: int = 0

    # 谱面难度列表
    beatmaps: list[OsuMapData] = field(default_factory=list)

    # 文件列表
    files: list[OszFileInfo] = field(default_factory=list)

    def __post_init__(self):
        # 这里不再需要手动初始化，field(default_factory=list)已经处理了
        pass


class OszProcessor:
    """OSZ文件处理器"""

    # 支持的文件类型
    AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    VIDEO_EXTENSIONS = {".avi", ".flv", ".mpg", ".wmv", ".mp4", ".m4v"}
    STORYBOARD_EXTENSIONS = {".osb", ".txt"}

    def __init__(self, storage_path: str | Path):
        """
        初始化OSZ处理器

        Args:
            storage_path: 文件存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def process_osz_file(
        self,
        osz_file_path: str | Path,
        original_filename: str = "",
    ) -> OszMapset:
        """
        处理OSZ文件

        Args:
            osz_file_path: OSZ文件路径
            original_filename: 原始文件名

        Returns:
            OszMapset: 解析后的谱面集信息
        """
        osz_path = Path(osz_file_path)

        # 计算文件哈希
        osz_hash = self._calculate_file_hash(osz_path)
        osz_size = osz_path.stat().st_size

        # 解压和解析
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir)

            # 解压OSZ文件
            try:
                with zipfile.ZipFile(osz_path, "r") as zip_file:
                    zip_file.extractall(extract_path)
            except zipfile.BadZipFile:
                raise ValueError("Invalid OSZ file: not a valid zip archive")

            # 解析文件
            mapset = self._parse_extracted_files(extract_path)

        # 设置OSZ文件信息
        mapset.osz_filename = original_filename or osz_path.name
        mapset.osz_hash = osz_hash
        mapset.osz_size = osz_size

        return mapset

    def process_osz_bytes(self, osz_data: bytes, original_filename: str) -> OszMapset:
        """
        处理OSZ文件字节数据

        Args:
            osz_data: OSZ文件字节数据
            original_filename: 原始文件名

        Returns:
            OszMapset: 解析后的谱面集信息
        """
        # 计算文件哈希
        osz_hash = hashlib.md5(osz_data).hexdigest()
        osz_size = len(osz_data)

        # 解压和解析
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir)

            # 创建临时OSZ文件
            temp_osz = extract_path / "temp.osz"
            temp_osz.write_bytes(osz_data)

            # 解压OSZ文件
            try:
                with zipfile.ZipFile(temp_osz, "r") as zip_file:
                    zip_file.extractall(extract_path)
            except zipfile.BadZipFile:
                raise ValueError("Invalid OSZ file: not a valid zip archive")

            # 解析文件
            mapset = self._parse_extracted_files(extract_path)

        # 设置OSZ文件信息
        mapset.osz_filename = original_filename
        mapset.osz_hash = osz_hash
        mapset.osz_size = osz_size

        return mapset

    def _parse_extracted_files(self, extract_path: Path) -> OszMapset:
        """解析解压后的文件"""
        mapset = OszMapset(title="", artist="", creator="")

        # 遍历所有文件
        for file_path in extract_path.rglob("*"):
            if file_path.is_file():
                self._process_file(file_path, extract_path, mapset)

        # 验证谱面集
        if not mapset.beatmaps:
            raise ValueError("No valid beatmap files found in OSZ")

        # 从第一个谱面获取基本信息
        first_map = mapset.beatmaps[0]
        if not mapset.title:
            mapset.title = first_map.title or first_map.title_unicode
        if not mapset.artist:
            mapset.artist = first_map.artist or first_map.artist_unicode
        if not mapset.creator:
            mapset.creator = first_map.creator
        if not mapset.source:
            mapset.source = first_map.source
        if not mapset.tags:
            mapset.tags = first_map.tags

        return mapset

    def _process_file(
        self,
        file_path: Path,
        base_path: Path,
        mapset: OszMapset,
    ) -> None:
        """处理单个文件"""
        relative_path = file_path.relative_to(base_path)
        filename = str(relative_path).replace("\\", "/")

        # 读取文件内容
        try:
            content = file_path.read_bytes()
        except Exception as e:
            print(f"Warning: Cannot read file {filename}: {e}")
            return

        # 计算文件信息
        file_size = len(content)
        file_hash = hashlib.md5(content).hexdigest()
        file_type = self._get_file_type(file_path)

        # 创建文件信息
        file_info = OszFileInfo(
            filename=filename,
            size=file_size,
            md5_hash=file_hash,
            content=content,
            file_type=file_type,
        )
        mapset.files.append(file_info)

        # 如果是.osu文件，解析谱面数据
        if file_type == "osu":
            try:
                content_str = content.decode("utf-8", errors="ignore")
                osu_data = parse_osu_content(content_str)

                # 设置文件相关信息
                osu_data.filename = filename
                osu_data.md5 = file_hash

                mapset.beatmaps.append(osu_data)
            except Exception as e:
                print(f"Warning: Cannot parse beatmap {filename}: {e}")

    def _get_file_type(self, file_path: Path) -> str:
        """根据文件扩展名确定文件类型"""
        ext = file_path.suffix.lower()

        if ext == ".osu":
            return "osu"
        elif ext in self.AUDIO_EXTENSIONS:
            return "audio"
        elif ext in self.IMAGE_EXTENSIONS:
            return "image"
        elif ext in self.VIDEO_EXTENSIONS:
            return "video"
        elif ext in self.STORYBOARD_EXTENSIONS:
            return "storyboard"
        else:
            return "other"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def store_osz_file(self, osz_data: bytes, osz_hash: str) -> Path:
        """
        存储OSZ文件到磁盘

        Args:
            osz_data: OSZ文件数据
            osz_hash: 文件哈希

        Returns:
            Path: 存储的文件路径
        """
        # 使用哈希值的前两位作为子目录，避免单个目录文件过多
        sub_dir = osz_hash[:2]
        storage_dir = self.storage_path / "osz" / sub_dir
        storage_dir.mkdir(parents=True, exist_ok=True)

        # 存储文件
        file_path = storage_dir / f"{osz_hash}.osz"
        file_path.write_bytes(osz_data)

        return file_path

    def store_map_files(self, mapset: OszMapset, map_id: int) -> list[tuple[str, Path]]:
        """
        存储谱面相关文件

        Args:
            mapset: 谱面集数据
            map_id: 谱面ID

        Returns:
            List[Tuple[str, Path]]: (file_type, file_path) 的列表
        """
        stored_files = []

        # 为每个谱面创建目录
        for beatmap in mapset.beatmaps:
            map_dir = self.storage_path / "maps" / str(map_id) / beatmap.md5[:2]
            map_dir.mkdir(parents=True, exist_ok=True)

            # 存储对应的文件
            for file_info in mapset.files:
                if file_info.file_type == "osu" and file_info.md5_hash == beatmap.md5:
                    # 存储.osu文件
                    file_path = map_dir / f"{beatmap.md5}.osu"
                    file_path.write_bytes(file_info.content)
                    stored_files.append(("osu", file_path))

                elif file_info.file_type in ("audio", "image", "video"):
                    # 存储资源文件 (音频、图片、视频)
                    file_path = map_dir / file_info.filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(file_info.content)
                    stored_files.append((file_info.file_type, file_path))

        return stored_files

    def validate_osz(self, mapset: OszMapset) -> list[str]:
        """
        验证OSZ文件的有效性

        Args:
            mapset: 谱面集数据

        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []

        # 基本信息验证
        if not mapset.title.strip():
            errors.append("Mapset title is required")

        if not mapset.artist.strip():
            errors.append("Artist name is required")

        if not mapset.creator.strip():
            errors.append("Creator name is required")

        # 谱面验证
        if not mapset.beatmaps:
            errors.append("At least one beatmap is required")
            return errors

        # 检查每个谱面
        seen_versions = set()
        for beatmap in mapset.beatmaps:
            # 检查重复的版本名
            version_key = (beatmap.mode, beatmap.version)
            if version_key in seen_versions:
                errors.append(
                    f"Duplicate difficulty version: {beatmap.version} (mode {beatmap.mode})",
                )
            seen_versions.add(version_key)

            # 检查必要的谱面信息
            if not beatmap.version.strip():
                errors.append("Beatmap version/difficulty name is required")

            if not beatmap.creator.strip():
                errors.append("Beatmap creator is required")

            # 检查击打物件
            if not beatmap.hit_objects:
                errors.append(f"No hit objects found in difficulty: {beatmap.version}")

            # 检查音频文件
            if beatmap.audio_filename:
                audio_found = any(
                    f.filename.lower() == beatmap.audio_filename.lower()
                    and f.file_type == "audio"
                    for f in mapset.files
                )
                if not audio_found:
                    errors.append(f"Audio file not found: {beatmap.audio_filename}")

        # 检查至少有一个音频文件
        audio_files = [f for f in mapset.files if f.file_type == "audio"]
        if not audio_files:
            errors.append("At least one audio file is required")

        return errors


def process_osz_upload(
    file_data: bytes,
    original_filename: str,
    storage_path: str | Path,
) -> OszMapset:
    """
    便捷函数：处理OSZ文件上传

    Args:
        file_data: 文件数据
        original_filename: 原始文件名
        storage_path: 存储路径

    Returns:
        OszMapset: 解析后的谱面集
    """
    processor = OszProcessor(storage_path)
    return processor.process_osz_bytes(file_data, original_filename)
