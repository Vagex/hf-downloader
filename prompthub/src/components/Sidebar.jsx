import React from 'react';
import { 
  Compass, Film, Image as ImageIcon, MessageSquare, Star, 
  Tag, Ratio, Sparkles, Layers, SlidersHorizontal, Check
} from 'lucide-react';

export default function Sidebar({
  prompts,
  activeCategory,
  setActiveCategory,
  selectedModel,
  setSelectedModel,
  selectedTag,
  setSelectedTag,
  selectedRatio,
  setSelectedRatio,
  onlyPinned,
  setOnlyPinned,
  sidebarOpen,
  setSidebarOpen
}) {
  // Count stats
  const totalCount = prompts.length;
  const videoCount = prompts.filter(p => p.category === 'video').length;
  const imageCount = prompts.filter(p => p.category === 'image').length;
  const textCount = prompts.filter(p => p.category === 'text').length;
  const pinnedCount = prompts.filter(p => p.isPinned).length;

  // Extract all unique tags with count
  const tagCounts = {};
  prompts.forEach(p => {
    if (Array.isArray(p.tags)) {
      p.tags.forEach(t => {
        tagCounts[t] = (tagCounts[t] || 0) + 1;
      });
    }
  });
  const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]);

  // Extract unique aspect ratios
  const ratios = Array.from(new Set(prompts.map(p => p.aspectRatio).filter(Boolean)));

  const categories = [
    { key: 'all', label: '全部提示词', icon: Compass, count: totalCount },
    { key: 'video', label: 'AI 视频生成', icon: Film, count: videoCount, desc: 'Sora / Runway / 可灵' },
    { key: 'image', label: 'AI 视觉生图', icon: ImageIcon, count: imageCount, desc: 'Midjourney / FLUX' },
    { key: 'text', label: '大模型 / 文本', icon: MessageSquare, count: textCount, desc: 'Claude / GPT-4o' }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`
        fixed lg:sticky top-16 z-30 h-[calc(100vh-4rem)] w-64 flex-shrink-0 
        bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800 
        transition-all duration-300 ease-in-out overflow-y-auto p-4 space-y-6
        ${sidebarOpen ? 'left-0 shadow-2xl' : '-left-64 lg:left-0'}
      `}>
        {/* Navigation Categories */}
        <div className="space-y-1">
          <div className="px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            分类导航
          </div>
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.key && !onlyPinned;
            return (
              <button
                key={cat.key}
                onClick={() => {
                  setActiveCategory(cat.key);
                  setOnlyPinned(false);
                  if (window.innerWidth < 1024) setSidebarOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`} />
                  <span>{cat.label}</span>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
                  isActive ? 'bg-blue-200/60 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                }`}>
                  {cat.count}
                </span>
              </button>
            );
          })}

          {/* Starred / Pinned filter */}
          <button
            onClick={() => {
              setOnlyPinned(!onlyPinned);
              if (window.innerWidth < 1024) setSidebarOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
              onlyPinned
                ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <Star className={`w-4 h-4 ${onlyPinned ? 'text-amber-500 fill-amber-500' : 'text-slate-400'}`} />
              <span>星标精选库</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-slate-100 dark:bg-slate-800 text-slate-500">
              {pinnedCount}
            </span>
          </button>
        </div>

        {/* Models & Engines Filter (Prioritizing LTX 2.5 and Minimax h3) */}
        <div className="space-y-2">
          <div className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center justify-between">
            <span>主力引擎 / 模型</span>
            {selectedModel && (
              <button
                onClick={() => setSelectedModel(null)}
                className="text-[10px] text-blue-500 lowercase hover:underline"
              >
                清除
              </button>
            )}
          </div>
          <div className="space-y-1">
            {[
              { id: 'LTX 2.5', label: 'LTX 2.5', highlight: true, tag: '推荐' },
              { id: 'Minimax h3', label: 'Minimax h3', highlight: true, tag: '海螺' },
              { id: '可灵', label: '可灵 Kling', highlight: false },
              { id: 'Runway', label: 'Runway Gen-3', highlight: false },
              { id: 'FLUX', label: 'FLUX.1', highlight: false },
              { id: 'Midjourney', label: 'Midjourney', highlight: false }
            ].map(m => {
              const isSelected = selectedModel === m.id;
              const count = prompts.filter(p => (p.subcategory || '').toLowerCase().includes(m.id.toLowerCase())).length;
              return (
                <button
                  key={m.id}
                  onClick={() => {
                    setSelectedModel(isSelected ? null : m.id);
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs transition ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-xs font-semibold'
                      : m.highlight
                      ? 'bg-amber-50/70 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 hover:bg-amber-100/70 border border-amber-200/50 dark:border-amber-900/30'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    {m.highlight && <span className="text-[10px]">🔥</span>}
                    <span>{m.label}</span>
                    {m.tag && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-amber-200 dark:bg-amber-900 text-amber-800 dark:text-amber-200 font-bold">
                        {m.tag}
                      </span>
                    )}
                  </div>
                  {count > 0 && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                      isSelected ? 'bg-blue-800 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                    }`}>
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Aspect Ratio Filter (if any) */}
        {ratios.length > 0 && (
          <div className="space-y-2">
            <div className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center justify-between">
              <span>画幅比 (Ratio)</span>
              {selectedRatio && (
                <button
                  onClick={() => setSelectedRatio(null)}
                  className="text-[10px] text-blue-500 lowercase hover:underline"
                >
                  清除
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5 px-1">
              {ratios.map(r => (
                <button
                  key={r}
                  onClick={() => setSelectedRatio(selectedRatio === r ? null : r)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono border transition ${
                    selectedRatio === r
                      ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                      : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200/80 dark:border-slate-700/80 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tags Cloud */}
        <div className="space-y-2">
          <div className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center justify-between">
            <span>常用镜头与标签</span>
            {selectedTag && (
              <button
                onClick={() => setSelectedTag(null)}
                className="text-[10px] text-blue-500 lowercase hover:underline"
              >
                清除
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5 px-1 max-h-60 overflow-y-auto">
            {sortedTags.map(([tag, count]) => {
              const isSelected = selectedTag === tag;
              return (
                <button
                  key={tag}
                  onClick={() => {
                    setSelectedTag(isSelected ? null : tag);
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs transition ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-xs font-medium'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  <Tag className="w-2.5 h-2.5 text-blue-400" />
                  <span>{tag}</span>
                  <span className={`text-[10px] ${isSelected ? 'text-blue-100' : 'text-slate-400'}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Pro Tips Box */}
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20 text-xs space-y-1.5">
          <div className="font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" />
            快速引用技巧
          </div>
          <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
            在提示词中使用 <code className="text-blue-600 dark:text-blue-300 font-mono">{`{{变量名}}`}</code>，点击卡片「填槽引用」即可秒级替换参数生成新词！
          </p>
        </div>
      </aside>
    </>
  );
}
