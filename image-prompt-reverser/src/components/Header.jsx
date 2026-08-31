import React from 'react';
import { Sparkles, Settings, History, Image as ImageIcon, BookOpen, Layers, ShieldCheck } from 'lucide-react';

export default function Header({ 
  onOpenSettings, 
  onOpenHistory, 
  onOpenGallery, 
  historyCount = 0,
  apiProvider = 'simulation'
}) {
  return (
    <header className="sticky top-0 z-30 w-full glass-panel border-b border-slate-800/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/25 ring-1 ring-white/20">
            <Sparkles className="w-5 h-5 text-white animate-pulse-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-brand-300 bg-clip-text text-transparent">
                PromptReverser Studio
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30 rounded-full">
                7大专业模式
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI 图像反向工程与精准绘图提示词提取工作台
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Preset Gallery Button */}
          <button
            onClick={onOpenGallery}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 hover:border-brand-500/50 transition shadow-sm"
            title="查看预设范例库"
          >
            <ImageIcon className="w-3.5 h-3.5 text-brand-400" />
            <span className="hidden md:inline">预设范例库</span>
            <span className="md:hidden">范例</span>
          </button>

          {/* History Button */}
          <button
            onClick={onOpenHistory}
            className="relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 hover:border-brand-500/50 transition shadow-sm"
            title="反推历史记录"
          >
            <History className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden md:inline">反推历史</span>
            <span className="md:hidden">历史</span>
            {historyCount > 0 && (
              <span className="ml-0.5 px-1.5 py-0.2 bg-brand-500 text-white rounded-full text-[10px] font-bold">
                {historyCount}
              </span>
            )}
          </button>

          {/* API Settings Button */}
          <button
            onClick={onOpenSettings}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition shadow-sm border ${
              apiProvider !== 'simulation'
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40 hover:bg-emerald-900/50'
                : 'bg-slate-800/80 text-slate-300 border-slate-700/60 hover:bg-slate-700/80 hover:border-brand-500/50'
            }`}
            title="配置 Vision 视觉大模型 API"
          >
            <Settings className={`w-3.5 h-3.5 ${apiProvider !== 'simulation' ? 'text-emerald-400' : 'text-slate-400'}`} />
            <span className="hidden sm:inline">
              {apiProvider === 'simulation' ? '模型设置 (免Key仿真)' : `API: ${apiProvider}`}
            </span>
            <span className="sm:hidden">设置</span>
          </button>

        </div>

      </div>
    </header>
  );
}
