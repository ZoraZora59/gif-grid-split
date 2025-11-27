"""
精灵表转 GIF Web 应用
Flask 后端 API
"""

import os
import sys
import uuid
import time
import shutil
import threading
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from io import BytesIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import analyze_spritesheet, slice_spritesheet_to_frames, create_gif_from_frames
from core.slicer import slice_spritesheet
from web.idea_generator import generate_idea_plan

app = Flask(__name__)

# ============================================
# 配置
# ============================================

# 数据存储目录（可通过环境变量覆盖）
DATA_FOLDER = os.environ.get('DATA_FOLDER', os.path.join(os.path.dirname(__file__), 'data'))

# 子目录
ORIGINALS_FOLDER = os.path.join(DATA_FOLDER, 'originals')    # 原图
FRAMES_FOLDER = os.path.join(DATA_FOLDER, 'frames')          # 切分后的帧
GIFS_FOLDER = os.path.join(DATA_FOLDER, 'gifs')              # 生成的 GIF
TEMP_FOLDER = os.path.join(DATA_FOLDER, 'temp')              # 临时文件

# 文件限制
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 文件保留时间（秒）
FILE_RETENTION_DAYS = int(os.environ.get('FILE_RETENTION_DAYS', 30))
FILE_MAX_AGE = FILE_RETENTION_DAYS * 24 * 3600  # 30天

# 清理间隔（秒）
CLEANUP_INTERVAL = 6 * 3600  # 每6小时清理一次

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保目录存在
for folder in [DATA_FOLDER, ORIGINALS_FOLDER, FRAMES_FOLDER, GIFS_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# ============================================
# 辅助函数
# ============================================

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_ext(filename):
    """获取文件扩展名"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'


def generate_task_id():
    """生成任务ID（基于时间戳+UUID）"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_uuid = str(uuid.uuid4())[:8]
    return f"{timestamp}_{short_uuid}"


def save_metadata(task_id, metadata):
    """保存任务元数据"""
    meta_path = os.path.join(DATA_FOLDER, f"{task_id}_meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def cleanup_old_files():
    """清理过期文件"""
    now = time.time()
    cleaned_count = 0
    
    # 清理各个目录
    for folder in [ORIGINALS_FOLDER, FRAMES_FOLDER, GIFS_FOLDER, TEMP_FOLDER]:
        if not os.path.exists(folder):
            continue
            
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            try:
                item_time = os.path.getmtime(item_path)
                if now - item_time > FILE_MAX_AGE:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    cleaned_count += 1
            except Exception as e:
                print(f"[清理] 删除失败: {item_path}, 错误: {e}")
    
    # 清理元数据文件
    for item in os.listdir(DATA_FOLDER):
        if item.endswith('_meta.json'):
            item_path = os.path.join(DATA_FOLDER, item)
            try:
                if now - os.path.getmtime(item_path) > FILE_MAX_AGE:
                    os.remove(item_path)
                    cleaned_count += 1
            except Exception:
                pass
    
    if cleaned_count > 0:
        print(f"[清理] 已清理 {cleaned_count} 个过期文件/目录")


def start_cleanup_thread():
    """启动后台清理线程"""
    def cleanup_loop():
        while True:
            time.sleep(CLEANUP_INTERVAL)
            print(f"[清理] 开始清理超过 {FILE_RETENTION_DAYS} 天的文件...")
            cleanup_old_files()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    print(f"[清理] 后台清理线程已启动，保留期限: {FILE_RETENTION_DAYS} 天")


# ============================================
# 路由
# ============================================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/idea', methods=['POST'])
def idea_to_plan():
    """调用 Gemini，根据创意生成精灵表计划。"""

    data = request.get_json(silent=True) or {}
    idea = (data.get('idea') or data.get('prompt') or '').strip()
    style = (data.get('style') or '').strip() or None
    model = (data.get('model') or '').strip() or None
    temperature = data.get('temperature', 0.6)

    if not idea:
        return jsonify({'error': '请提供 idea 字段'}), 400

    try:
        temperature_value = float(temperature)
    except (TypeError, ValueError):
        return jsonify({'error': 'temperature 参数格式不正确'}), 400

    task_id = generate_task_id()
    try:
        plan = generate_idea_plan(
            idea,
            style=style,
            model=model,
            temperature=temperature_value,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({'error': f'生成计划失败: {exc}'}), 500

    metadata = {
        'task_id': task_id,
        'idea': idea,
        'style': style,
        'model': model,
        'temperature': temperature_value,
        'idea_plan': plan,
        'create_time': datetime.now().isoformat(),
    }
    save_metadata(task_id, metadata)

    return jsonify({
        'success': True,
        'task_id': task_id,
        'plan': plan,
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析上传的图片，返回网格检测结果"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400
    
    try:
        # 生成任务ID
        task_id = generate_task_id()
        
        # 读取图片数据
        image_data = file.read()
        
        # 保存原图
        original_filename = secure_filename(file.filename) or f"image.{get_file_ext(file.filename)}"
        ext = get_file_ext(original_filename)
        original_path = os.path.join(ORIGINALS_FOLDER, f"{task_id}.{ext}")
        with open(original_path, 'wb') as f:
            f.write(image_data)
        
        # 分析图片
        result = analyze_spritesheet(image_data)
        
        # 保存临时文件路径（用于后续转换）
        temp_path = os.path.join(TEMP_FOLDER, f"{task_id}.tmp")
        with open(temp_path, 'wb') as f:
            f.write(image_data)
        
        # 保存元数据
        metadata = {
            'task_id': task_id,
            'original_filename': original_filename,
            'original_path': original_path,
            'upload_time': datetime.now().isoformat(),
            'analysis': result
        }
        save_metadata(task_id, metadata)
        
        return jsonify({
            'success': True,
            'file_id': task_id,
            'analysis': {
                'rows': result['rows'],
                'cols': result['cols'],
                'margin': result['margin'],
                'line_width': result['line_width'],
                'confidence': result['confidence'],
                'image_size': result['image_size'],
                'total_frames': result['rows'] * result['cols']
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/api/convert', methods=['POST'])
def convert():
    """将精灵表转换为 GIF"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    task_id = data.get('file_id')
    rows = data.get('rows')
    cols = data.get('cols')
    margin = data.get('margin', 2)
    duration = data.get('duration', 80)
    
    if not all([task_id, rows, cols]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    temp_path = os.path.join(TEMP_FOLDER, f"{task_id}.tmp")
    
    if not os.path.exists(temp_path):
        return jsonify({'error': '文件已过期，请重新上传'}), 404
    
    try:
        # 创建帧目录
        frames_dir = os.path.join(FRAMES_FOLDER, task_id)
        os.makedirs(frames_dir, exist_ok=True)
        
        # 切片并保存帧文件
        saved_frames = slice_spritesheet(temp_path, frames_dir, rows, cols, margin)
        
        # 从保存的帧生成 GIF
        frames = slice_spritesheet_to_frames(temp_path, rows, cols, margin)
        gif_data = create_gif_from_frames(frames, duration)
        
        # 保存 GIF
        gif_path = os.path.join(GIFS_FOLDER, f"{task_id}.gif")
        with open(gif_path, 'wb') as f:
            f.write(gif_data)
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except Exception:
            pass
        
        # 更新元数据
        meta_path = os.path.join(DATA_FOLDER, f"{task_id}_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata.update({
                'frames_dir': frames_dir,
                'frames_count': len(saved_frames),
                'gif_path': gif_path,
                'convert_time': datetime.now().isoformat(),
                'params': {
                    'rows': rows,
                    'cols': cols,
                    'margin': margin,
                    'duration': duration
                }
            })
            save_metadata(task_id, metadata)
        
        return jsonify({
            'success': True,
            'gif_id': task_id,
            'download_url': f'/api/download/{task_id}',
            'frames_count': len(saved_frames)
        })
    
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500


@app.route('/api/download/<task_id>')
def download(task_id):
    """下载生成的 GIF"""
    # 安全检查
    if not task_id.replace('-', '').replace('_', '').isalnum():
        return jsonify({'error': '无效的文件ID'}), 400
    
    gif_path = os.path.join(GIFS_FOLDER, f"{task_id}.gif")
    
    if not os.path.exists(gif_path):
        return jsonify({'error': '文件不存在或已过期'}), 404
    
    return send_file(
        gif_path,
        mimetype='image/gif',
        as_attachment=True,
        download_name='sprite_animation.gif'
    )


@app.route('/api/preview/<task_id>')
def preview(task_id):
    """预览生成的 GIF"""
    if not task_id.replace('-', '').replace('_', '').isalnum():
        return jsonify({'error': '无效的文件ID'}), 400
    
    gif_path = os.path.join(GIFS_FOLDER, f"{task_id}.gif")
    
    if not os.path.exists(gif_path):
        return jsonify({'error': '文件不存在或已过期'}), 404
    
    return send_file(gif_path, mimetype='image/gif')


@app.route('/api/stats')
def stats():
    """获取存储统计信息（管理用）"""
    def get_folder_stats(folder):
        if not os.path.exists(folder):
            return {'count': 0, 'size': 0}
        
        count = 0
        size = 0
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            if os.path.isfile(item_path):
                count += 1
                size += os.path.getsize(item_path)
            elif os.path.isdir(item_path):
                count += 1
                for root, dirs, files in os.walk(item_path):
                    for f in files:
                        size += os.path.getsize(os.path.join(root, f))
        return {'count': count, 'size': size}
    
    return jsonify({
        'retention_days': FILE_RETENTION_DAYS,
        'originals': get_folder_stats(ORIGINALS_FOLDER),
        'frames': get_folder_stats(FRAMES_FOLDER),
        'gifs': get_folder_stats(GIFS_FOLDER),
        'temp': get_folder_stats(TEMP_FOLDER)
    })


# ============================================
# 启动
# ============================================

# 启动时清理旧文件
cleanup_old_files()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080, help='服务端口')
    parser.add_argument('--data-dir', type=str, help='数据存储目录')
    args = parser.parse_args()
    
    if args.data_dir:
        DATA_FOLDER = args.data_dir
        ORIGINALS_FOLDER = os.path.join(DATA_FOLDER, 'originals')
        FRAMES_FOLDER = os.path.join(DATA_FOLDER, 'frames')
        GIFS_FOLDER = os.path.join(DATA_FOLDER, 'gifs')
        TEMP_FOLDER = os.path.join(DATA_FOLDER, 'temp')
        for folder in [DATA_FOLDER, ORIGINALS_FOLDER, FRAMES_FOLDER, GIFS_FOLDER, TEMP_FOLDER]:
            os.makedirs(folder, exist_ok=True)
    
    # 启动后台清理线程
    start_cleanup_thread()
    
    # 运行服务器
    print(f"\n🚀 服务已启动: http://localhost:{args.port}")
    print(f"📁 数据目录: {DATA_FOLDER}")
    print(f"📅 文件保留: {FILE_RETENTION_DAYS} 天\n")
    app.run(host='0.0.0.0', port=args.port, debug=False)
