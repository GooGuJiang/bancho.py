"""osu!谱面文件解析器
解析.osu文件格式，提取谱面元数据和难度信息
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


@dataclass
class TimingPoint:
    """时间点数据"""

    time: int
    beat_length: float
    meter: int
    sample_set: int
    sample_index: int
    volume: int
    uninherited: bool
    effects: int


@dataclass
class HitObject:
    """击打物件数据"""

    x: int
    y: int
    time: int
    type: int
    hit_sound: int
    object_params: str = ""
    hit_sample: str = ""


@dataclass
class OsuMapData:
    """解析后的.osu文件数据"""

    # 基本信息
    osu_file_format: int = 14

    # 文件相关信息 (在解析后设置)
    filename: str = ""
    md5: str = ""

    # [General] 部分
    audio_filename: str = ""
    audio_lead_in: int = 0
    audio_hash: str = ""
    preview_time: int = -1
    countdown: int = 1
    sample_set: str = "Normal"
    stack_leniency: float = 0.7
    mode: int = 0
    letterbox_in_breaks: bool = False
    story_fire_in_front: bool = True
    use_skin_sprites: bool = False
    always_show_playfield: bool = False
    overlay_position: str = "NoChange"
    skin_preference: str = ""
    epilepsy_warning: bool = False
    countdown_offset: int = 0
    special_style: bool = False
    widescreen_storyboard: bool = False
    samples_match_playback_rate: bool = False

    # [Editor] 部分
    bookmarks: list[int] = field(default_factory=list)
    distance_spacing: float = 1.0
    beat_divisor: int = 4
    grid_size: int = 4
    timeline_zoom: float = 1.0

    # [Metadata] 部分
    title: str = ""
    title_unicode: str = ""
    artist: str = ""
    artist_unicode: str = ""
    creator: str = ""
    version: str = ""
    source: str = ""
    tags: str = ""
    beatmap_id: int = 0
    beatmapset_id: int = 0

    # [Difficulty] 部分
    hp_drain_rate: float = 5.0
    circle_size: float = 5.0
    overall_difficulty: float = 5.0
    approach_rate: float = 5.0
    slider_multiplier: float = 1.4
    slider_tick_rate: float = 1.0

    # [Events] 部分 (简化处理)
    background_filename: str = ""
    break_periods: list[tuple] = field(default_factory=list)

    # [TimingPoints] 部分
    timing_points: list[TimingPoint] = field(default_factory=list)

    # [Colours] 部分
    combo_colours: list[tuple] = field(default_factory=list)

    # [HitObjects] 部分
    hit_objects: list[HitObject] = field(default_factory=list)

    # 计算得出的信息
    total_length: int = 0  # 总长度(毫秒)
    hit_length: int = 0  # 击打长度(毫秒)
    max_combo: int = 0
    bpm: float = 0.0

    def __post_init__(self):
        """初始化默认值"""
        # 这里不再需要手动初始化，field(default_factory=list)已经处理了
        pass


class OsuFileParser:
    """osu!文件解析器"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置解析器状态"""
        self.current_section = ""
        self.data = OsuMapData()

    def parse_file(self, file_path: str | Path) -> OsuMapData:
        """解析.osu文件"""
        self.reset()

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content)

    def parse_content(self, content: str) -> OsuMapData:
        """解析.osu文件内容"""
        self.reset()

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            try:
                self._parse_line(line.strip())
            except Exception as e:
                print(f"Warning: Error parsing line {line_num}: {line.strip()}")
                print(f"Error: {e}")
                continue

        # 计算派生信息
        self._calculate_derived_info()

        return self.data

    def _parse_line(self, line: str) -> None:
        """解析单行内容"""
        if not line or line.startswith("//"):
            return

        # 检查是否是版本行
        if line.startswith("osu file format v"):
            try:
                self.data.osu_file_format = int(line.split("v")[1])
            except (IndexError, ValueError):
                pass
            return

        # 检查是否是段落标题
        if line.startswith("[") and line.endswith("]"):
            self.current_section = line[1:-1]
            return

        # 根据当前段落解析内容
        if self.current_section == "General":
            self._parse_general(line)
        elif self.current_section == "Editor":
            self._parse_editor(line)
        elif self.current_section == "Metadata":
            self._parse_metadata(line)
        elif self.current_section == "Difficulty":
            self._parse_difficulty(line)
        elif self.current_section == "Events":
            self._parse_events(line)
        elif self.current_section == "TimingPoints":
            self._parse_timing_points(line)
        elif self.current_section == "Colours":
            self._parse_colours(line)
        elif self.current_section == "HitObjects":
            self._parse_hit_objects(line)

    def _parse_key_value(self, line: str) -> tuple[str, str]:
        """解析键值对"""
        if ":" not in line:
            return "", ""

        key, value = line.split(":", 1)
        return key.strip(), value.strip()

    def _parse_general(self, line: str) -> None:
        """解析[General]段落"""
        key, value = self._parse_key_value(line)
        if not key:
            return

        try:
            if key == "AudioFilename":
                self.data.audio_filename = value
            elif key == "AudioLeadIn":
                self.data.audio_lead_in = int(value)
            elif key == "AudioHash":
                self.data.audio_hash = value
            elif key == "PreviewTime":
                self.data.preview_time = int(value)
            elif key == "Countdown":
                self.data.countdown = int(value)
            elif key == "SampleSet":
                self.data.sample_set = value
            elif key == "StackLeniency":
                self.data.stack_leniency = float(value)
            elif key == "Mode":
                self.data.mode = int(value)
            elif key == "LetterboxInBreaks":
                self.data.letterbox_in_breaks = value == "1"
            elif key == "StoryFireInFront":
                self.data.story_fire_in_front = value == "1"
            elif key == "UseSkinSprites":
                self.data.use_skin_sprites = value == "1"
            elif key == "AlwaysShowPlayfield":
                self.data.always_show_playfield = value == "1"
            elif key == "OverlayPosition":
                self.data.overlay_position = value
            elif key == "SkinPreference":
                self.data.skin_preference = value
            elif key == "EpilepsyWarning":
                self.data.epilepsy_warning = value == "1"
            elif key == "CountdownOffset":
                self.data.countdown_offset = int(value)
            elif key == "SpecialStyle":
                self.data.special_style = value == "1"
            elif key == "WidescreenStoryboard":
                self.data.widescreen_storyboard = value == "1"
            elif key == "SamplesMatchPlaybackRate":
                self.data.samples_match_playback_rate = value == "1"
        except (ValueError, TypeError):
            pass

    def _parse_editor(self, line: str) -> None:
        """解析[Editor]段落"""
        key, value = self._parse_key_value(line)
        if not key:
            return

        try:
            if key == "Bookmarks":
                if value:
                    self.data.bookmarks = [int(x.strip()) for x in value.split(",")]
            elif key == "DistanceSpacing":
                self.data.distance_spacing = float(value)
            elif key == "BeatDivisor":
                self.data.beat_divisor = int(value)
            elif key == "GridSize":
                self.data.grid_size = int(value)
            elif key == "TimelineZoom":
                self.data.timeline_zoom = float(value)
        except (ValueError, TypeError):
            pass

    def _parse_metadata(self, line: str) -> None:
        """解析[Metadata]段落"""
        key, value = self._parse_key_value(line)
        if not key:
            return

        if key == "Title":
            self.data.title = value
        elif key == "TitleUnicode":
            self.data.title_unicode = value
        elif key == "Artist":
            self.data.artist = value
        elif key == "ArtistUnicode":
            self.data.artist_unicode = value
        elif key == "Creator":
            self.data.creator = value
        elif key == "Version":
            self.data.version = value
        elif key == "Source":
            self.data.source = value
        elif key == "Tags":
            self.data.tags = value
        elif key == "BeatmapID":
            try:
                self.data.beatmap_id = int(value)
            except ValueError:
                pass
        elif key == "BeatmapSetID":
            try:
                self.data.beatmapset_id = int(value)
            except ValueError:
                pass

    def _parse_difficulty(self, line: str) -> None:
        """解析[Difficulty]段落"""
        key, value = self._parse_key_value(line)
        if not key:
            return

        try:
            if key == "HPDrainRate":
                self.data.hp_drain_rate = float(value)
            elif key == "CircleSize":
                self.data.circle_size = float(value)
            elif key == "OverallDifficulty":
                self.data.overall_difficulty = float(value)
            elif key == "ApproachRate":
                self.data.approach_rate = float(value)
            elif key == "SliderMultiplier":
                self.data.slider_multiplier = float(value)
            elif key == "SliderTickRate":
                self.data.slider_tick_rate = float(value)
        except (ValueError, TypeError):
            pass

    def _parse_events(self, line: str) -> None:
        """解析[Events]段落"""
        if line.startswith("0,0,"):  # Background
            parts = line.split(",")
            if len(parts) >= 3:
                filename = parts[2].strip('"')
                self.data.background_filename = filename
        elif line.startswith("2,"):  # Break period
            parts = line.split(",")
            if len(parts) >= 3:
                try:
                    start_time = int(parts[1])
                    end_time = int(parts[2])
                    self.data.break_periods.append((start_time, end_time))
                except ValueError:
                    pass

    def _parse_timing_points(self, line: str) -> None:
        """解析[TimingPoints]段落"""
        parts = line.split(",")
        if len(parts) < 2:
            return

        try:
            time = int(float(parts[0]))
            beat_length = float(parts[1])
            meter = int(parts[2]) if len(parts) > 2 else 4
            sample_set = int(parts[3]) if len(parts) > 3 else 0
            sample_index = int(parts[4]) if len(parts) > 4 else 0
            volume = int(parts[5]) if len(parts) > 5 else 100
            uninherited = parts[6] == "1" if len(parts) > 6 else True
            effects = int(parts[7]) if len(parts) > 7 else 0

            timing_point = TimingPoint(
                time=time,
                beat_length=beat_length,
                meter=meter,
                sample_set=sample_set,
                sample_index=sample_index,
                volume=volume,
                uninherited=uninherited,
                effects=effects,
            )
            self.data.timing_points.append(timing_point)
        except (ValueError, IndexError):
            pass

    def _parse_colours(self, line: str) -> None:
        """解析[Colours]段落"""
        key, value = self._parse_key_value(line)
        if key.startswith("Combo") and value:
            try:
                rgb = tuple(int(x.strip()) for x in value.split(","))
                if len(rgb) == 3:
                    self.data.combo_colours.append(rgb)
            except ValueError:
                pass

    def _parse_hit_objects(self, line: str) -> None:
        """解析[HitObjects]段落"""
        parts = line.split(",")
        if len(parts) < 5:
            return

        try:
            x = int(parts[0])
            y = int(parts[1])
            time = int(parts[2])
            obj_type = int(parts[3])
            hit_sound = int(parts[4])

            # 获取剩余参数
            object_params = ",".join(parts[5:-1]) if len(parts) > 6 else ""
            hit_sample = parts[-1] if len(parts) > 5 else ""

            hit_object = HitObject(
                x=x,
                y=y,
                time=time,
                type=obj_type,
                hit_sound=hit_sound,
                object_params=object_params,
                hit_sample=hit_sample,
            )
            self.data.hit_objects.append(hit_object)
        except (ValueError, IndexError):
            pass

    def _calculate_derived_info(self) -> None:
        """计算派生信息"""
        if not self.data.hit_objects:
            return

        # 计算总长度和击打长度
        first_object_time = min(obj.time for obj in self.data.hit_objects)
        last_object_time = max(obj.time for obj in self.data.hit_objects)

        self.data.hit_length = last_object_time - first_object_time

        # 如果有preview_time，使用它来计算总长度，否则使用最后一个物件的时间
        if self.data.preview_time > 0:
            self.data.total_length = max(
                last_object_time + 2000,
                self.data.preview_time + 30000,
            )
        else:
            self.data.total_length = last_object_time + 2000

        # 计算最大连击数 (简化版本，只算圆圈和滑条)
        combo_count = 0
        for obj in self.data.hit_objects:
            obj_type = obj.type
            if obj_type & 1:  # 圆圈
                combo_count += 1
            elif obj_type & 2:  # 滑条
                # 简化处理，假设每个滑条算1个combo
                combo_count += 1
            elif obj_type & 8:  # 转盘
                combo_count += 1

        self.data.max_combo = combo_count

        # 计算BPM (使用第一个uninherited timing point)
        for tp in self.data.timing_points:
            if tp.uninherited and tp.beat_length > 0:
                self.data.bpm = 60000 / tp.beat_length
                break


def parse_osu_file(file_path: str | Path) -> OsuMapData:
    """便捷函数：解析.osu文件"""
    parser = OsuFileParser()
    return parser.parse_file(file_path)


def parse_osu_content(content: str) -> OsuMapData:
    """便捷函数：解析.osu文件内容"""
    parser = OsuFileParser()
    return parser.parse_content(content)
