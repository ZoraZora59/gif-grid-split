# 🎮 Sprite → GIF | 精灵表动画转换器

将网格排列的精灵表（Sprite Sheet）智能识别并转换为 GIF 动画。

支持 **Web 在线使用** 和 **命令行工具** 两种模式。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

---

## ✨ 功能特点

- 🔍 **AI 智能识别** - 自动检测网格行列数和分隔线宽度
- 🎨 **现代化界面** - 赛博朋克风格的科技感 UI
- ⚡ **实时预览** - 即时查看生成的 GIF 动画
- 🔒 **隐私安全** - 文件仅临时处理，自动清理
- 📱 **响应式设计** - 支持桌面和移动设备

---

## 🚀 快速开始

### 方式一：Web 服务部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/gif-grid-split.git
cd gif-grid-split
```

#### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 启动服务

```bash
# 开发模式
python web/app.py

# 生产模式（推荐）
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

#### 4. 访问

打开浏览器访问 `http://localhost:5000`

---

### 方式二：命令行工具

适合批量处理或脚本集成。

```bash
cd cli

# 使用示例图片测试
python slice_spritesheet.py -i ../examples/柯南攻击图片.jpg --auto
python make_gif.py -i frames -o conan.gif

# 自定义参数
python slice_spritesheet.py -i 图片.jpg -r 6 -c 6 -m 3
python make_gif.py -i frames -o output.gif -d 80
```

---

## 📦 示例文件

`examples/` 目录包含测试用的示例精灵表：

| 文件 | 网格 | 尺寸 | 说明 |
|------|------|------|------|
| `柯南攻击图片.jpg` | 6×6 | 1024×1024 | 36帧动画示例 |

---

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t sprite-to-gif .

# 运行容器
docker run -d -p 5000:5000 sprite-to-gif
```

---

## 📁 项目结构

```
gif-grid-split/
├── core/                   # 核心处理模块
│   ├── __init__.py
│   ├── detector.py         # 网格自动检测
│   ├── slicer.py           # 图片切片
│   └── gif_maker.py        # GIF 合成
│
├── web/                    # Web 应用
│   ├── app.py              # Flask 后端
│   ├── templates/          # HTML 模板
│   └── static/             # 静态资源
│
├── cli/                    # 命令行工具
│   ├── run.py              # 交互式引导
│   ├── slice_spritesheet.py
│   ├── make_gif.py
│   └── auto_detect.py
│
├── examples/               # 示例文件
│   └── 柯南攻击图片.jpg
│
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PORT` | 服务端口 | `5000` |
| `MAX_CONTENT_LENGTH` | 最大上传文件大小 | `16MB` |
| `TEMP_FILE_MAX_AGE` | 临时文件保留时间(秒) | `3600` |
| `ZENMUX_API_KEY` | ZenMux 平台分配的 Gemini 调用密钥（必填，务必通过环境变量注入） | - |
| `ZENMUX_BASE_URL` | Gemini 代理地址 | `https://zenmux.ai/api/vertex-ai` |
| `ZENMUX_GEMINI_MODEL` | 默认模型名称 | `google/gemini-3-pro-image-preview` |

### 临时文件管理

- 上传的文件存储在 `web/uploads/` 目录
- 后台线程每 10 分钟自动清理过期文件
- 默认保留时间为 1 小时

### 使用 Gemini（ZenMux）调用示例

项目提供了 `web/genai_client.py` 封装，确保密钥不写入代码：

```bash
export ZENMUX_API_KEY="你的 ZenMux SK"
# 可选：export ZENMUX_BASE_URL="https://zenmux.ai/api/vertex-ai"
# 可选：export ZENMUX_GEMINI_MODEL="google/gemini-3-pro-image-preview"
```

```python
from web.genai_client import generate_text

answer = generate_text("帮我设计一个像素风格的冒险主角动作列表")
print(answer)
```

如果希望让用户直接输入创意并生成精灵表计划，可调用新增的 `/api/idea` 接口：

```http
POST /api/idea
Content-Type: application/json

{
  "idea": "像素风蒸汽朋克猫咪骑士",
  "style": "复古赛博",
  "temperature": 0.6
}
```

**响应示例：**
```json
{
  "success": true,
  "task_id": "20250219_123456_abcd1234",
  "plan": {
    "title": "蒸汽朋克猫咪骑士",
    "image_prompt": "steampunk cat knight, pixel art, ...",
    "grid": {"rows": 4, "cols": 4, "cell_size": 256},
    "actions": ["idle", "walk", "attack"],
    "style_notes": "retro cyber pixel art",
    "raw": "模型原始输出文本"
  }
}
```

---

## 🔧 API 接口

### 分析图片

```http
POST /api/analyze
Content-Type: multipart/form-data

file: <图片文件>
```

**响应:**
```json
{
    "success": true,
    "file_id": "uuid",
    "analysis": {
        "rows": 6,
        "cols": 6,
        "margin": 3,
        "confidence": 0.95,
        "total_frames": 36
    }
}
```

### 转换为 GIF

```http
POST /api/convert
Content-Type: application/json

{
    "file_id": "uuid",
    "rows": 6,
    "cols": 6,
    "margin": 3,
    "duration": 80
}
```

**响应:**
```json
{
    "success": true,
    "gif_id": "uuid",
    "download_url": "/api/download/uuid"
}
```

### 下载 GIF

```http
GET /api/download/{gif_id}
```

---

## 🛠️ 技术栈

- **后端**: Python, Flask
- **前端**: HTML5, CSS3, Vanilla JavaScript
- **图像处理**: Pillow
- **部署**: Gunicorn, Docker

---

## 🎨 界面预览

### 赛博朋克风格设计

- 深色主题配合霓虹光效
- 流畅的交互动画
- 三步式引导流程

---

## ❓ 常见问题

### Q: 检测结果不准确怎么办？

在第二步可以手动调整行列数和边距参数。

### Q: 支持哪些图片格式？

PNG, JPG, JPEG, WebP, BMP, GIF

### Q: 最大支持多大的图片？

默认 16MB，可通过配置调整。

### Q: 文件会被保存吗？

不会。所有上传的文件在处理后 1 小时内自动删除。

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Pillow](https://pillow.readthedocs.io/) - Python 图像处理库
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
