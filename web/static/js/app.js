/**
 * 精灵表转 GIF - 前端交互逻辑
 */

// 预设模板数据
const TEMPLATES = {
    'weapon-attack': {
        name: '武器战斗',
        grid: { rows: 6, cols: 6 },
        prompt: `参考原图的人物生成一张正方形像素图(图片中不要有序号），6×6共36格，从左上到右下就是GIF播放顺序。

动作是角色一次夸张霸气的完整武器攻击：
1-4格：静止准备姿势
5-10格：蓄力（下蹲、拉武器）
11-17格：向前猛冲
18-25格：原地全力挥击
26-31格：高高跳起→空中下劈重击
32-35格：落地收招
36格：准备回到第1格，以实现无缝循环

动作要夸张有冲击力，身体大扭转，武器大摆幅，全程加武器轨迹、光效、冲击波，特效别遮住角色。
每格里角色、武器、特效一个像素都不许出界。
动作流畅，每一格都接上一格。每一格都必须拿着武器。
像素风，线条干净，颜色鲜艳，白色背景，直接输出完整的36格大图。`
    },
    'elegant-exit': {
        name: '优雅下车',
        grid: { rows: 6, cols: 6 },
        prompt: `参考原图的人物生成一张正方形像素图(图片中不要有序号），6×6共36格，从左上到右下就是GIF播放顺序。

动作是角色优雅从豪车下车的完整过程：
1-6格：车门缓缓打开
7-12格：伸出一只脚，优雅落地
13-18格：身体转出，手扶车门
19-24格：站直身体，整理衣服
25-30格：甩头撩发/调整领带
31-35格：自信微笑，气场全开
36格：回到准备姿态，实现无缝循环

动作要优雅有气质，姿态从容不迫。
每格里角色一个像素都不许出界。
动作流畅，每一格都接上一格。
像素风，线条干净，颜色鲜艳，白色背景，直接输出完整的36格大图。`
    },
    'martial-arts': {
        name: '武术连招',
        grid: { rows: 6, cols: 6 },
        prompt: `参考原图的人物生成一张正方形像素图(图片中不要有序号），6×6共36格，从左上到右下就是GIF播放顺序。

动作是角色一套行云流水的武术连招：
1-4格：抱拳起势
5-10格：连续三拳（左右左）
11-16格：旋风腿扫踢
17-22格：飞身侧踢
23-28格：落地接后空翻
29-34格：双掌推出气功波
35-36格：收势抱拳，回到起始

动作要刚柔并济，拳拳到肉，腿法凌厉。全程加拳风、脚风特效。
每格里角色、特效一个像素都不许出界。
动作流畅，每一格都接上一格。
像素风，线条干净，颜色鲜艳，白色背景，直接输出完整的36格大图。`
    },
    'magic-spell': {
        name: '魔法释放',
        grid: { rows: 6, cols: 6 },
        prompt: `参考原图的人物生成一张正方形像素图(图片中不要有序号），6×6共36格，从左上到右下就是GIF播放顺序。

动作是角色释放强大魔法的完整过程：
1-6格：双手合十聚气，魔法阵在脚下浮现
7-12格：能量球在双手间逐渐成形、增大
13-18格：将能量举过头顶，光芒四射
19-24格：猛然向前推出，魔法激射而出
25-30格：能量冲击波扩散，特效炸裂
31-35格：收回双手，魔力余韵消散
36格：回到平静站姿，准备下一次施法

全程魔法光效华丽，颜色渐变流动。
每格里角色、魔法特效一个像素都不许出界。
动作流畅，每一格都接上一格。
像素风，线条干净，颜色鲜艳，白色背景，直接输出完整的36格大图。`
    },
    'parkour': {
        name: '跑酷跳跃',
        grid: { rows: 6, cols: 6 },
        prompt: `参考原图的人物生成一张正方形像素图(图片中不要有序号），6×6共36格，从左上到右下就是GIF播放顺序。

动作是角色一段帅气的跑酷动作：
1-6格：快速助跑，身体前倾
7-12格：单脚蹬地起跳
13-18格：空中前滚翻
19-24格：展开身体，空中滑翔姿态
25-30格：落地翻滚缓冲
31-35格：起身继续跑动
36格：回到跑步姿态，实现无缝循环

动作要有速度感和力量感，加运动残影特效。
每格里角色、特效一个像素都不许出界。
动作流畅，每一格都接上一格。
像素风，线条干净，颜色鲜艳，白色背景，直接输出完整的36格大图。`
    }
};

class SpriteToGif {
    constructor() {
        this.fileId = null;
        this.currentStep = 1;
        this.imageData = null;  // 存储原图数据用于预览
        this.imageSize = { width: 0, height: 0 };
        this.currentTemplate = 'weapon-attack';  // 当前选中的模板
        this.isCustomPrompt = false;  // 是否是自定义提示词
        this.referenceImageData = null;  // 参考图数据
        this.initElements();
        this.bindEvents();
        this.initTemplates();
    }

    initElements() {
        // 区域
        this.uploadSection = document.getElementById('upload-section');
        this.configSection = document.getElementById('config-section');
        this.resultSection = document.getElementById('result-section');
        
        // Tab 切换
        this.sourceTabs = document.querySelectorAll('.source-tab');
        this.aiGeneratePanel = document.getElementById('ai-generate-panel');
        this.manualUploadPanel = document.getElementById('manual-upload-panel');
        
        // AI 生成相关
        this.templateGrid = document.getElementById('template-grid');
        this.templateCards = document.querySelectorAll('.template-card');
        this.referenceUpload = document.getElementById('reference-upload');
        this.referencePlaceholder = document.getElementById('reference-placeholder');
        this.referencePreview = document.getElementById('reference-preview');
        this.referenceImage = document.getElementById('reference-image');
        this.referenceInput = document.getElementById('reference-input');
        this.refRemoveBtn = document.getElementById('ref-remove');
        this.promptInput = document.getElementById('prompt-input');
        this.templateBadge = document.getElementById('template-badge');
        this.generateBtn = document.getElementById('generate-btn');
        
        // 上传相关
        this.uploadZone = document.getElementById('upload-zone');
        this.fileInput = document.getElementById('file-input');
        this.previewContainer = document.getElementById('preview-container');
        this.previewImage = document.getElementById('preview-image');
        this.previewBadge = document.getElementById('preview-badge');
        
        // 网格预览
        this.gridPreviewCanvas = document.getElementById('grid-preview-canvas');
        this.firstFrameCanvas = document.getElementById('first-frame-canvas');
        this.showNumbersCheckbox = document.getElementById('show-numbers');
        this.previewCellSize = document.getElementById('preview-cell-size');
        this.previewTotalFrames = document.getElementById('preview-total-frames');
        
        // 原图 Image 对象
        this.originalImage = null;
        
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
        // Tab 切换
        this.sourceTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        
        // 模板卡片点击
        if (this.templateGrid) {
            this.templateGrid.addEventListener('click', (e) => {
                const card = e.target.closest('.template-card');
                if (card) {
                    this.selectTemplate(card.dataset.template);
                }
            });
        }
        
        // 参考图上传
        if (this.referenceUpload) {
            this.referenceUpload.addEventListener('click', (e) => {
                if (e.target === this.refRemoveBtn || e.target.closest('#ref-remove')) return;
                if (e.target !== this.referenceInput) {
                    this.referenceInput.click();
                }
            });
            
            this.referenceInput.addEventListener('change', (e) => this.handleReferenceSelect(e));
            
            // 拖放参考图
            this.referenceUpload.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.referenceUpload.classList.add('dragover');
            });
            
            this.referenceUpload.addEventListener('dragleave', () => {
                this.referenceUpload.classList.remove('dragover');
            });
            
            this.referenceUpload.addEventListener('drop', (e) => {
                e.preventDefault();
                this.referenceUpload.classList.remove('dragover');
                const file = e.dataTransfer.files[0];
                if (file && file.type.startsWith('image/')) {
                    this.loadReferenceImage(file);
                }
            });
        }
        
        // 移除参考图
        if (this.refRemoveBtn) {
            this.refRemoveBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeReferenceImage();
            });
        }
        
        // 提示词输入监听
        if (this.promptInput) {
            this.promptInput.addEventListener('input', () => {
                // 检查是否修改了模板提示词
                const currentTemplate = TEMPLATES[this.currentTemplate];
                if (currentTemplate && this.promptInput.value.trim() !== currentTemplate.prompt.trim()) {
                    this.isCustomPrompt = true;
                    this.templateBadge.textContent = '自定义';
                    this.templateCards.forEach(card => card.classList.remove('active'));
                }
            });
        }
        
        // 生成按钮
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateSprite());
        }
        
        // 检查元素是否存在
        if (this.uploadZone && this.fileInput) {
            // 上传区域点击
            this.uploadZone.addEventListener('click', (e) => {
                // 如果点击的是 input 本身，不要重复触发
                if (e.target === this.fileInput) return;
                e.stopPropagation();
                this.fileInput.click();
            });
            
            // 触摸反馈
            this.uploadZone.addEventListener('touchstart', () => {
                this.uploadZone.classList.add('dragover');
            }, { passive: true });
            
            this.uploadZone.addEventListener('touchend', (e) => {
                this.uploadZone.classList.remove('dragover');
                // 触摸结束时触发文件选择
                if (e.target !== this.fileInput) {
                    this.fileInput.click();
                }
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
        }
        
        // 转换按钮
        this.convertBtn.addEventListener('click', () => this.convert());
        
        // 重新开始
        this.restartBtn.addEventListener('click', () => this.restart());
        
        // 实时预览：监听参数变化
        this.rowsInput.addEventListener('input', () => this.updateGridPreview());
        this.colsInput.addEventListener('input', () => this.updateGridPreview());
        this.marginInput.addEventListener('input', () => this.updateGridPreview());
        
        // 显示/隐藏编号
        if (this.showNumbersCheckbox) {
            this.showNumbersCheckbox.addEventListener('change', () => this.updateGridPreview());
        }
        
        // 快速预设按钮
        const presetButtons = document.getElementById('preset-buttons');
        if (presetButtons) {
            presetButtons.addEventListener('click', (e) => {
                const btn = e.target.closest('.preset-btn');
                if (btn) {
                    const rows = parseInt(btn.dataset.rows);
                    const cols = parseInt(btn.dataset.cols);
                    this.rowsInput.value = rows;
                    this.colsInput.value = cols;
                    this.updateGridPreview();
                    
                    // 高亮当前选中的按钮
                    presetButtons.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
            });
        }
        
        // 加减调整按钮
        document.querySelectorAll('.adj-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = document.getElementById(btn.dataset.target);
                const delta = parseInt(btn.dataset.delta);
                if (target) {
                    const newVal = Math.max(1, Math.min(50, parseInt(target.value) + delta));
                    target.value = newVal;
                    this.updateGridPreview();
                }
            });
        });
        
        // 阻止双击缩放（移动端）
        document.addEventListener('dblclick', (e) => {
            e.preventDefault();
        }, { passive: false });
    }
    
    // 初始化模板
    initTemplates() {
        // 默认选中第一个模板
        this.selectTemplate('weapon-attack');
    }
    
    // Tab 切换
    switchTab(tabId) {
        this.sourceTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabId);
        });
        
        if (tabId === 'ai-generate') {
            this.aiGeneratePanel.classList.add('active');
            this.manualUploadPanel.classList.remove('active');
        } else {
            this.aiGeneratePanel.classList.remove('active');
            this.manualUploadPanel.classList.add('active');
        }
    }
    
    // 选择模板
    selectTemplate(templateId) {
        const template = TEMPLATES[templateId];
        if (!template) return;
        
        this.currentTemplate = templateId;
        this.isCustomPrompt = false;
        
        // 更新 UI
        this.templateCards.forEach(card => {
            card.classList.toggle('active', card.dataset.template === templateId);
        });
        
        this.promptInput.value = template.prompt;
        this.templateBadge.textContent = template.name;
    }
    
    // 处理参考图选择
    handleReferenceSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.loadReferenceImage(file);
        }
    }
    
    // 加载参考图
    loadReferenceImage(file) {
        if (!file.type.startsWith('image/')) {
            this.showToast('请选择图片文件', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.referenceImageData = e.target.result;
            this.referenceImage.src = this.referenceImageData;
            this.referencePlaceholder.classList.add('hidden');
            this.referencePreview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
    
    // 移除参考图
    removeReferenceImage() {
        this.referenceImageData = null;
        this.referenceInput.value = '';
        this.referencePlaceholder.classList.remove('hidden');
        this.referencePreview.classList.add('hidden');
    }
    
    // AI 生成精灵表
    async generateSprite() {
        const prompt = this.promptInput.value.trim();
        if (!prompt) {
            this.showToast('请输入提示词', 'error');
            return;
        }
        
        this.showLoading('AI 正在生成精灵表...\n这可能需要 30-60 秒');
        
        try {
            const requestBody = {
                prompt: prompt
            };
            
            // 如果有参考图，添加到请求
            if (this.referenceImageData) {
                requestBody.reference_image = this.referenceImageData;
            }
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.fileId = data.file_id;
                this.imageData = data.image_data;
                this.imageSize = {
                    width: data.analysis.image_size[0],
                    height: data.analysis.image_size[1]
                };
                
                // 显示预览
                this.previewImage.src = this.imageData;
                this.previewContainer.classList.remove('hidden');
                this.previewBadge.textContent = 'AI 生成';
                this.infoFilename.textContent = this.isCustomPrompt ? '自定义' : TEMPLATES[this.currentTemplate]?.name || 'AI 生成';
                
                this.showAnalysisResult(data.analysis);
                this.goToStep(2);
                this.showToast('精灵表生成成功！', 'success');
            } else {
                this.showToast(data.error || '生成失败', 'error');
            }
        } catch (error) {
            console.error('生成失败:', error);
            this.showToast('生成失败，请重试', 'error');
        } finally {
            this.hideLoading();
        }
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
        
        // 读取图片并显示预览
        const reader = new FileReader();
        reader.onload = (e) => {
            this.imageData = e.target.result;
            this.previewImage.src = this.imageData;
            this.previewContainer.classList.remove('hidden');
            this.infoFilename.textContent = file.name;
            
            // 获取图片尺寸
            const img = new Image();
            img.onload = () => {
                this.imageSize = { width: img.width, height: img.height };
            };
            img.src = this.imageData;
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
                this.imageSize = {
                    width: data.analysis.image_size[0],
                    height: data.analysis.image_size[1]
                };
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
        
        // 加载原图用于网格预览
        if (this.imageData) {
            this.originalImage = new Image();
            this.originalImage.onload = () => {
                this.updateGridPreview();
            };
            this.originalImage.src = this.imageData;
        }
    }

    updateGridPreview() {
        const canvas = this.gridPreviewCanvas;
        const img = this.originalImage;
        
        if (!canvas || !img || !img.complete) return;
        
        const rows = parseInt(this.rowsInput.value) || 1;
        const cols = parseInt(this.colsInput.value) || 1;
        const margin = parseInt(this.marginInput.value) || 0;
        const showNumbers = this.showNumbersCheckbox ? this.showNumbersCheckbox.checked : true;
        
        // 计算显示尺寸（保持原图比例）
        const maxWidth = 480;
        const maxHeight = 350;
        const imgRatio = img.width / img.height;
        
        let displayWidth, displayHeight;
        if (imgRatio > maxWidth / maxHeight) {
            displayWidth = Math.min(maxWidth, img.width);
            displayHeight = displayWidth / imgRatio;
        } else {
            displayHeight = Math.min(maxHeight, img.height);
            displayWidth = displayHeight * imgRatio;
        }
        
        canvas.width = displayWidth;
        canvas.height = displayHeight;
        
        const ctx = canvas.getContext('2d');
        
        // 绘制原图
        ctx.drawImage(img, 0, 0, displayWidth, displayHeight);
        
        const cellWidth = displayWidth / cols;
        const cellHeight = displayHeight / rows;
        
        // 绘制边距预览（橙色区域表示会被裁掉的部分）
        if (margin > 0) {
            const scaleX = displayWidth / img.width;
            const scaleY = displayHeight / img.height;
            const marginX = margin * scaleX;
            const marginY = margin * scaleY;
            
            ctx.fillStyle = 'rgba(255, 100, 50, 0.35)';
            
            for (let row = 0; row < rows; row++) {
                for (let col = 0; col < cols; col++) {
                    const cellX = col * cellWidth;
                    const cellY = row * cellHeight;
                    
                    // 上边距
                    ctx.fillRect(cellX, cellY, cellWidth, marginY);
                    // 下边距
                    ctx.fillRect(cellX, cellY + cellHeight - marginY, cellWidth, marginY);
                    // 左边距
                    ctx.fillRect(cellX, cellY + marginY, marginX, cellHeight - marginY * 2);
                    // 右边距
                    ctx.fillRect(cellX + cellWidth - marginX, cellY + marginY, marginX, cellHeight - marginY * 2);
                }
            }
        }
        
        // 绘制网格线
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.9)';
        ctx.lineWidth = 2;
        
        // 垂直线
        for (let i = 1; i < cols; i++) {
            const x = Math.round(i * cellWidth);
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, displayHeight);
            ctx.stroke();
        }
        
        // 水平线
        for (let i = 1; i < rows; i++) {
            const y = Math.round(i * cellHeight);
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(displayWidth, y);
            ctx.stroke();
        }
        
        // 绘制外框
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.5)';
        ctx.lineWidth = 2;
        ctx.strokeRect(1, 1, displayWidth - 2, displayHeight - 2);
        
        // 绘制帧编号（左上角小标签样式）
        if (showNumbers) {
            const fontSize = Math.max(10, Math.min(14, Math.min(cellWidth, cellHeight) / 5));
            ctx.font = `bold ${fontSize}px monospace`;
            
            let frameNum = 1;
            for (let row = 0; row < rows; row++) {
                for (let col = 0; col < cols; col++) {
                    const x = col * cellWidth + 3;
                    const y = row * cellHeight + 3;
                    
                    const text = frameNum.toString();
                    const textWidth = ctx.measureText(text).width;
                    
                    // 绘制背景标签（圆角矩形）
                    ctx.fillStyle = 'rgba(0, 240, 255, 0.9)';
                    const w = textWidth + 6;
                    const h = fontSize + 4;
                    const r = 2;
                    ctx.beginPath();
                    ctx.moveTo(x + r, y);
                    ctx.lineTo(x + w - r, y);
                    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
                    ctx.lineTo(x + w, y + h - r);
                    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
                    ctx.lineTo(x + r, y + h);
                    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
                    ctx.lineTo(x, y + r);
                    ctx.quadraticCurveTo(x, y, x + r, y);
                    ctx.closePath();
                    ctx.fill();
                    
                    // 绘制文字
                    ctx.fillStyle = '#0a0a0f';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'top';
                    ctx.fillText(text, x + 3, y + 2);
                    
                    frameNum++;
                }
            }
        }
        
        // 更新统计信息
        const realCellWidth = Math.round(img.width / cols);
        const realCellHeight = Math.round(img.height / rows);
        const totalFrames = rows * cols;
        
        if (this.previewCellSize) {
            this.previewCellSize.textContent = `单帧尺寸: ${realCellWidth} × ${realCellHeight}`;
        }
        if (this.previewTotalFrames) {
            this.previewTotalFrames.textContent = `总帧数: ${totalFrames}`;
        }
        
        // 高亮匹配的预设按钮
        const presetButtons = document.getElementById('preset-buttons');
        if (presetButtons) {
            presetButtons.querySelectorAll('.preset-btn').forEach(btn => {
                const btnRows = parseInt(btn.dataset.rows);
                const btnCols = parseInt(btn.dataset.cols);
                if (btnRows === rows && btnCols === cols) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }
        
        // 更新第一帧预览
        this.updateFirstFramePreview(rows, cols, margin);
    }
    
    updateFirstFramePreview(rows, cols, margin) {
        const canvas = this.firstFrameCanvas;
        const img = this.originalImage;
        
        if (!canvas || !img || !img.complete) return;
        
        // 计算第一帧的位置和尺寸
        const cellWidth = img.width / cols;
        const cellHeight = img.height / rows;
        
        const srcX = margin;
        const srcY = margin;
        const srcW = cellWidth - margin * 2;
        const srcH = cellHeight - margin * 2;
        
        if (srcW <= 0 || srcH <= 0) {
            // 边距太大，无法显示
            canvas.width = 100;
            canvas.height = 100;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, 100, 100);
            ctx.fillStyle = '#ff6666';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('边距过大', 50, 50);
            return;
        }
        
        // 计算显示尺寸（限制最大尺寸）
        const maxSize = 120;
        const ratio = srcW / srcH;
        let displayWidth, displayHeight;
        
        if (ratio > 1) {
            displayWidth = Math.min(maxSize, srcW);
            displayHeight = displayWidth / ratio;
        } else {
            displayHeight = Math.min(maxSize, srcH);
            displayWidth = displayHeight * ratio;
        }
        
        canvas.width = displayWidth;
        canvas.height = displayHeight;
        
        const ctx = canvas.getContext('2d');
        
        // 绘制第一帧
        ctx.drawImage(
            img,
            srcX, srcY, srcW, srcH,  // 源图裁剪区域
            0, 0, displayWidth, displayHeight  // 目标绘制区域
        );
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
        this.currentGifId = data.gif_id;
        
        this.resultGif.src = previewUrl;
        
        // 移除旧的事件监听器，添加新的
        const newDownloadBtn = this.downloadBtn.cloneNode(true);
        this.downloadBtn.parentNode.replaceChild(newDownloadBtn, this.downloadBtn);
        this.downloadBtn = newDownloadBtn;
        
        // 使用点击事件处理下载（兼容移动端）
        this.downloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.downloadGif(data.gif_id);
        });
    }
    
    async downloadGif(gifId) {
        try {
            this.showLoading('准备下载...');
            
            const response = await fetch(`/api/download/${gifId}`);
            if (!response.ok) {
                throw new Error('下载失败');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // 创建临时链接触发下载
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'sprite_animation.gif';
            document.body.appendChild(a);
            
            // iOS Safari 特殊处理
            if (this.isIOS()) {
                // iOS 上直接打开新窗口显示图片
                window.open(url, '_blank');
                this.showToast('长按图片可保存到相册');
            } else {
                a.click();
            }
            
            // 清理
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 100);
            
        } catch (error) {
            console.error('下载失败:', error);
            this.showError('下载失败，请重试');
        } finally {
            this.hideLoading();
        }
    }
    
    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }
    
    showToast(message) {
        // 创建 toast 提示
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 240, 255, 0.9);
            color: #0a0a0f;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            animation: fadeInUp 0.3s ease;
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
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
        this.imageData = null;
        this.originalImage = null;
        if (this.fileInput) this.fileInput.value = '';
        this.previewContainer.classList.add('hidden');
        this.previewImage.src = '';
        
        // 重置 AI 生成状态
        this.removeReferenceImage();
        this.selectTemplate('weapon-attack');
        
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
