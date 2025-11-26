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
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from io import BytesIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import analyze_spritesheet, slice_spritesheet_to_frames, create_gif_from_frames

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
TEMP_FILE_MAX_AGE = 3600  # 临时文件保留时间（秒）

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    """清理过期的临时文件"""
    now = time.time()
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > TEMP_FILE_MAX_AGE:
                    os.remove(filepath)
            elif os.path.isdir(filepath):
                dir_age = now - os.path.getmtime(filepath)
                if dir_age > TEMP_FILE_MAX_AGE:
                    shutil.rmtree(filepath)
        except Exception as e:
            print(f"清理文件失败: {filepath}, 错误: {e}")


def start_cleanup_thread():
    """启动后台清理线程"""
    def cleanup_loop():
        while True:
            time.sleep(600)  # 每10分钟清理一次
            cleanup_old_files()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


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
        # 读取图片数据
        image_data = file.read()
        
        # 分析图片
        result = analyze_spritesheet(image_data)
        
        # 保存临时文件以供后续处理
        file_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.tmp")
        with open(temp_path, 'wb') as f:
            f.write(image_data)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
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
    
    file_id = data.get('file_id')
    rows = data.get('rows')
    cols = data.get('cols')
    margin = data.get('margin', 2)
    duration = data.get('duration', 80)
    
    if not all([file_id, rows, cols]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    temp_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.tmp")
    
    if not os.path.exists(temp_path):
        return jsonify({'error': '文件已过期，请重新上传'}), 404
    
    try:
        # 切片
        frames = slice_spritesheet_to_frames(temp_path, rows, cols, margin)
        
        # 生成 GIF
        gif_data = create_gif_from_frames(frames, duration)
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except Exception:
            pass
        
        # 保存 GIF 供下载
        gif_id = str(uuid.uuid4())
        gif_path = os.path.join(UPLOAD_FOLDER, f"{gif_id}.gif")
        with open(gif_path, 'wb') as f:
            f.write(gif_data)
        
        return jsonify({
            'success': True,
            'gif_id': gif_id,
            'download_url': f'/api/download/{gif_id}'
        })
    
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500


@app.route('/api/download/<gif_id>')
def download(gif_id):
    """下载生成的 GIF"""
    # 安全检查
    if not gif_id.replace('-', '').isalnum():
        return jsonify({'error': '无效的文件ID'}), 400
    
    gif_path = os.path.join(UPLOAD_FOLDER, f"{gif_id}.gif")
    
    if not os.path.exists(gif_path):
        return jsonify({'error': '文件不存在或已过期'}), 404
    
    return send_file(
        gif_path,
        mimetype='image/gif',
        as_attachment=True,
        download_name='sprite_animation.gif'
    )


@app.route('/api/preview/<gif_id>')
def preview(gif_id):
    """预览生成的 GIF"""
    if not gif_id.replace('-', '').isalnum():
        return jsonify({'error': '无效的文件ID'}), 400
    
    gif_path = os.path.join(UPLOAD_FOLDER, f"{gif_id}.gif")
    
    if not os.path.exists(gif_path):
        return jsonify({'error': '文件不存在或已过期'}), 404
    
    return send_file(gif_path, mimetype='image/gif')


# 启动时清理旧文件
cleanup_old_files()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080, help='服务端口')
    args = parser.parse_args()
    
    # 启动后台清理线程
    start_cleanup_thread()
    
    # 运行服务器
    print(f"\n🚀 服务已启动: http://localhost:{args.port}\n")
    app.run(host='0.0.0.0', port=args.port, debug=True)

