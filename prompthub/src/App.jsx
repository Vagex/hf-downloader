import React, { useState, useEffect, useMemo } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import PromptCard from './components/PromptCard';
import PromptModal from './components/PromptModal';
import VariableInterpolationModal from './components/VariableInterpolationModal';
import ExportImportModal from './components/ExportImportModal';
import { initialPrompts } from './data/initialPrompts';
import { Sparkles, Plus, Layers, AlertCircle, CheckCircle2, Info } from 'lucide-react';

export default function App() {
  // State
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('prompthub_dark') === 'true' || 
      window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'compact'
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all'); // 'all' | 'video' | 'image' | 'text'
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedTag, setSelectedTag] = useState(null);
  const [selectedRatio, setSelectedRatio] = useState(null);
  const [onlyPinned, setOnlyPinned] = useState(false);

  // Modals
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [interpolatingPrompt, setInterpolatingPrompt] = useState(null);
  const [isExportImportOpen, setIsExportImportOpen] = useState(false);

  // Toasts
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => {
      setToast(prev => (prev?.message === message ? null : prev));
    }, 3000);
  };

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('prompthub_dark', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('prompthub_dark', 'false');
    }
  }, [darkMode]);

  // Load prompts from API or localStorage
  const fetchPrompts = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/prompts');
      const json = await res.json();
      if (json.success && json.data && json.data.length > 0) {
        setPrompts(json.data);
      } else {
        // Fallback or seed with initialPrompts
        const local = localStorage.getItem('prompthub_offline_data');
        if (local) {
          const parsed = JSON.parse(local);
          setPrompts(parsed);
        } else {
          // Initialize with curated seed prompts
          setPrompts(initialPrompts);
          // Sync to backend
          try {
            await fetch('/api/import', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ prompts: initialPrompts, mode: 'replace' })
            });
          } catch (e) {}
        }
      }
    } catch (err) {
      console.warn('Backend API unavailable, using local store:', err);
      const local = localStorage.getItem('prompthub_offline_data');
      if (local) {
        setPrompts(JSON.parse(local));
      } else {
        setPrompts(initialPrompts);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  // Save changes locally and to backend
  const handleSavePrompt = async (formData) => {
    if (editingPrompt) {
      // Update
      const updatedPrompt = { ...editingPrompt, ...formData };
      try {
        await fetch(`/api/prompts/${editingPrompt.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedPrompt)
        });
      } catch (e) {}

      setPrompts(prev => {
        const next = prev.map(p => p.id === editingPrompt.id ? updatedPrompt : p);
        localStorage.setItem('prompthub_offline_data', JSON.stringify(next));
        return next;
      });
      showToast('提示词已成功更新', 'success');
    } else {
      // Create new
      const newPrompt = {
        ...formData,
        id: `prompt-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        createdAt: new Date().toISOString()
      };
      try {
        await fetch('/api/prompts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newPrompt)
        });
      } catch (e) {}

      setPrompts(prev => {
        const next = [newPrompt, ...prev];
        localStorage.setItem('prompthub_offline_data', JSON.stringify(next));
        return next;
      });
      showToast('已添加新提示词到收藏库', 'success');
    }
    setEditingPrompt(null);
  };

  // Delete Prompt
  const handleDeletePrompt = async (id) => {
    if (!window.confirm('确定要删除这条提示词吗？此操作无法撤销。')) return;

    try {
      await fetch(`/api/prompts/${id}`, { method: 'DELETE' });
    } catch (e) {}

    setPrompts(prev => {
      const next = prev.filter(p => p.id !== id);
      localStorage.setItem('prompthub_offline_data', JSON.stringify(next));
      return next;
    });
    showToast('已删除该提示词', 'info');
  };

  // Toggle Pin
  const handleTogglePin = async (id) => {
    const target = prompts.find(p => p.id === id);
    if (!target) return;
    const updated = { ...target, isPinned: !target.isPinned };

    try {
      await fetch(`/api/prompts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });
    } catch (e) {}

    setPrompts(prev => {
      const next = prev.map(p => p.id === id ? updated : p);
      localStorage.setItem('prompthub_offline_data', JSON.stringify(next));
      return next;
    });
    showToast(updated.isPinned ? '已加入置顶精选' : '已取消置顶', 'info');
  };

  // Filtered & Searched Prompts
  const filteredPrompts = useMemo(() => {
    return prompts.filter(p => {
      // 1. Search Query match
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const titleMatch = (p.title || '').toLowerCase().includes(q);
        const promptMatch = (p.prompt || '').toLowerCase().includes(q);
        const subcategoryMatch = (p.subcategory || '').toLowerCase().includes(q);
        const negativeMatch = (p.negativePrompt || '').toLowerCase().includes(q);
        const notesMatch = (p.notes || '').toLowerCase().includes(q);
        const tagsMatch = Array.isArray(p.tags) && p.tags.some(t => t.toLowerCase().includes(q));
        if (!titleMatch && !promptMatch && !subcategoryMatch && !negativeMatch && !notesMatch && !tagsMatch) {
          return false;
        }
      }

      // 2. Category match
      if (activeCategory !== 'all' && p.category !== activeCategory) {
        return false;
      }

      // 3. Pinned only
      if (onlyPinned && !p.isPinned) {
        return false;
      }

      // 4. Model / Subcategory match
      if (selectedModel && !(p.subcategory || '').toLowerCase().includes(selectedModel.toLowerCase())) {
        return false;
      }

      // 5. Tag match
      if (selectedTag && (!Array.isArray(p.tags) || !p.tags.includes(selectedTag))) {
        return false;
      }

      // 6. Ratio match
      if (selectedRatio && p.aspectRatio !== selectedRatio) {
        return false;
      }

      return true;
    }).sort((a, b) => {
      // Pinned first, then by date
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
    });
  }, [prompts, searchQuery, activeCategory, onlyPinned, selectedModel, selectedTag, selectedRatio]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 transition-colors">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-20 right-6 z-50 animate-bounce transition-all">
          <div className={`flex items-center gap-2.5 px-4 py-3 rounded-2xl shadow-xl border text-sm font-medium ${
            toast.type === 'success' 
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/90 dark:text-emerald-200 dark:border-emerald-800'
              : toast.type === 'error'
              ? 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/90 dark:text-red-200 dark:border-red-800'
              : 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/90 dark:text-blue-200 dark:border-blue-800'
          }`}>
            {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> :
             toast.type === 'error' ? <AlertCircle className="w-4 h-4 text-red-500" /> :
             <Info className="w-4 h-4 text-blue-500" />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <Header
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        viewMode={viewMode}
        setViewMode={setViewMode}
        onOpenCreate={() => { setEditingPrompt(null); setIsPromptModalOpen(true); }}
        onOpenExportImport={() => setIsExportImportOpen(true)}
        activeCategory={activeCategory}
        setActiveCategory={setActiveCategory}
        toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
        totalCount={prompts.length}
      />

      {/* Main Layout Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full flex gap-6 py-6">
        {/* Sidebar */}
        <Sidebar
          prompts={prompts}
          activeCategory={activeCategory}
          setActiveCategory={setActiveCategory}
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
          selectedTag={selectedTag}
          setSelectedTag={setSelectedTag}
          selectedRatio={selectedRatio}
          setSelectedRatio={setSelectedRatio}
          onlyPinned={onlyPinned}
          setOnlyPinned={setOnlyPinned}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />

        {/* Content Area */}
        <main className="flex-1 min-w-0">
          {/* Active Filter Chips */}
          {(selectedModel || selectedTag || selectedRatio || onlyPinned || searchQuery) && (
            <div className="mb-4 flex flex-wrap items-center gap-2 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 text-xs">
              <span className="text-slate-400 font-medium">当前筛选:</span>
              
              {onlyPinned && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 rounded-lg">
                  ⭐ 仅看置顶
                  <button onClick={() => setOnlyPinned(false)}>✕</button>
                </span>
              )}

              {selectedModel && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200 rounded-lg font-medium">
                  🔥 引擎: {selectedModel}
                  <button onClick={() => setSelectedModel(null)}>✕</button>
                </span>
              )}

              {selectedTag && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 rounded-lg">
                  #{selectedTag}
                  <button onClick={() => setSelectedTag(null)}>✕</button>
                </span>
              )}

              {selectedRatio && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 rounded-lg">
                  比例: {selectedRatio}
                  <button onClick={() => setSelectedRatio(null)}>✕</button>
                </span>
              )}

              {searchQuery && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 rounded-lg">
                  搜索: "{searchQuery}"
                  <button onClick={() => setSearchQuery('')}>✕</button>
                </span>
              )}

              <button
                onClick={() => {
                  setSelectedModel(null);
                  setSelectedTag(null);
                  setSelectedRatio(null);
                  setOnlyPinned(false);
                  setSearchQuery('');
                }}
                className="ml-auto text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                重置所有筛选
              </button>
            </div>
          )}

          {/* Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-64 rounded-2xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
              ))}
            </div>
          ) : filteredPrompts.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-12 text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-500 mx-auto flex items-center justify-center">
                <Layers className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  未找到符合条件的提示词
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  尝试清空搜索条件，或点击右上角录入新的优秀 Prompt
                </p>
              </div>
              <button
                onClick={() => { setEditingPrompt(null); setIsPromptModalOpen(true); }}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition"
              >
                <Plus className="w-4 h-4" />
                立即收藏一条
              </button>
            </div>
          ) : (
            <div className={`grid gap-5 ${
              viewMode === 'compact' 
                ? 'grid-cols-1' 
                : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2'
            }`}>
              {filteredPrompts.map(p => (
                <PromptCard
                  key={p.id}
                  prompt={p}
                  viewMode={viewMode}
                  onInterpolate={(item) => setInterpolatingPrompt(item)}
                  onEdit={(item) => { setEditingPrompt(item); setIsPromptModalOpen(true); }}
                  onDelete={handleDeletePrompt}
                  onTogglePin={handleTogglePin}
                  onToast={showToast}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      <PromptModal
        isOpen={isPromptModalOpen}
        onClose={() => { setIsPromptModalOpen(false); setEditingPrompt(null); }}
        onSave={handleSavePrompt}
        editingPrompt={editingPrompt}
        onToast={showToast}
      />

      <VariableInterpolationModal
        isOpen={!!interpolatingPrompt}
        promptData={interpolatingPrompt}
        onClose={() => setInterpolatingPrompt(null)}
        onToast={showToast}
      />

      <ExportImportModal
        isOpen={isExportImportOpen}
        onClose={() => setIsExportImportOpen(false)}
        prompts={prompts}
        onImportSuccess={fetchPrompts}
        onToast={showToast}
      />
    </div>
  );
}
