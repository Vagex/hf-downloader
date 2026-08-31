import React, { useState, useEffect } from 'react';
import { X, Upload, Plus, Trash2, Sparkles, Tag, Film, Image as ImageIcon, MessageSquare, AlertCircle } from 'lucide-react';

export default function PromptModal({ isOpen, onClose, onSave, editingPrompt, onToast }) {
  if (!isOpen) return null;

  const [formData, setFormData] = useState({
    title: '',
    category: 'video', // 'video' | 'image' | 'text'
    subcategory: 'Runway / 可灵 Kling',
    aspectRatio: '9:16',
    duration: '8-10s',
    rating: 5,
    isPinned: false,
    prompt: '',
    negativePrompt: '',
    tags: [],
    variables: [],
    images: [],
    notes: ''
  });

  const [tagInput, setTagInput] = useState('');
  const [imageUrlInput, setImageUrlInput] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (editingPrompt) {
      setFormData({
        title: editingPrompt.title || '',
        category: editingPrompt.category || 'video',
        subcategory: editingPrompt.subcategory || '',
        aspectRatio: editingPrompt.aspectRatio || '',
        duration: editingPrompt.duration || '',
        rating: editingPrompt.rating || 5,
        isPinned: !!editingPrompt.isPinned,
        prompt: editingPrompt.prompt || '',
        negativePrompt: editingPrompt.negativePrompt || '',
        tags: Array.isArray(editingPrompt.tags) ? [...editingPrompt.tags] : [],
        variables: Array.isArray(editingPrompt.variables) ? [...editingPrompt.variables] : [],
        images: Array.isArray(editingPrompt.images) ? [...editingPrompt.images] : [],
        notes: editingPrompt.notes || ''
      });
    } else {
      setFormData({
        title: '',
        category: 'video',
        subcategory: '可灵 Kling / Runway Gen-3',
        aspectRatio: '9:16',
        duration: '8-10s',
        rating: 5,
        isPinned: false,
        prompt: '',
        negativePrompt: '',
        tags: ['一镜到底', '长镜头', '写实摄影'],
        variables: [],
        images: [],
        notes: ''
      });
    }
  }, [editingPrompt]);

  // Auto scan {{var}} in prompt
  const handleAutoScanVariables = () => {
    const matches = [...formData.prompt.matchAll(/\{\{([^}]+)\}\}/g)];
    const uniqueKeys = Array.from(new Set(matches.map(m => m[1].trim())));
    
    if (uniqueKeys.length === 0) {
      if (onToast) onToast('未在提示词中发现 {{变量}} 占位符', 'info');
      return;
    }

    const currentMap = {};
    formData.variables.forEach(v => { currentMap[v.key] = v; });

    const newVars = uniqueKeys.map(key => ({
      key,
      label: currentMap[key]?.label || key,
      defaultValue: currentMap[key]?.defaultValue || ''
    }));

    setFormData({ ...formData, variables: newVars });
    if (onToast) onToast(`已自动提取 ${newVars.length} 个变量`, 'success');
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter' || e.type === 'click') {
      e.preventDefault();
      const val = tagInput.trim().replace(/^#/, '');
      if (val && !formData.tags.includes(val)) {
        setFormData({ ...formData, tags: [...formData.tags, val] });
        setTagInput('');
      }
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData({ ...formData, tags: formData.tags.filter(t => t !== tagToRemove) });
  };

  const handleAddImageUrl = (e) => {
    e.preventDefault();
    if (imageUrlInput.trim()) {
      setFormData({ ...formData, images: [...formData.images, imageUrlInput.trim()] });
      setImageUrlInput('');
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const data = new FormData();
    for (let i = 0; i < files.length; i++) {
      data.append('images', files[i]);
    }

    setUploading(true);
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: data
      });
      const json = await res.json();
      if (json.success && json.urls) {
        setFormData(prev => ({ ...prev, images: [...prev.images, ...json.urls] }));
        if (onToast) onToast(`成功上传 ${json.urls.length} 张图片`, 'success');
      } else {
        throw new Error(json.message || 'Upload failed');
      }
    } catch (err) {
      console.error(err);
      if (onToast) onToast('图片上传失败，请检查网络或后端服务', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveImage = (index) => {
    setFormData({ ...formData, images: formData.images.filter((_, i) => i !== index) });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.prompt.trim()) {
      if (onToast) onToast('请填写标题和提示词正文', 'error');
      return;
    }
    onSave(formData);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col transition-all"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              {formData.category === 'video' ? <Film className="w-5 h-5" /> :
               formData.category === 'image' ? <ImageIcon className="w-5 h-5" /> : <MessageSquare className="w-5 h-5" />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                {editingPrompt ? '编辑提示词' : '收藏/录入新提示词'}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                录入高质量结构化 Prompt，支持多模态参考图与变量槽提取
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form id="prompt-form" onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5 flex-1 text-sm">
          {/* Row 1: Title & Category */}
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-7 space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                提示词标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
                placeholder="例如：飞机舷窗一镜到底长镜头（首尾帧穿梭）"
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
            </div>

            <div className="sm:col-span-5 space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                主类型
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'video', label: 'AI 视频', icon: Film },
                  { key: 'image', label: 'AI 生图', icon: ImageIcon },
                  { key: 'text', label: '大模型/文本', icon: MessageSquare }
                ].map(c => {
                  const Icon = c.icon;
                  return (
                    <button
                      type="button"
                      key={c.key}
                      onClick={() => setFormData({ ...formData, category: c.key })}
                      className={`flex items-center justify-center gap-1.5 py-2.5 px-2 rounded-xl text-xs font-medium border transition ${
                        formData.category === c.key
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {c.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Row 2: Subcategory/Model, Aspect Ratio, Duration */}
          <div className="space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
              <div className="sm:col-span-6 space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    适配模型 / 引擎
                  </label>
                  <span className="text-[11px] text-blue-600 dark:text-blue-400">点击下方快捷选择</span>
                </div>
                <input
                  type="text"
                  value={formData.subcategory}
                  onChange={e => setFormData({ ...formData, subcategory: e.target.value })}
                  placeholder="如：LTX 2.5 / Minimax h3 / 可灵 Kling"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white text-xs font-medium"
                />
              </div>
              <div className="sm:col-span-3 space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  画幅比例 (Aspect Ratio)
                </label>
                <input
                  type="text"
                  value={formData.aspectRatio}
                  onChange={e => setFormData({ ...formData, aspectRatio: e.target.value })}
                  placeholder="如：9:16 / 16:9 / 1:1"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white text-xs"
                />
              </div>
              <div className="sm:col-span-3 space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  时长 / 参数
                </label>
                <input
                  type="text"
                  value={formData.duration}
                  onChange={e => setFormData({ ...formData, duration: e.target.value })}
                  placeholder="如：8-10s / 5s 慢动作"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white text-xs"
                />
              </div>
            </div>

            {/* Quick Model Selector Pills */}
            <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/60 dark:border-slate-800 space-y-2">
              {/* Primary Models */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400 mr-1 flex items-center gap-0.5">
                  ⭐ 主力引擎:
                </span>
                {[
                  { name: 'LTX 2.5', label: 'LTX 2.5 (Lightricks)' },
                  { name: 'Minimax h3', label: 'Minimax h3 (海螺视频)' },
                  { name: '可灵 Kling 1.5/2.0', label: '可灵 Kling' },
                  { name: 'Runway Gen-3', label: 'Runway Gen-3' },
                  { name: 'FLUX.1', label: 'FLUX.1' },
                  { name: 'Midjourney v6.1', label: 'Midjourney v6.1' }
                ].map(m => (
                  <button
                    type="button"
                    key={m.name}
                    onClick={() => setFormData({ ...formData, subcategory: m.name })}
                    className={`px-2.5 py-1 text-xs rounded-lg font-medium transition ${
                      formData.subcategory === m.name
                        ? 'bg-blue-600 text-white shadow-xs font-semibold'
                        : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:border-blue-400 hover:text-blue-600'
                    }`}
                  >
                    {m.name}
                  </button>
                ))}
              </div>

              {/* Secondary / Other Models */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1.5 border-t border-slate-200/50 dark:border-slate-800">
                <span className="text-[11px] font-medium text-slate-400 mr-1">
                  备选/其他:
                </span>
                {[
                  'Sora', 'Luma Dream Machine', 'Vidu', 'Hunyuan Video (混元)', 'WanX (通义万相)', 'Claude 3.7 / GPT-4o'
                ].map(m => (
                  <button
                    type="button"
                    key={m}
                    onClick={() => setFormData({ ...formData, subcategory: m })}
                    className={`px-2 py-0.5 text-[11px] rounded-md transition ${
                      formData.subcategory === m
                        ? 'bg-blue-500 text-white font-medium'
                        : 'bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Row 3: Prompt Text (with Scan Variables action) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                提示词正文 (支持使用 {`{{变量名}}`} 定义可变槽) <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={handleAutoScanVariables}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium"
              >
                <Sparkles className="w-3.5 h-3.5" />
                自动识别并提取变量
              </button>
            </div>
            <textarea
              required
              rows={6}
              value={formData.prompt}
              onChange={e => setFormData({ ...formData, prompt: e.target.value })}
              placeholder="输入完整的 Prompt 内容，例如：从首帧开始：坐在飞机座位上向外看椭圆形舷窗... 准确落在尾帧：双手拿着登机牌，上面写着 FLIGHT {{flight_no}}..."
              className="w-full p-3.5 font-mono text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white leading-relaxed"
            />
          </div>

          {/* Row 4: Negative Prompt */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              负向提示词 (Negative Prompt / 约束词)
            </label>
            <input
              type="text"
              value={formData.negativePrompt}
              onChange={e => setFormData({ ...formData, negativePrompt: e.target.value })}
              placeholder="如：不要跳切，不要文字变形，不要额外字幕，不要突然出现别人的大脸"
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
            />
          </div>

          {/* Row 5: Tags */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              分类标签 (按回车添加)
            </label>
            <div className="flex flex-wrap items-center gap-2 p-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl min-h-[46px]">
              {formData.tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium rounded-lg shadow-sm border border-slate-200 dark:border-slate-600"
                >
                  <Tag className="w-3 h-3 text-blue-500" />
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="text-slate-400 hover:text-red-500 transition"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <input
                type="text"
                value={tagInput}
                onChange={e => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                placeholder="输入标签按回车 (如: 一镜到底, 首尾帧, 4K)..."
                className="flex-1 min-w-[180px] bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none px-2 py-1 placeholder-slate-400"
              />
            </div>
          </div>

          {/* Row 6: Reference Images & Videos / Uploads */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                多媒体资产（支持生成视频 .mp4/.webm、首尾帧参考图）
              </label>
              <span className="text-[11px] text-slate-400">单文件最高支持 200MB</span>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {formData.images.map((mediaUrl, idx) => {
                const isVid = mediaUrl.endsWith('.mp4') || mediaUrl.endsWith('.webm') || mediaUrl.endsWith('.mov') || mediaUrl.includes('/uploads/video-');
                return (
                  <div key={idx} className="relative group rounded-xl overflow-hidden aspect-video bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    {isVid ? (
                      <>
                        <video src={mediaUrl} className="w-full h-full object-cover" muted />
                        <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/70 text-white text-[9px] font-bold flex items-center gap-1">
                          <Film className="w-2.5 h-2.5 text-blue-400" />
                          视频
                        </div>
                      </>
                    ) : (
                      <img src={mediaUrl} alt="Reference" className="w-full h-full object-cover" />
                    )}
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(idx)}
                      className="absolute top-1.5 right-1.5 p-1 bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition shadow"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}

              <label className="border-2 border-dashed border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-500 rounded-xl aspect-video flex flex-col items-center justify-center cursor-pointer p-2 transition bg-slate-50/50 dark:bg-slate-800/20 text-slate-500 dark:text-slate-400 hover:text-blue-500">
                <Upload className="w-5 h-5 mb-1" />
                <span className="text-[11px] font-medium text-center">
                  {uploading ? '上传中...' : '上传视频 / 图片'}
                </span>
                <span className="text-[9px] text-slate-400">MP4 / WebM / PNG / JPG</span>
                <input
                  type="file"
                  multiple
                  accept="image/*,video/*"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploading}
                />
              </label>
            </div>

            <div className="flex items-center gap-2 mt-2">
              <input
                type="text"
                value={imageUrlInput}
                onChange={e => setImageUrlInput(e.target.value)}
                placeholder="或粘贴网络图片 / 视频 URL (如: https://.../sample.mp4)..."
                className="flex-1 px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
              <button
                type="button"
                onClick={handleAddImageUrl}
                className="px-3 py-2 text-xs font-medium bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 rounded-xl text-slate-700 dark:text-slate-200 transition"
              >
                添加媒体 URL
              </button>
            </div>
          </div>

          {/* Row 7: Notes & Pin */}
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-9 space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                心得与生成技巧备注
              </label>
              <input
                type="text"
                value={formData.notes}
                onChange={e => setFormData({ ...formData, notes: e.target.value })}
                placeholder="例如：可灵 1.5 首尾帧效果最好，建议首帧调低运镜幅度，尾帧文字要清晰..."
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
            </div>
            <div className="sm:col-span-3 flex items-end">
              <label className="flex items-center gap-2 p-2.5 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 cursor-pointer w-full">
                <input
                  type="checkbox"
                  checked={formData.isPinned}
                  onChange={e => setFormData({ ...formData, isPinned: e.target.checked })}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  设为精选置顶 ⭐
                </span>
              </label>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl transition"
          >
            取消
          </button>
          <button
            type="submit"
            form="prompt-form"
            className="px-6 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg shadow-blue-500/25 transition active:scale-95"
          >
            保存到收藏库
          </button>
        </div>
      </div>
    </div>
  );
}
