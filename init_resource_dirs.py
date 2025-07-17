#!/usr/bin/env python3
"""初始化谱面资源目录结构"""

from __future__ import annotations

from pathlib import Path


def init_resource_directories():
    """初始化必要的目录结构"""

    # user_backend 资源目录
    base_dir = Path("user_backend/uploads/custom_maps")

    # 创建目录
    directories = [
        base_dir / "thumbs",  # 缩略图
        base_dir / "previews",  # 预览音频
        base_dir / "osz",  # OSZ 文件
        base_dir / "maps",  # 谱面文件
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # 创建 .gitkeep 文件
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep}")

    print("目录结构初始化完成！")


if __name__ == "__main__":
    init_resource_directories()
