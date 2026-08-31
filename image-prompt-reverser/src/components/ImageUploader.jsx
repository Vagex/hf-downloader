import React, { useRef, useState, useEffect } from 'react';
import { UploadCloud, Image as ImageIcon, X, Palette, Crop, RefreshCw, Sparkles } from 'lucide-react';
import { extractImageInfo } from '../services/colorExtractor';

export default function ImageUploader({
  imageSrc,
  imageInfo,
  onImageLoaded,
  onClearImage,
  onLoadSample,
  selectedCategoryId
}) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(false);

  // Global paste listener for Ctrl+V
  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const blob = items[i].getAsFile();
          processFile(blob);
          break;
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, []);

  const processFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('请上传有效的图片文件 (JPG, PNG, WebP, SVG)');
      return;
    }

    setLoadingInfo(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target.result;
      const info = await extractImageInfo(dataUrl);
      onImageLoaded(dataUrl, info);
      setLoadingInfo(false);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-brand-500"></span>
          步骤 2 · 上传待反推图片
        </label>
        <button
          onClick={onLoadSample}
          className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition"
        >
          <Sparkles className="w-3 h-3" />
          <span>一键加载当前类别示范图</span>
        </button>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files?.[0] && processFile(e.target.files[0])}
        accept="image/*"
        className="hidden"
      />

      {!imageSrc ? (
        // Empty State / Upload Dropzone
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative w-full h-56 sm:h-64 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-200 ${
            isDragging
              ? 'border-brand-400 bg-brand-500/10 scale-[1.005]'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/50 hover:bg-slate-900/80'
          }`}
        >
          <div className="w-14 h-14 rounded-2xl bg-slate-800/90 border border-slate-700/60 flex items-center justify-center mb-3 text-brand-400 shadow-inner group-hover:scale-110 transition">
            <UploadCloud className="w-7 h-7" />
          </div>

          <p className="text-sm font-semibold text-slate-200 mb-1">
            点击上传 或 将图片拖拽至此处
          </p>
          <p className="text-xs text-slate-400 mb-3 max-w-sm">
            支持直接按 <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px]">Ctrl + V</kbd> 粘贴剪贴板截图
          </p>

          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span>JPG / PNG / WEBP / GIF</span>
            <span>•</span>
            <span>自动解析画幅比例与色彩主轴</span>
          </div>
        </div>
      ) : (
        // Image Preview & Inspector Panel
        <div className="relative rounded-2xl bg-slate-900/80 border border-slate-800 p-4 space-y-4 shadow-xl">
          <div className="relative flex flex-col md:flex-row items-center gap-5">
            
            {/* Image Container */}
            <div className="relative w-full md:w-56 h-48 sm:h-52 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center flex-shrink-0 group">
              <img
                src={imageSrc}
                alt="Uploaded target"
                className="max-h-full max-w-full object-contain"
              />
              
              {/* Overlay Action */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs flex items-center gap-1"
                  title="更换图片"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> 更换
                </button>
              </div>

              {/* Close Button */}
              <button
                onClick={onClearImage}
                className="absolute top-2 right-2 p-1.5 rounded-full bg-slate-900/90 hover:bg-rose-900/80 text-slate-400 hover:text-white transition border border-slate-700"
                title="移除图片"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Visual Specs & Color Extraction Info */}
            <div className="flex-1 w-full space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-brand-400" />
                  图像视觉特征智能解析
                </h4>
                <span className="px-2 py-0.5 text-[10px] rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  解析就绪
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                  <div className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Crop className="w-3 h-3 text-slate-400" /> 推荐画幅
                  </div>
                  <div className="text-xs font-mono font-bold text-brand-300 mt-0.5">
                    {imageInfo?.ratio || '16:9'}
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                  <div className="text-[10px] text-slate-400">原始分辨率</div>
                  <div className="text-xs font-mono font-bold text-slate-200 mt-0.5">
                    {imageInfo?.width && imageInfo?.height ? `${imageInfo.width} × ${imageInfo.height}` : '自适应'}
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60 col-span-2 sm:col-span-1">
                  <div className="text-[10px] text-slate-400">色彩主基调</div>
                  <div className="text-xs font-semibold text-slate-200 mt-0.5 truncate">
                    {imageInfo?.palette?.[0]?.name || '复合色系'}
                  </div>
                </div>
              </div>

              {/* Dominant Palette Swatches */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <Palette className="w-3 h-3 text-amber-400" />
                  <span>提取主色盘 (Palette):</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {imageInfo?.palette?.map((color, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300"
                    >
                      <span
                        className="w-3.5 h-3.5 rounded-full border border-white/20 shadow-sm"
                        style={{ backgroundColor: color.hex }}
                      />
                      <span>{color.name}</span>
                      <span className="text-[10px] text-slate-400">{color.hex}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

          </div>
        </div>
      )}
    </div>
  );
}
