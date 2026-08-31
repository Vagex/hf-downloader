import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Sparkles, RefreshCw, Layers } from 'lucide-react';

export default function VariableInterpolationModal({ promptData, isOpen, onClose, onToast }) {
  if (!isOpen || !promptData) return null;

  // Extract variables from prompt text {{var}}
  const extractVariables = (text) => {
    const matches = [...text.matchAll(/\{\{([^}]+)\}\}/g)];
    const uniqueKeys = Array.from(new Set(matches.map(m => m[1].trim())));
    
    // Merge with promptData.variables if predefined
    const predefinedMap = {};
    if (promptData.variables && Array.isArray(promptData.variables)) {
      promptData.variables.forEach(v => {
        predefinedMap[v.key] = v;
      });
    }

    return uniqueKeys.map(key => ({
      key,
      label: predefinedMap[key]?.label || key,
      defaultValue: predefinedMap[key]?.defaultValue || ''
    }));
  };

  const [varsList, setVarsList] = useState([]);
  const [formValues, setFormValues] = useState({});
  const [includeNegative, setIncludeNegative] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (promptData) {
      const vars = extractVariables(promptData.prompt || '');
      setVarsList(vars);
      const initialVals = {};
      vars.forEach(v => {
        initialVals[v.key] = v.defaultValue || '';
      });
      setFormValues(initialVals);
      setCopied(false);
    }
  }, [promptData]);

  // Compute final generated prompt
  const getInterpolatedPrompt = () => {
    let result = promptData.prompt || '';
    varsList.forEach(v => {
      const val = formValues[v.key] !== undefined && formValues[v.key] !== '' 
        ? formValues[v.key] 
        : (v.defaultValue || `{{${v.key}}}`);
      const regex = new RegExp(`\\{\\{\\s*${v.key}\\s*\\}\\}`, 'g');
      result = result.replace(regex, val);
    });

    if (includeNegative && promptData.negativePrompt) {
      result += `\n\n【负向提示词 / 约束】:\n${promptData.negativePrompt}`;
    }

    return result;
  };

  const handleCopy = () => {
    const textToCopy = getInterpolatedPrompt();
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    if (onToast) onToast('已成功合成并复制到剪贴板！', 'success');
    setTimeout(() => setCopied(false), 2500);
  };

  const handleReset = () => {
    const initialVals = {};
    varsList.forEach(v => {
      initialVals[v.key] = v.defaultValue || '';
    });
    setFormValues(initialVals);
    if (onToast) onToast('已恢复默认参数', 'info');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] transition-all"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                动态填槽引用
                <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                  {promptData.subcategory || promptData.category}
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                {promptData.title}
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

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Variables Configuration Form */}
          {varsList.length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-blue-500" />
                  填入可变参数 ({varsList.length} 个变量)
                </label>
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-xs text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-1 transition"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  重置默认值
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200/60 dark:border-slate-800">
                {varsList.map((v) => (
                  <div key={v.key} className="space-y-1">
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      {v.label} <code className="text-[10px] text-blue-500 font-mono">({`{{${v.key}}}`})</code>
                    </label>
                    <input
                      type="text"
                      value={formValues[v.key] || ''}
                      onChange={(e) => setFormValues({ ...formValues, [v.key]: e.target.value })}
                      placeholder={v.defaultValue || `输入 ${v.label}`}
                      className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 dark:text-white placeholder-slate-400 transition"
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200/60 dark:border-slate-800 text-sm text-slate-500 dark:text-slate-400">
              此提示词中未检测到 <code className="text-blue-500">{`{{变量}}`}</code> 占位符，将直接使用完整提示词内容。
            </div>
          )}

          {/* Prompt Preview */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                合成后的最终 Prompt 实时预览
              </label>
              {promptData.negativePrompt && (
                <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeNegative}
                    onChange={(e) => setIncludeNegative(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900"
                  />
                  包含负向/约束词
                </label>
              )}
            </div>
            
            <div className="relative">
              <div className="w-full p-4 bg-slate-900 text-slate-100 dark:bg-black font-mono text-sm leading-relaxed rounded-xl border border-slate-800 max-h-64 overflow-y-auto whitespace-pre-wrap selection:bg-blue-600 selection:text-white">
                {getInterpolatedPrompt()}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex items-center justify-between">
          <div className="text-xs text-slate-500 dark:text-slate-400">
            已就绪，点击按钮一键复制即可粘贴到生成软件
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl transition"
            >
              关闭
            </button>
            <button
              onClick={handleCopy}
              className={`flex items-center gap-2 px-5 py-2 text-sm font-semibold rounded-xl text-white shadow-lg transition-all transform active:scale-95 ${
                copied
                  ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/25'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/25'
              }`}
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4" />
                  已复制到剪贴板
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  合成并一键复制
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
