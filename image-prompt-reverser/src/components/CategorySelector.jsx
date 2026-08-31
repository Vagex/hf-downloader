import React from 'react';
import { CATEGORIES } from '../services/categories';
import { 
  Sparkles, 
  Type, 
  Mountain, 
  Camera, 
  Palette, 
  Box, 
  Smile, 
  Check 
} from 'lucide-react';

const iconMap = {
  Sparkles,
  Type,
  Mountain,
  Camera,
  Palette,
  Box,
  Smile
};

export default function CategorySelector({ selectedCategoryId, onSelectCategory }) {
  return (
    <div className="w-full space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-brand-500"></span>
          步骤 1 · 选择专业反推模式 (7大类别)
        </label>
        <span className="text-xs text-slate-500">按需选择以匹配专属提示词工程体系</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2.5">
        {CATEGORIES.map((cat, idx) => {
          const IconComp = iconMap[cat.icon] || Sparkles;
          const isSelected = selectedCategoryId === cat.id;

          return (
            <button
              key={cat.id}
              onClick={() => onSelectCategory(cat.id)}
              className={`relative flex flex-col p-3 rounded-xl text-left transition-all duration-200 border group ${
                isSelected
                  ? 'bg-gradient-to-b from-brand-950/70 to-slate-900 border-brand-500/80 shadow-lg shadow-brand-500/10 ring-1 ring-brand-500/40'
                  : 'bg-slate-900/60 hover:bg-slate-800/80 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              {/* Top Badge & Index */}
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105 ${
                    isSelected
                      ? `bg-gradient-to-tr ${cat.color} text-white shadow-md`
                      : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'
                  }`}
                >
                  <IconComp className="w-3.5 h-3.5" />
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  0{idx + 1}
                </span>
              </div>

              {/* Title & Badge */}
              <div className="space-y-0.5">
                <div className="flex items-center gap-1">
                  <h3 className={`text-xs font-bold leading-snug truncate ${isSelected ? 'text-white' : 'text-slate-200'}`}>
                    {cat.name}
                  </h3>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">
                  {cat.badge}
                </p>
              </div>

              {/* Selected Check Indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-brand-500 text-white flex items-center justify-center shadow">
                  <Check className="w-2.5 h-2.5 stroke-[3]" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Category Feature Details Banner */}
      {(() => {
        const current = CATEGORIES.find(c => c.id === selectedCategoryId) || CATEGORIES[0];
        return (
          <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/80 flex flex-wrap items-center gap-3 text-xs text-slate-300">
            <span className="px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30 font-medium">
              当前维度: {current.name}
            </span>
            <span className="text-slate-400">{current.description}</span>
            <div className="hidden lg:flex items-center gap-1.5 ml-auto text-[11px] text-slate-400">
              <span className="text-slate-500">核心拆解项:</span>
              {current.dimensions.slice(0, 4).map((d) => (
                <span key={d.key} className="px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/50">
                  {d.label}
                </span>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
