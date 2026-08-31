import React from 'react';
import { AI_ENGINES } from '../services/categories';
import { Sparkles, Play, Sliders, MessageSquare, Zap, Check } from 'lucide-react';

export default function ParameterPanel({
  selectedEngineId,
  onSelectEngine,
  userNotes,
  onChangeUserNotes,
  onStartReverse,
  isLoading,
  hasImage
}) {
  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-brand-500"></span>
          步骤 3 · 目标绘图模型与定制微调
        </label>
        <span className="text-xs text-slate-500">针对特定生图引擎优化指令语法</span>
      </div>

      {/* Target Engine Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {AI_ENGINES.map((engine) => {
          const isSelected = selectedEngineId === engine.id;
          return (
            <button
              key={engine.id}
              onClick={() => onSelectEngine(engine.id)}
              className={`px-3 py-2.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-brand-950/80 border-brand-500 text-white shadow-md shadow-brand-500/10 ring-1 ring-brand-500/50'
                  : 'bg-slate-900/60 hover:bg-slate-800/80 border-slate-800 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-brand-300">
                  {engine.badge}
                </span>
                {isSelected && <Check className="w-3.5 h-3.5 text-brand-400" />}
              </div>
              <span className="text-xs font-semibold mt-1 truncate">
                {engine.name}
              </span>
            </button>
          );
        })}
      </div>

      {/* Optional User Guidance Notes */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <label className="flex items-center gap-1">
            <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
            <span>重点反推关注点 / 自定义补充（选填）:</span>
          </label>
          <span className="text-[11px] text-slate-400">例如：突出头发的发光效果 / 强调胶片噪点</span>
        </div>
        <input
          type="text"
          value={userNotes}
          onChange={(e) => onChangeUserNotes(e.target.value)}
          placeholder="可在此输入你特别希望 AI 重点捕捉的细节、色调或特殊风格..."
          className="w-full px-3.5 py-2 rounded-xl glass-input text-xs placeholder:text-slate-500"
        />
      </div>

      {/* Big Action Button */}
      <button
        onClick={onStartReverse}
        disabled={isLoading || !hasImage}
        className={`w-full py-3.5 px-6 rounded-2xl font-bold text-sm sm:text-base flex items-center justify-center gap-2.5 transition-all duration-300 shadow-xl ${
          isLoading
            ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
            : !hasImage
            ? 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-slate-800'
            : 'bg-gradient-to-r from-brand-600 via-brand-500 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white shadow-brand-500/25 hover:shadow-brand-500/40 hover:scale-[1.008] active:scale-[0.995] border border-white/20'
        }`}
      >
        {isLoading ? (
          <>
            <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
            <span>AI 视觉神经中枢深度反推解析中...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 text-amber-300" />
            <span>{!hasImage ? '请先在上方上传图片' : '立即执行 AI 图像深度反推 (Generate Prompt)'}</span>
            <Zap className="w-4 h-4 opacity-80" />
          </>
        )}
      </button>
    </div>
  );
}
