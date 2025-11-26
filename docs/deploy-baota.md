# 宝塔面板部署指南

本文档介绍如何在宝塔面板服务器上部署 Sprite → GIF 应用。

---

## 📋 环境要求

- 宝塔面板 7.0+
- Python 3.8+
- 建议内存 1GB+

---

## 🚀 部署步骤

### 1. 安装 Python 项目管理器

1. 登录宝塔面板
2. 进入 **软件商店**
3. 搜索并安装 **Python项目管理器**

### 2. 上传项目代码

**方式一：Git 克隆（推荐）**

```bash
# SSH 登录服务器
cd /www/wwwroot
git clone https://github.com/ZoraZora59/gif-grid-split.git
cd gif-grid-split
```

**方式二：宝塔文件管理器上传**

1. 进入 **文件** 管理器
2. 进入 `/www/wwwroot/`
3. 上传项目压缩包并解压

### 3. 创建数据目录

```bash
# 创建数据存储目录（存放用户上传的文件）
mkdir -p /www/wwwroot/gif-grid-split/data
chmod 755 /www/wwwroot/gif-grid-split/data
```

### 4. 使用 Python 项目管理器配置

1. 打开 **Python项目管理器**
2. 点击 **添加项目**
3. 填写配置：

| 配置项 | 值 |
|--------|-----|
| 项目名称 | `sprite-to-gif` |
| 项目路径 | `/www/wwwroot/gif-grid-split` |
| Python版本 | `3.8+`（选择已安装的版本） |
| 框架 | `flask` |
| 启动方式 | `gunicorn` |
| 启动文件 | `web/app.py` |
| 端口 | `8080`（或其他未占用端口） |

4. **环境变量**（在高级设置中添加）：

```
DATA_FOLDER=/www/wwwroot/gif-grid-split/data
FILE_RETENTION_DAYS=30
```

5. 点击 **确定** 创建项目

### 5. 安装依赖

项目创建后，点击项目进入管理页面：

1. 点击 **模块** 标签
2. 在输入框中填入：`Flask Pillow gunicorn`
3. 点击 **安装**

或者通过 SSH：

```bash
cd /www/wwwroot/gif-grid-split
source /www/server/pyproject_evn/sprite-to-gif/bin/activate
pip install -r requirements.txt
```

### 6. 启动项目

在 Python 项目管理器中点击 **启动**

### 7. 配置 Nginx 反向代理

1. 进入 **网站** 管理
2. 添加站点（如 `gif.yourdomain.com`）
3. 点击站点进入 **设置**
4. 选择 **反向代理** → **添加反向代理**

配置：
```
代理名称: sprite-to-gif
目标URL: http://127.0.0.1:8080
发送域名: $host
```

5. 点击 **配置文件**，添加以下配置：

```nginx
# 在 location / 块中添加
client_max_body_size 20m;  # 允许上传 20MB 文件

# 添加 WebSocket 支持（如需要）
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 8. 配置 SSL（可选但推荐）

1. 在站点设置中选择 **SSL**
2. 申请 Let's Encrypt 免费证书
3. 开启 **强制 HTTPS**

---

## 📁 文件存储结构

用户上传的文件存储在 `/www/wwwroot/gif-grid-split/data/` 目录：

```
data/
├── originals/          # 原始上传图片
│   ├── 20241126_143052_a1b2c3d4.jpg
│   └── ...
├── frames/             # 切分后的帧
│   ├── 20241126_143052_a1b2c3d4/
│   │   ├── frame_001.png
│   │   ├── frame_002.png
│   │   └── ...
│   └── ...
├── gifs/               # 生成的 GIF
│   ├── 20241126_143052_a1b2c3d4.gif
│   └── ...
├── temp/               # 临时文件
└── *_meta.json         # 任务元数据
```

### 文件命名规则

文件名格式：`YYYYMMDD_HHMMSS_uuid8`

例如：`20241126_143052_a1b2c3d4`
- `20241126` - 日期
- `143052` - 时间
- `a1b2c3d4` - 8位UUID

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATA_FOLDER` | 数据存储目录 | `web/data` |
| `FILE_RETENTION_DAYS` | 文件保留天数 | `30` |

### 修改保留时间

编辑项目环境变量，修改 `FILE_RETENTION_DAYS`：

```bash
FILE_RETENTION_DAYS=60  # 改为60天
```

然后重启项目。

---

## 🔧 运维命令

### 查看存储统计

访问 `http://你的域名/api/stats` 可以查看存储统计：

```json
{
  "retention_days": 30,
  "originals": {"count": 150, "size": 45000000},
  "frames": {"count": 150, "size": 120000000},
  "gifs": {"count": 150, "size": 80000000},
  "temp": {"count": 2, "size": 500000}
}
```

### 手动清理过期文件

```bash
cd /www/wwwroot/gif-grid-split
source /www/server/pyproject_evn/sprite-to-gif/bin/activate
python -c "from web.app import cleanup_old_files; cleanup_old_files()"
```

### 查看日志

在 Python 项目管理器中点击 **日志** 查看运行日志。

---

## 🔒 安全建议

1. **限制上传大小**：已在 Nginx 配置 `client_max_body_size`
2. **启用 HTTPS**：保护用户数据传输
3. **定期备份**：如果需要长期保存，定期备份 `data/` 目录
4. **监控磁盘**：关注磁盘使用情况，避免存储耗尽

---

## ❓ 常见问题

### Q: 启动失败，提示找不到模块

检查虚拟环境是否激活，依赖是否安装完整：

```bash
source /www/server/pyproject_evn/sprite-to-gif/bin/activate
pip install Flask Pillow gunicorn
```

### Q: 上传文件失败

1. 检查 Nginx 配置的 `client_max_body_size`
2. 检查 `data/` 目录权限

```bash
chmod -R 755 /www/wwwroot/gif-grid-split/data
chown -R www:www /www/wwwroot/gif-grid-split/data
```

### Q: 文件没有自动清理

确认后台清理线程正常运行。可以查看日志中是否有 `[清理]` 相关输出。

### Q: 如何迁移数据

只需要备份和恢复 `data/` 目录即可。

---

## 📊 磁盘空间估算

假设每天 100 个转换任务，每个任务：
- 原图：~500KB
- 帧文件：~2MB（36帧）
- GIF：~500KB

每天新增：~300MB
30天累计：~9GB

建议预留 **20GB+** 磁盘空间。

