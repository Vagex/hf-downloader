import React, { useState } from 'react';
import { X, History, Trash2, Download, Search, ExternalLink, Copy, Check } from 'lucide-react';
import { CATEGORIES } from '../services/categories';

export default function HistoryModal({ isOpen, onClose, historyList, onSelectHistoryItem, onClearHistory }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  if (!isOpen) return null;

  const filteredList = historyList.filter(item => {
    const term = searchTerm.toLowerCase();
    return (
      (item.categoryName || '').toLowerCase().includes(term) ||
      (item.result?.englishPrompt || '').toLowerCase().includes(term) ||
      (item.result?.chinesePrompt || '').toLowerCase().includes(term)
    );
  });

  const exportToJson = () => {
    const blob = new Blob([JSON.stringify(historyList, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `PromptReverser_History_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  };

  const exportToMarkdown = () => {
    let md = `# AI 图像反推提示词记录库\n导出时间: ${new Date().toLocaleString()}\n\n---\n\n`;
    historyList.forEach((item, idx) => {
      md += `## 记录 #${idx + 1} · ${item.categoryName || '反推记录'} (${new Date(item.timestamp).toLocaleString()})\n\n`;
      md += `### 推荐参数\n\`${item.result?.recommendedParams || ''}\`\n\n`;
      md += `### 英文 Prompt\n\`\`\`text\n${item.result?.englishPrompt || ''}\n\`\`\`\n\n`;
      md += `### 中文描述\n${item.result?.chinesePrompt || ''}\n\n`;
      if (item.result?.keywords) {
        md += `### 关键词\n${item.result.keywords.join(', ')}\n\n`;
      }
      md += `---\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `PromptReverser_History_${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
  };

  const copyPrompt = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[85vh] rounded-3xl glass-panel border border-slate-700/80 shadow-2xl p-6 flex flex-col space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                反推历史记录库
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-xs font-mono">
                  {historyList.length} 条
                </span>
              </h3>
              <p className="text-xs text-slate-400">所有反推记录均存储在本地，支持一键导出 Markdown 与 JSON</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 flex-shrink-0">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索历史反推词/类别..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl glass-input text-xs"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={exportToMarkdown}
              disabled={historyList.length === 0}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition border border-slate-700"
              title="导出为 Markdown 笔记"
            >
              <Download className="w-3.5 h-3.5 text-brand-400" />
              <span>导出 MD</span>
            </button>
            <button
              onClick={exportToJson}
              disabled={historyList.length === 0}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition border border-slate-700"
              title="导出为 JSON 备份"
            >
              <Download className="w-3.5 h-3.5 text-indigo-400" />
              <span>导出 JSON</span>
            </button>
            <button
              onClick={onClearHistory}
              disabled={historyList.length === 0}
              className="px-3 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 disabled:opacity-50 text-rose-300 text-xs font-medium flex items-center gap-1.5 transition border border-rose-900/60"
              title="清空所有记录"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>清空</span>
            </button>
          </div>
        </div>

        {/* History List Container */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {filteredList.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-slate-500 text-xs">
              <History className="w-8 h-8 mb-2 opacity-30" />
              <span>暂无符合条件的反推记录</span>
            </div>
          ) : (
            filteredList.map((item) => {
              const category = CATEGORIES.find(c => c.id === item.categoryId);
              return (
                <div
                  key={item.id}
                  className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition flex flex-col sm:flex-row items-start gap-4 group"
                >
                  {/* Thumbnail */}
                  {item.image && (
                    <div className="w-20 h-20 rounded-xl overflow-hidden bg-black/60 border border-slate-800 flex items-center justify-center flex-shrink-0">
                      <img src={item.image} alt="thumb" className="w-full h-full object-cover" />
                    </div>
                  )}

                  {/* Details */}
                  <div className="flex-1 space-y-1.5 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-md bg-brand-500/20 text-brand-300 border border-brand-500/30 text-[10px] font-bold">
                          {item.categoryName || category?.name || '反推记录'}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          {new Date(item.timestamp).toLocaleString()}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 opacity-90">
                        <button
                          onClick={() => copyPrompt(item.result?.englishPrompt, item.id)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] flex items-center gap-1 transition"
                        >
                          {copiedId === item.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          <span>复制英文</span>
                        </button>
                        <button
                          onClick={() => {
                            onSelectHistoryItem(item);
                            onClose();
                          }}
                          className="px-2 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-[11px] flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>载入工作台</span>
                        </button>
                      </div>
                    </div>

                    <p className="text-xs font-mono text-slate-300 line-clamp-2 leading-relaxed">
                      {item.result?.englishPrompt}
                    </p>

                    <p className="text-xs text-slate-400 line-clamp-1">
                      {item.result?.chinesePrompt}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>

      </div>
    </div>
  );
}
