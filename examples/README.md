# 示例文件

本目录包含用于测试的示例精灵表图片。

## 柯南攻击图片.jpg

- **网格**: 6 × 6
- **尺寸**: 1024 × 1024 像素
- **帧数**: 36 帧

### 使用方法

**Web 方式**：直接上传到网页即可自动识别

**命令行方式**：

```bash
cd cli
python slice_spritesheet.py -i ../examples/柯南攻击图片.jpg --auto -o frames
python make_gif.py -i frames -o conan.gif
```

