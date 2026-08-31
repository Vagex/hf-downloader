import React, { useState } from 'react';
import { X, Sparkles, ArrowRight, Layers, Tag, Eye } from 'lucide-react';
import { SAMPLE_PRESETS } from '../services/samplePresets';
import { CATEGORIES } from '../services/categories';

export default function PresetGalleryModal({ isOpen, onClose, onSelectPreset }) {
  const [activeCategoryFilter, setActiveCategoryFilter] = useState('all');

  if (!isOpen) return null;

  const filteredPresets = activeCategoryFilter === 'all'
    ? SAMPLE_PRESETS
    : SAMPLE_PRESETS.filter(p => p.categoryId === activeCategoryFilter);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-5xl max-h-[90vh] rounded-3xl glass-panel border border-slate-700/80 shadow-2xl p-6 flex flex-col space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                7大专业模式 · 官方预设范例展厅
                <span className="px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 text-xs font-mono">
                  开箱即试
                </span>
              </h3>
              <p className="text-xs text-slate-400">点击任意范例卡片，一键载入图像并在工作台体验完整反推与 Prompt 解构</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 flex-shrink-0">
          <button
            onClick={() => setActiveCategoryFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
              activeCategoryFilter === 'all'
                ? 'bg-brand-600 text-white shadow-md'
                : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            全部范例 ({SAMPLE_PRESETS.length})
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategoryFilter(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition flex items-center gap-1 ${
                activeCategoryFilter === cat.id
                  ? 'bg-brand-600 text-white shadow-md'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <span>{cat.name}</span>
            </button>
          ))}
        </div>

        {/* Gallery Grid */}
        <div className="flex-1 overflow-y-auto pr-1">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPresets.map((preset) => {
              const cat = CATEGORIES.find(c => c.id === preset.categoryId) || CATEGORIES[0];
              return (
                <div
                  key={preset.id}
                  className="rounded-2xl bg-slate-900/90 border border-slate-800/80 hover:border-brand-500/50 hover:shadow-xl transition duration-200 overflow-hidden flex flex-col justify-between group"
                >
                  {/* Image Preview Box */}
                  <div className="relative w-full h-44 bg-slate-950 flex items-center justify-center overflow-hidden border-b border-slate-800/60">
                    <img
                      src={preset.image}
                      alt={preset.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-md text-[10px] font-bold text-brand-300 border border-slate-700">
                      {cat.name}
                    </span>
                  </div>

                  {/* Body Content */}
                  <div className="p-4 space-y-2 flex-1 flex flex-col justify-between">
                    <div className="space-y-1">
                      <h4 className="text-sm font-bold text-white group-hover:text-brand-300 transition">
                        {preset.title}
                      </h4>
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {preset.result.chinesePrompt}
                      </p>
                    </div>

                    {/* Keywords Tag Preview */}
                    <div className="flex flex-wrap gap-1 pt-2">
                      {preset.result.keywords?.slice(0, 3).map((kw, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-400"
                        >
                          #{kw}
                        </span>
                      ))}
                    </div>

                    {/* Load Button */}
                    <button
                      onClick={() => {
                        onSelectPreset(preset);
                        onClose();
                      }}
                      className="w-full mt-3 py-2 px-3 rounded-xl bg-brand-600/90 hover:bg-brand-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-md"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>载入工作台体验</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
