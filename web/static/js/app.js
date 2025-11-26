/**
 * 精灵表转 GIF - 前端交互逻辑
 */

class SpriteToGif {
    constructor() {
        this.fileId = null;
        this.currentStep = 1;
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        // 区域
        this.uploadSection = document.getElementById('upload-section');
        this.configSection = document.getElementById('config-section');
        this.resultSection = document.getElementById('result-section');
        
        // 上传相关
        this.uploadZone = document.getElementById('upload-zone');
        this.fileInput = document.getElementById('file-input');
        this.previewContainer = document.getElementById('preview-container');
        this.previewImage = document.getElementById('preview-image');
        
        // 信息显示
        this.infoSize = document.getElementById('info-size');
        this.infoFilename = document.getElementById('info-filename');
        this.confidenceBadge = document.getElementById('confidence-badge');
        this.detectedGrid = document.getElementById('detected-grid');
        this.detectedFrames = document.getElementById('detected-frames');
        this.detectedLinewidth = document.getElementById('detected-linewidth');
        
        // 表单输入
        this.rowsInput = document.getElementById('rows');
        this.colsInput = document.getElementById('cols');
        this.marginInput = document.getElementById('margin');
        this.durationInput = document.getElementById('duration');
        
        // 按钮
        this.convertBtn = document.getElementById('convert-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.restartBtn = document.getElementById('restart-btn');
        
        // 结果
        this.resultGif = document.getElementById('result-gif');
        
        // 加载状态
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        
        // 步骤指示器
        this.steps = document.querySelectorAll('.step');
    }

    bindEvents() {
        // 上传区域点击（支持触摸）
        this.uploadZone.addEventListener('click', (e) => {
            e.preventDefault();
            this.fileInput.click();
        });
        
        // 触摸反馈
        this.uploadZone.addEventListener('touchstart', () => {
            this.uploadZone.classList.add('dragover');
        }, { passive: true });
        
        this.uploadZone.addEventListener('touchend', () => {
            this.uploadZone.classList.remove('dragover');
        }, { passive: true });
        
        // 文件选择
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // 拖放（桌面端）
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('dragover');
        });
        
        this.uploadZone.addEventListener('dragleave', () => {
            this.uploadZone.classList.remove('dragover');
        });
        
        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) this.processFile(file);
        });
        
        // 转换按钮
        this.convertBtn.addEventListener('click', () => this.convert());
        
        // 重新开始
        this.restartBtn.addEventListener('click', () => this.restart());
        
        // 阻止双击缩放（移动端）
        document.addEventListener('dblclick', (e) => {
            e.preventDefault();
        }, { passive: false });
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) this.processFile(file);
    }

    async processFile(file) {
        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            this.showError('请选择图片文件');
            return;
        }
        
        // 显示预览
        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewImage.src = e.target.result;
            this.previewContainer.classList.remove('hidden');
            this.infoFilename.textContent = file.name;
        };
        reader.readAsDataURL(file);
        
        // 上传并分析
        this.showLoading('正在智能分析...');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.fileId = data.file_id;
                this.showAnalysisResult(data.analysis);
                this.goToStep(2);
            } else {
                this.showError(data.error || '分析失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
            console.error(error);
        } finally {
            this.hideLoading();
        }
    }

    showAnalysisResult(analysis) {
        // 更新尺寸信息
        this.infoSize.textContent = `${analysis.image_size[0]} × ${analysis.image_size[1]}`;
        
        // 更新检测结果
        this.detectedGrid.textContent = `${analysis.rows} × ${analysis.cols}`;
        this.detectedFrames.textContent = analysis.total_frames;
        this.detectedLinewidth.textContent = `${analysis.line_width} px`;
        
        // 更新置信度
        const confidence = Math.round(analysis.confidence * 100);
        this.confidenceBadge.querySelector('.confidence-value').textContent = confidence;
        
        // 根据置信度调整样式
        const badge = this.confidenceBadge;
        if (confidence >= 80) {
            badge.style.background = 'linear-gradient(135deg, #00f0ff 0%, #7b2cff 100%)';
        } else if (confidence >= 50) {
            badge.style.background = 'linear-gradient(135deg, #ffc832 0%, #ff8c00 100%)';
        } else {
            badge.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%)';
        }
        
        // 显示/隐藏低置信度提示
        const tipBox = document.getElementById('low-confidence-tip');
        if (tipBox) {
            if (confidence < 70) {
                tipBox.classList.remove('hidden');
            } else {
                tipBox.classList.add('hidden');
            }
        }
        
        // 填充表单
        this.rowsInput.value = analysis.rows;
        this.colsInput.value = analysis.cols;
        this.marginInput.value = analysis.margin;
    }

    async convert() {
        if (!this.fileId) {
            this.showError('请先上传图片');
            return;
        }
        
        this.showLoading('正在生成 GIF...');
        
        const params = {
            file_id: this.fileId,
            rows: parseInt(this.rowsInput.value),
            cols: parseInt(this.colsInput.value),
            margin: parseInt(this.marginInput.value),
            duration: parseInt(this.durationInput.value)
        };
        
        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showResult(data);
                this.goToStep(3);
            } else {
                this.showError(data.error || '转换失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
            console.error(error);
        } finally {
            this.hideLoading();
        }
    }

    showResult(data) {
        const previewUrl = `/api/preview/${data.gif_id}`;
        const downloadUrl = `/api/download/${data.gif_id}`;
        
        this.resultGif.src = previewUrl;
        this.downloadBtn.href = downloadUrl;
    }

    goToStep(step) {
        this.currentStep = step;
        
        // 更新步骤指示器
        this.steps.forEach((el, index) => {
            if (index + 1 <= step) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
        
        // 切换区域
        this.uploadSection.classList.remove('active');
        this.configSection.classList.remove('active');
        this.resultSection.classList.remove('active');
        
        switch (step) {
            case 1:
                this.uploadSection.classList.add('active');
                break;
            case 2:
                this.configSection.classList.add('active');
                break;
            case 3:
                this.resultSection.classList.add('active');
                break;
        }
    }

    restart() {
        // 重置状态
        this.fileId = null;
        this.fileInput.value = '';
        this.previewContainer.classList.add('hidden');
        this.previewImage.src = '';
        
        // 回到第一步
        this.goToStep(1);
    }

    showLoading(text = '处理中...') {
        this.loadingText.textContent = text;
        this.loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    }

    showError(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type = 'info') {
        // 移除已存在的 toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="toast-message">${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // 触发动画
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // 自动消失
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new SpriteToGif();
});

