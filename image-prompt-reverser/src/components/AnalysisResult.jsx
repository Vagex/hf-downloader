import React, { useState } from 'react';
import { 
  Copy, 
  Check, 
  Sparkles, 
  Layers, 
  Sun, 
  Palette, 
  Layout, 
  Maximize2, 
  Feather, 
  Tag, 
  Share2, 
  Bookmark, 
  AlertCircle,
  Terminal,
  FileText
} from 'lucide-react';
import { AI_ENGINES } from '../services/categories';

export default function AnalysisResult({ 
  result, 
  category, 
  selectedEngineId, 
  imageInfo,
  onSaveHistory 
}) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [activePromptTab, setActivePromptTab] = useState('bilingual'); // 'bilingual', 'english', 'chinese', 'command'

  if (!result) return null;

  const currentEngine = AI_ENGINES.find(e => e.id === selectedEngineId) || AI_ENGINES[0];

  // Construct target engine command
  const buildEngineCommand = () => {
    const rawEng = result.englishPrompt || '';
    const params = result.recommendedParams || '';
    if (selectedEngineId === 'midjourney' || selectedEngineId === 'niji') {
      return `/imagine prompt: ${rawEng} ${params}`.trim();
    }
    return `${rawEng} ${params}`.trim();
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const breakdownItems = [
    { key: 'subjectBreakdown', label: '主体与内容', icon: Layers, color: 'text-blue-400', content: result.subjectBreakdown },
    { key: 'styleBreakdown', label: '风格与流派', icon: Feather, color: 'text-purple-400', content: result.styleBreakdown },
    { key: 'lightingBreakdown', label: '光影与氛围', icon: Sun, color: 'text-amber-400', content: result.lightingBreakdown },
    { key: 'colorBreakdown', label: '色彩与色调', icon: Palette, color: 'text-emerald-400', content: result.colorBreakdown },
    { key: 'compositionBreakdown', label: '构图与镜头', icon: Layout, color: 'text-cyan-400', content: result.compositionBreakdown },
    { key: 'textureBreakdown', label: '材质与质感', icon: Maximize2, color: 'text-pink-400', content: result.textureBreakdown },
  ].filter(item => Boolean(item.content));

  return (
    <div className="w-full space-y-6 pt-4 border-t border-slate-800/80 animate-fadeIn">
      
      {/* Warning if fallback */}
      {result._warning && (
        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 flex items-center gap-2.5 text-xs text-amber-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>{result._warning}</span>
        </div>
      )}

      {/* Header Info Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30 flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              反推结果就绪 · {category?.name || '通用模式'}
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] border border-emerald-500/30 font-mono">
                精准解构完成
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              适配 {currentEngine.name} 提示词工程规范 · 可直接复制使用
            </p>
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => copyToClipboard(buildEngineCommand(), 'all-cmd')}
            className="px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 transition shadow-lg shadow-brand-600/25"
          >
            {copiedKey === 'all-cmd' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>一键复制生图指令</span>
          </button>
        </div>
      </div>

      {/* Prompt Card with Multiple Views */}
      <div className="rounded-2xl glass-panel p-5 space-y-4 shadow-xl border border-slate-800">
        
        {/* Tab Headers */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800">
            <button
              onClick={() => setActivePromptTab('bilingual')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePromptTab === 'bilingual'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              中英双语对照
            </button>
            <button
              onClick={() => setActivePromptTab('english')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePromptTab === 'english'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              纯英文 Prompt
            </button>
            <button
              onClick={() => setActivePromptTab('chinese')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePromptTab === 'chinese'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              纯中文 Prompt
            </button>
            <button
              onClick={() => setActivePromptTab('command')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePromptTab === 'command'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-3 h-3 inline mr-1" />
              生图完整指令
            </button>
          </div>

          <span className="text-[11px] font-mono text-slate-400">
            建议参数: <code className="px-1.5 py-0.5 rounded bg-slate-800 text-brand-300 border border-slate-700">{result.recommendedParams || '--ar 16:9 --v 6.1'}</code>
          </span>
        </div>

        {/* Content depending on Active Tab */}
        {activePromptTab === 'bilingual' && (
          <div className="space-y-4">
            {/* English Box */}
            <div className="relative p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 group">
              <div className="flex items-center justify-between mb-1.5 text-xs text-slate-400">
                <span className="font-semibold text-brand-300 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400" /> English Prompt (推荐用于 MJ / FLUX / SD)
                </span>
                <button
                  onClick={() => copyToClipboard(result.englishPrompt, 'eng')}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] flex items-center gap-1 transition"
                >
                  {copiedKey === 'eng' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>复制英文</span>
                </button>
              </div>
              <p className="text-sm font-mono text-slate-200 leading-relaxed select-all">
                {result.englishPrompt}
              </p>
            </div>

            {/* Chinese Box */}
            <div className="relative p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 group">
              <div className="flex items-center justify-between mb-1.5 text-xs text-slate-400">
                <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> 中文详细描述 (用于可灵/大模型/语义理解)
                </span>
                <button
                  onClick={() => copyToClipboard(result.chinesePrompt, 'cn')}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] flex items-center gap-1 transition"
                >
                  {copiedKey === 'cn' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>复制中文</span>
                </button>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed select-all">
                {result.chinesePrompt}
              </p>
            </div>
          </div>
        )}

        {activePromptTab === 'english' && (
          <div className="relative p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="flex justify-end mb-2">
              <button
                onClick={() => copyToClipboard(result.englishPrompt, 'eng-only')}
                className="px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-xs flex items-center gap-1"
              >
                {copiedKey === 'eng-only' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />} 复制英文 Prompt
              </button>
            </div>
            <p className="text-sm font-mono text-slate-200 leading-relaxed select-all">
              {result.englishPrompt}
            </p>
          </div>
        )}

        {activePromptTab === 'chinese' && (
          <div className="relative p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="flex justify-end mb-2">
              <button
                onClick={() => copyToClipboard(result.chinesePrompt, 'cn-only')}
                className="px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-xs flex items-center gap-1"
              >
                {copiedKey === 'cn-only' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />} 复制中文 Prompt
              </button>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed select-all">
              {result.chinesePrompt}
            </p>
          </div>
        )}

        {activePromptTab === 'command' && (
          <div className="relative p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">
                适配引擎: <strong className="text-brand-300">{currentEngine.name}</strong>
              </span>
              <button
                onClick={() => copyToClipboard(buildEngineCommand(), 'cmd-only')}
                className="px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-xs flex items-center gap-1"
              >
                {copiedKey === 'cmd-only' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />} 复制完整指令
              </button>
            </div>
            <div className="p-3 rounded-lg bg-black/70 border border-slate-800 text-xs font-mono text-emerald-300 select-all overflow-x-auto">
              {buildEngineCommand()}
            </div>
          </div>
        )}

        {/* Negative Prompt Row if exists */}
        {result.negativePrompt && (
          <div className="pt-2 border-t border-slate-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 text-slate-400">
              <span className="font-semibold text-rose-400">Negative Prompt (负向约束词):</span>
              <span className="font-mono text-slate-300 select-all line-clamp-1">{result.negativePrompt}</span>
            </div>
            <button
              onClick={() => copyToClipboard(result.negativePrompt, 'neg')}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] self-end sm:self-auto transition"
            >
              {copiedKey === 'neg' ? '已复制' : '复制负向词'}
            </button>
          </div>
        )}

      </div>

      {/* Keywords Chips (Interactive) */}
      {result.keywords && result.keywords.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Tag className="w-3.5 h-3.5 text-amber-400" />
              精准特征关键词标签 (点击即可复制单个标签):
            </span>
            <button
              onClick={() => copyToClipboard(result.keywords.join(', '), 'all-tags')}
              className="text-xs text-brand-400 hover:text-brand-300"
            >
              {copiedKey === 'all-tags' ? '已复制全部标签' : '一键复制全部标签'}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {result.keywords.map((kw, idx) => (
              <button
                key={idx}
                onClick={() => copyToClipboard(kw, `kw-${idx}`)}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-brand-500/50 text-xs font-mono text-slate-300 hover:text-white transition flex items-center gap-1.5 shadow-sm group"
              >
                <span>{kw}</span>
                {copiedKey === `kw-${idx}` ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Copy className="w-2.5 h-2.5 opacity-0 group-hover:opacity-60" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6-Dimension Structured Breakdown Matrix */}
      {breakdownItems.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-brand-400" />
              多维深度拆解矩阵 (6维视觉体系)
            </h4>
            <span className="text-xs text-slate-500">剖析风格、光影、材质、构图与镜头</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {breakdownItems.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.key}
                  className="p-4 rounded-xl glass-panel border border-slate-800/80 hover:border-slate-700/80 transition space-y-2 flex flex-col justify-between shadow-md"
                >
                  <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${item.color}`} />
                      <span className="text-xs font-bold text-slate-200">{item.label}</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(item.content, item.key)}
                      className="p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition"
                      title="复制此维度描述"
                    >
                      {copiedKey === item.key ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {item.content}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
