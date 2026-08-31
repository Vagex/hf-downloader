import React, { useState, useEffect } from 'react';
import { X, Settings, Key, Globe, Cpu, Check, HelpCircle, Shield, AlertTriangle } from 'lucide-react';
import { getStoredApiSettings, saveApiSettings } from '../services/visionApi';

export default function ApiSettingsModal({ isOpen, onClose, onSaved }) {
  const [settings, setSettings] = useState({
    provider: 'simulation',
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '',
    model: 'gpt-4o',
    temperature: 0.4,
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setSettings(getStoredApiSettings());
      setSavedSuccess(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleProviderChange = (provider) => {
    let newBaseUrl = settings.baseUrl;
    let newModel = settings.model;

    if (provider === 'openai') {
      newBaseUrl = 'https://api.openai.com/v1';
      newModel = 'gpt-4o';
    } else if (provider === 'claude') {
      newBaseUrl = 'https://api.anthropic.com/v1';
      newModel = 'claude-3-5-sonnet-20241022';
    } else if (provider === 'gemini') {
      newBaseUrl = 'https://generativelanguage.googleapis.com/v1beta';
      newModel = 'gemini-2.0-flash';
    } else if (provider === 'deepseek') {
      newBaseUrl = 'https://api.deepseek.com/v1';
      newModel = 'deepseek-chat';
    } else if (provider === 'simulation') {
      newBaseUrl = '';
      newModel = 'smart-simulation-v1';
    }

    setSettings({
      ...settings,
      provider,
      baseUrl: newBaseUrl,
      model: newModel
    });
  };

  const handleSave = () => {
    saveApiSettings(settings);
    setSavedSuccess(true);
    if (onSaved) onSaved(settings);
    setTimeout(() => {
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-xl rounded-3xl glass-panel border border-slate-700/80 shadow-2xl p-6 space-y-5">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Vision 视觉大模型接口配置</h3>
              <p className="text-xs text-slate-400">支持接入任意 Vision 多模态模型或使用内置免Key智能仿真</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Provider Switch Tabs */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">选择接口服务商 (Provider):</label>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
            {[
              { id: 'simulation', name: '智能仿真', badge: '开箱免Key' },
              { id: 'openai', name: 'OpenAI', badge: 'GPT-4o' },
              { id: 'claude', name: 'Claude', badge: '3.5 Sonnet' },
              { id: 'gemini', name: 'Gemini', badge: 'Flash / Pro' },
              { id: 'custom', name: '自定义/中转', badge: 'OneAPI/Ollama' },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => handleProviderChange(p.id)}
                className={`p-2.5 rounded-xl border text-left transition flex flex-col justify-between ${
                  settings.provider === p.id
                    ? 'bg-brand-950 border-brand-500 text-white ring-1 ring-brand-500/50 shadow-md'
                    : 'bg-slate-900/80 hover:bg-slate-800 border-slate-800 text-slate-400'
                }`}
              >
                <span className="text-xs font-bold truncate">{p.name}</span>
                <span className="text-[10px] text-slate-500 mt-0.5 truncate">{p.badge}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Fields */}
        {settings.provider === 'simulation' ? (
          <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 text-xs text-emerald-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-emerald-300">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>当前模式：内置免Key高精度智能仿真引擎</span>
            </div>
            <p className="text-slate-300 leading-relaxed">
              无需配置任何 API Key 或科学上网，系统将结合实时提取的图片特征、主色调、画幅比例与 7 大专业反推体系，毫秒级输出高质量绘图指令！
            </p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {/* API Key */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
                <span className="flex items-center gap-1">
                  <Key className="w-3.5 h-3.5 text-brand-400" /> API Key (密钥):
                </span>
                <span className="text-[10px] text-slate-500">仅保存在本地浏览器或私有服务</span>
              </label>
              <input
                type="password"
                value={settings.apiKey}
                onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
                placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
                className="w-full px-3.5 py-2 rounded-xl glass-input text-xs font-mono"
              />
            </div>

            {/* Base URL */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1">
                <Globe className="w-3.5 h-3.5 text-indigo-400" /> API Base URL (接口基址):
              </label>
              <input
                type="text"
                value={settings.baseUrl}
                onChange={(e) => setSettings({ ...settings, baseUrl: e.target.value })}
                placeholder="https://api.openai.com/v1"
                className="w-full px-3.5 py-2 rounded-xl glass-input text-xs font-mono"
              />
            </div>

            {/* Model Name & Temperature */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1">
                  <Cpu className="w-3.5 h-3.5 text-purple-400" /> 模型名称 (Model):
                </label>
                <input
                  type="text"
                  value={settings.model}
                  onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                  placeholder="gpt-4o / claude-3-5-sonnet / gemini-1.5-flash"
                  className="w-full px-3.5 py-2 rounded-xl glass-input text-xs font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">
                  创意发散度 (Temperature): {settings.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-brand-500 mt-2"
                />
              </div>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-lg shadow-brand-600/25"
          >
            {savedSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : null}
            <span>{savedSuccess ? '配置已保存' : '保存设置'}</span>
          </button>
        </div>

      </div>
    </div>
  );
}
