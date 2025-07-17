# 谱面缩略图和预览音频功能说明

## 功能概述

在上传自定义谱面时，系统会自动生成：
1. **缩略图**：160x120 像素的 JPEG 图片，文件名格式为 `{beatmap_id}l.jpg`
2. **预览音频**：64kbps、22kHz、10秒长度的 MP3 预览音频

## 依赖安装

在 user_backend 环境中安装以下依赖：

```bash
pip install Pillow==10.1.0
pip install pydub==0.25.1
pip install opencv-python==4.8.1.78
```

## API 路由

### 获取缩略图
- **路径**: `/thumb/{beatmap_id}l.jpg`
- **方法**: GET
- **参数**: `beatmap_id` - 谱面ID
- **返回**: JPEG 图片文件
- **示例**: `GET /thumb/999999l.jpg`

### 获取预览音频 (user_backend)
- **路径**: `/preview/{beatmap_id}.mp3`
- **方法**: GET
- **参数**: `beatmap_id` - 谱面ID
- **返回**: MP3 音频文件
- **示例**: `GET /preview/999999.mp3`

### 主服务器缩略图路由
- **路径**: `/thumb/{beatmap_id}l.jpg`
- **方法**: GET
- **功能**: 自动检测是否为自定义谱面，从 user_backend 获取缩略图
- **兼容路径**: `/_mt/{beatmap_id}` (重定向到标准路由)

## 文件存储结构

```
user_backend/uploads/custom_maps/
├── thumbs/           # 缩略图目录
│   ├── 999999l.jpg   # 谱面缩略图
│   └── ...
├── previews/         # 预览音频目录
│   ├── 999999.mp3    # 预览音频
│   └── ...
├── osz/              # OSZ 文件
└── maps/             # 谱面文件
```

## 功能说明

### 缩略图生成
1. 尝试从 OSZ 文件中提取背景图片
2. 如果找到背景图，缩放并裁剪到 160x120
3. 如果没有背景图，使用默认颜色背景
4. 添加暗化遮罩和谱面ID文本水印
5. 保存为 JPEG 格式

### 预览音频生成
1. 从 OSZ 文件中提取音频文件
2. 根据 .osu 文件中的 PreviewTime 确定开始时间
3. 如果 PreviewTime 为 -1，从头开始截取
4. 截取 10 秒音频片段
5. 转换为 64kbps MP3，采样率 22kHz

## 错误处理
- 如果资源生成失败，不影响谱面上传
- 如果缩略图不存在，返回 404
- 如果预览音频不存在，返回 404

## 注意事项
1. 资源生成是异步进行的，不会阻塞上传流程
2. 生成的资源会缓存在本地，减少重复生成
3. 主服务器会代理自定义谱面的缩略图请求到 user_backend
4. 需要确保 user_backend 服务运行在 localhost:10050
