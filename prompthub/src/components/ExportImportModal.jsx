import React, { useState } from 'react';
import { X, Download, Upload, Copy, Check, FileText, Database, RefreshCw } from 'lucide-react';

export default function ExportImportModal({ isOpen, onClose, prompts, onImportSuccess, onToast }) {
  if (!isOpen) return null;

  const [importText, setImportText] = useState('');
  const [importMode, setImportMode] = useState('merge'); // 'merge' | 'replace'
  const [copied, setCopied] = useState(false);

  // Download JSON file
  const handleDownloadBackup = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(prompts, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `prompthub-backup-${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    if (onToast) onToast('备份文件已开始下载', 'success');
  };

  // Copy JSON to clipboard
  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(prompts, null, 2));
    setCopied(true);
    if (onToast) onToast('JSON 备份数据已复制到剪贴板', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  // File upload import
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        if (Array.isArray(parsed)) {
          executeImport(parsed);
        } else {
          if (onToast) onToast('文件格式不正确，必须为 JSON 数组', 'error');
        }
      } catch (err) {
        if (onToast) onToast('解析 JSON 文件失败', 'error');
      }
    };
    reader.readAsText(file);
  };

  // Textarea import
  const handleTextImport = () => {
    try {
      const parsed = JSON.parse(importText);
      if (Array.isArray(parsed)) {
        executeImport(parsed);
      } else {
        if (onToast) onToast('输入内容必须是 JSON 提示词数组', 'error');
      }
    } catch (err) {
      if (onToast) onToast('JSON 格式错误，请检查语法', 'error');
    }
  };

  const executeImport = async (newPrompts) => {
    try {
      const res = await fetch('/api/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompts: newPrompts, mode: importMode })
      });
      const json = await res.json();
      if (json.success) {
        if (onToast) onToast(`成功导入 ${newPrompts.length} 条提示词！`, 'success');
        onImportSuccess();
        onClose();
      } else {
        throw new Error(json.message);
      }
    } catch (err) {
      // Offline fallback: save to localStorage
      let updated = [];
      if (importMode === 'replace') {
        updated = newPrompts;
      } else {
        const existingIds = new Set(prompts.map(p => p.id));
        const toAdd = newPrompts.filter(p => !existingIds.has(p.id));
        updated = [...toAdd, ...prompts];
      }
      localStorage.setItem('prompthub_offline_data', JSON.stringify(updated));
      if (onToast) onToast(`已在本地成功导入 ${newPrompts.length} 条提示词！`, 'success');
      onImportSuccess();
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col transition-all"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                数据备份与迁移
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                支持全量 JSON 导出、本地一键还原与多设备数据同步
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

        {/* Content */}
        <div className="p-6 space-y-6 text-sm overflow-y-auto max-h-[80vh]">
          {/* Export Section */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Download className="w-4 h-4 text-blue-500" />
              导出当前提示词库 ({prompts.length} 条)
            </label>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleDownloadBackup}
                className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-500/20 transition active:scale-95"
              >
                <Download className="w-4 h-4" />
                下载 JSON 备份文件
              </button>
              <button
                onClick={handleCopyJSON}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-semibold transition"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                {copied ? '已复制 JSON' : '复制 JSON 到剪贴板'}
              </button>
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800" />

          {/* Import Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Upload className="w-4 h-4 text-indigo-500" />
                导入或恢复数据
              </label>

              {/* Merge Mode Toggle */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">导入策略:</span>
                <label className="inline-flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="importMode"
                    value="merge"
                    checked={importMode === 'merge'}
                    onChange={() => setImportMode('merge')}
                    className="text-blue-600"
                  />
                  <span className="text-slate-600 dark:text-slate-300">增量合并</span>
                </label>
                <label className="inline-flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="importMode"
                    value="replace"
                    checked={importMode === 'replace'}
                    onChange={() => setImportMode('replace')}
                    className="text-blue-600"
                  />
                  <span className="text-slate-600 dark:text-slate-300">完全覆盖</span>
                </label>
              </div>
            </div>

            {/* File Upload Button */}
            <div>
              <label className="border-2 border-dashed border-slate-200 dark:border-slate-700 hover:border-blue-500 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition bg-slate-50/50 dark:bg-slate-800/30 text-slate-600 dark:text-slate-300">
                <Upload className="w-6 h-6 mb-1 text-slate-400" />
                <span className="text-xs font-medium">点击选择本地 .json 备份文件导入</span>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Direct Paste JSON */}
            <div className="space-y-2">
              <textarea
                rows={4}
                value={importText}
                onChange={e => setImportText(e.target.value)}
                placeholder="或直接将 JSON 备份文本粘贴至此..."
                className="w-full p-3 font-mono text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
              {importText.trim() && (
                <button
                  onClick={handleTextImport}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-md transition"
                >
                  确认导入粘贴的数据
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl transition"
          >
            完成
          </button>
        </div>
      </div>
    </div>
  );
}
