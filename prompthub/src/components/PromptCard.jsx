import React, { useState } from 'react';
import { 
  Copy, Check, Sparkles, Pin, Star, Film, Image as ImageIcon, 
  MessageSquare, Edit3, Trash2, Tag, Maximize2, Clock, Ratio, ExternalLink, Play
} from 'lucide-react';

export default function PromptCard({ 
  prompt, 
  onInterpolate, 
  onEdit, 
  onDelete, 
  onTogglePin, 
  onToast,
  viewMode = 'grid' // 'grid' | 'compact'
}) {
  const [copied, setCopied] = useState(false);
  const [mediaLightbox, setMediaLightbox] = useState(null); // { url, isVideo }

  // Check if prompt has variables
  const hasVariables = /\{\{([^}]+)\}\}/.test(prompt.prompt || '');

  // Quick copy plain prompt
  const handleQuickCopy = (e) => {
    e.stopPropagation();
    let text = prompt.prompt || '';
    if (prompt.negativePrompt) {
      text += `\n\n【负向提示词】:\n${prompt.negativePrompt}`;
    }
    navigator.clipboard.writeText(text);
    setCopied(true);
    if (onToast) onToast('已复制完整提示词！', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  // Render highlighted prompt text with variable pills
  const renderHighlightedPrompt = (text) => {
    if (!text) return null;
    const parts = text.split(/(\{\{[^}]+\}\})/g);
    return parts.map((part, i) => {
      if (part.startsWith('{{') && part.endsWith('}}')) {
        const varName = part.slice(2, -2).trim();
        return (
          <span 
            key={i} 
            className="inline-block px-1.5 py-0.5 mx-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-700 dark:bg-purple-900/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
          >
            {`{{${varName}}}`}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  const getCategoryIcon = () => {
    switch (prompt.category) {
      case 'video': return <Film className="w-3.5 h-3.5" />;
      case 'image': return <ImageIcon className="w-3.5 h-3.5" />;
      default: return <MessageSquare className="w-3.5 h-3.5" />;
    }
  };

  const getCategoryColor = () => {
    switch (prompt.category) {
      case 'video': return 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200 dark:border-amber-900/50';
      case 'image': return 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border-indigo-200 dark:border-indigo-900/50';
      default: return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900/50';
    }
  };

  // Check if media item is video
  const isVideoUrl = (url) => {
    if (!url) return false;
    const cleanUrl = url.split('?')[0].toLowerCase();
    return cleanUrl.endsWith('.mp4') || cleanUrl.endsWith('.webm') || cleanUrl.endsWith('.mov') || cleanUrl.endsWith('.mkv') || url.includes('/uploads/video-');
  };

  // Combine images and videos
  const mediaList = [
    ...(Array.isArray(prompt.videos) ? prompt.videos : []),
    ...(Array.isArray(prompt.images) ? prompt.images : [])
  ];

  return (
    <>
      <div 
        className={`group bg-white dark:bg-slate-900 rounded-2xl border transition-all duration-300 flex flex-col justify-between overflow-hidden shadow-sm hover:shadow-xl ${
          prompt.isPinned 
            ? 'border-blue-300 dark:border-blue-800/80 ring-1 ring-blue-500/20' 
            : 'border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
        } ${viewMode === 'compact' ? 'p-4' : 'p-5'}`}
      >
        {/* Card Top / Header */}
        <div>
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex flex-wrap items-center gap-1.5">
              {/* Category Badge */}
              <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg border ${getCategoryColor()}`}>
                {getCategoryIcon()}
                {prompt.category === 'video' ? '视频' : prompt.category === 'image' ? '生图' : '文本'}
              </span>

              {/* Subcategory / Model Badge */}
              {prompt.subcategory && (
                <span className="px-2 py-0.5 text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-md">
                  {prompt.subcategory}
                </span>
              )}

              {/* Aspect Ratio */}
              {prompt.aspectRatio && (
                <span className="inline-flex items-center gap-0.5 px-2 py-0.5 text-[11px] font-mono bg-slate-100 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 rounded-md">
                  <Ratio className="w-3 h-3" />
                  {prompt.aspectRatio}
                </span>
              )}

              {/* Duration */}
              {prompt.duration && (
                <span className="inline-flex items-center gap-0.5 px-2 py-0.5 text-[11px] font-mono bg-slate-100 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 rounded-md">
                  <Clock className="w-3 h-3" />
                  {prompt.duration}
                </span>
              )}
            </div>

            {/* Quick Actions (Pin, Edit, Delete) */}
            <div className="flex items-center space-x-1">
              <button
                onClick={(e) => { e.stopPropagation(); onTogglePin(prompt.id); }}
                title={prompt.isPinned ? '取消置顶' : '置顶收藏'}
                className={`p-1.5 rounded-lg transition ${
                  prompt.isPinned 
                    ? 'text-amber-500 bg-amber-50 dark:bg-amber-950/50 hover:bg-amber-100' 
                    : 'text-slate-400 hover:text-amber-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Pin className={`w-4 h-4 ${prompt.isPinned ? 'fill-amber-500' : ''}`} />
              </button>
              
              <button
                onClick={(e) => { e.stopPropagation(); onEdit(prompt); }}
                title="编辑"
                className="p-1.5 text-slate-400 hover:text-blue-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition"
              >
                <Edit3 className="w-4 h-4" />
              </button>

              <button
                onClick={(e) => { e.stopPropagation(); onDelete(prompt.id); }}
                title="删除"
                className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-1 mb-2">
            {prompt.title}
          </h3>

          {/* Reference Images / Videos */}
          {mediaList.length > 0 && viewMode !== 'compact' && (
            <div className="mb-3.5">
              <div className={`grid gap-2 rounded-xl overflow-hidden ${
                mediaList.length === 1 ? 'grid-cols-1' : mediaList.length === 2 ? 'grid-cols-2' : 'grid-cols-3'
              }`}>
                {mediaList.slice(0, 3).map((mediaUrl, idx) => {
                  const isVid = isVideoUrl(mediaUrl);
                  return (
                    <div 
                      key={idx} 
                      className="relative group/img aspect-video bg-slate-100 dark:bg-slate-800 overflow-hidden cursor-pointer rounded-lg border border-slate-200/50 dark:border-slate-700/50"
                      onClick={() => setMediaLightbox({ url: mediaUrl, isVideo: isVid })}
                    >
                      {isVid ? (
                        <>
                          <video 
                            src={mediaUrl} 
                            muted 
                            loop 
                            playsInline 
                            className="w-full h-full object-cover"
                            onMouseEnter={e => e.target.play().catch(() => {})}
                            onMouseLeave={e => e.target.pause()}
                          />
                          <div className="absolute top-1.5 left-1.5 px-2 py-0.5 rounded bg-black/70 text-white text-[10px] font-medium flex items-center gap-1 backdrop-blur-xs">
                            <Film className="w-2.5 h-2.5 text-blue-400" />
                            <span>AI 视频</span>
                          </div>
                          <div className="absolute inset-0 bg-black/20 group-hover/img:bg-black/40 transition flex items-center justify-center text-white">
                            <div className="w-8 h-8 rounded-full bg-blue-600/90 flex items-center justify-center shadow-lg group-hover/img:scale-110 transition-transform">
                              <Play className="w-3.5 h-3.5 ml-0.5 fill-white" />
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <img 
                            src={mediaUrl} 
                            alt="Prompt Reference" 
                            className="w-full h-full object-cover transition-transform duration-500 group-hover/img:scale-105"
                            loading="lazy"
                          />
                          <div className="absolute inset-0 bg-black/30 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center text-white">
                            <Maximize2 className="w-4 h-4" />
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Prompt Body */}
          <div className="relative mb-3">
            <div className={`p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800/80 font-mono text-xs text-slate-800 dark:text-slate-200 leading-relaxed overflow-hidden whitespace-pre-wrap ${
              viewMode === 'compact' ? 'max-h-24' : 'max-h-48'
            } overflow-y-auto`}>
              {renderHighlightedPrompt(prompt.prompt)}
            </div>
          </div>

          {/* Negative Prompt Callout (if present) */}
          {prompt.negativePrompt && viewMode !== 'compact' && (
            <div className="mb-3 p-2.5 rounded-lg bg-red-50/70 dark:bg-red-950/20 border border-red-200/50 dark:border-red-900/40 text-[11px] text-red-700 dark:text-red-300">
              <span className="font-semibold mr-1">负向约束:</span>
              {prompt.negativePrompt}
            </div>
          )}

          {/* Notes / Tips */}
          {prompt.notes && (
            <p className="text-[11px] text-slate-500 dark:text-slate-400 italic mb-3 line-clamp-1">
              💡 {prompt.notes}
            </p>
          )}

          {/* Tags */}
          {prompt.tags && prompt.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {prompt.tags.map((tag) => (
                <span 
                  key={tag} 
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-slate-800 dark:hover:text-blue-400 rounded-md transition"
                >
                  <Tag className="w-2.5 h-2.5 text-blue-500" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Card Footer / Action Buttons */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2">
          {/* Quick Copy */}
          <button
            onClick={handleQuickCopy}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-medium border transition ${
              copied
                ? 'bg-emerald-50 text-emerald-600 border-emerald-300 dark:bg-emerald-950/40 dark:border-emerald-800'
                : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/80'
            }`}
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-500" />
                已复制
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                快速复制
              </>
            )}
          </button>

          {/* Dynamic Interpolation Button (Highlight if has variables) */}
          <button
            onClick={() => onInterpolate(prompt)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-semibold shadow-sm transition transform active:scale-95 ${
              hasVariables
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-blue-500/20'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-yellow-300 animate-pulse" />
            {hasVariables ? '填槽引用 ⚡' : '引用定制'}
          </button>
        </div>
      </div>

      {/* Image & Video Lightbox Preview Modal */}
      {mediaLightbox && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fadeIn"
          onClick={() => setMediaLightbox(null)}
        >
          <div 
            className="relative max-w-5xl max-h-[90vh] overflow-hidden rounded-2xl flex flex-col items-center justify-center"
            onClick={e => e.stopPropagation()}
          >
            {mediaLightbox.isVideo ? (
              <div className="relative w-full max-h-[85vh] flex flex-col items-center">
                <video 
                  src={mediaLightbox.url} 
                  controls 
                  autoPlay 
                  className="max-w-full max-h-[80vh] rounded-xl shadow-2xl bg-black" 
                />
                <div className="mt-3 flex items-center gap-3">
                  <a
                    href={mediaLightbox.url}
                    download
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow transition"
                  >
                    ⬇️ 下载原视频
                  </a>
                  <button
                    onClick={() => setMediaLightbox(null)}
                    className="px-4 py-1.5 rounded-xl bg-slate-800 text-white text-xs font-medium hover:bg-slate-700 transition"
                  >
                    关闭 ✕
                  </button>
                </div>
              </div>
            ) : (
              <>
                <img 
                  src={mediaLightbox.url} 
                  alt="Preview" 
                  className="max-w-full max-h-[85vh] object-contain rounded-xl shadow-2xl" 
                />
                <button
                  onClick={() => setMediaLightbox(null)}
                  className="absolute top-3 right-3 px-3 py-1.5 rounded-xl bg-black/60 text-white text-xs font-medium backdrop-blur-sm hover:bg-black/80 transition"
                >
                  关闭 ✕
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
