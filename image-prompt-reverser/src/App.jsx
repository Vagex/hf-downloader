import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CategorySelector from './components/CategorySelector';
import ImageUploader from './components/ImageUploader';
import ParameterPanel from './components/ParameterPanel';
import AnalysisResult from './components/AnalysisResult';
import ApiSettingsModal from './components/ApiSettingsModal';
import HistoryModal from './components/HistoryModal';
import PresetGalleryModal from './components/PresetGalleryModal';
import { CATEGORIES } from './services/categories';
import { reverseImageToPrompt, getStoredApiSettings } from './services/visionApi';
import { SAMPLE_PRESETS } from './services/samplePresets';
import { extractImageInfo } from './services/colorExtractor';

const HISTORY_KEY = 'image_reverser_history_v1';

export default function App() {
  const [selectedCategoryId, setSelectedCategoryId] = useState('general');
  const [selectedEngineId, setSelectedEngineId] = useState('midjourney');
  const [imageDataUrl, setImageDataUrl] = useState(null);
  const [imageInfo, setImageInfo] = useState(null);
  const [userNotes, setUserNotes] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Modals state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);

  // API settings state
  const [apiSettings, setApiSettings] = useState(() => getStoredApiSettings());

  // History state
  const [historyList, setHistoryList] = useState(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Sync category default engine
  const handleSelectCategory = (catId) => {
    setSelectedCategoryId(catId);
    const cat = CATEGORIES.find(c => c.id === catId);
    if (cat && cat.defaultEngine) {
      setSelectedEngineId(cat.defaultEngine);
    }
  };

  const handleImageLoaded = (dataUrl, info) => {
    setImageDataUrl(dataUrl);
    setImageInfo(info);
    setAnalysisResult(null);
  };

  const handleClearImage = () => {
    setImageDataUrl(null);
    setImageInfo(null);
    setAnalysisResult(null);
  };

  // Load preset sample image & preset result
  const handleLoadSample = async () => {
    const sample = SAMPLE_PRESETS.find(p => p.categoryId === selectedCategoryId) || SAMPLE_PRESETS[0];
    setImageDataUrl(sample.image);
    const info = await extractImageInfo(sample.image);
    setImageInfo(info);
    setAnalysisResult(sample.result);
  };

  const handleSelectPresetFromGallery = async (preset) => {
    setSelectedCategoryId(preset.categoryId);
    const cat = CATEGORIES.find(c => c.id === preset.categoryId);
    if (cat?.defaultEngine) setSelectedEngineId(cat.defaultEngine);

    setImageDataUrl(preset.image);
    const info = await extractImageInfo(preset.image);
    setImageInfo(info);
    setAnalysisResult(preset.result);
  };

  const handleSelectHistoryItem = (item) => {
    if (item.categoryId) setSelectedCategoryId(item.categoryId);
    if (item.image) setImageDataUrl(item.image);
    if (item.imageInfo) setImageInfo(item.imageInfo);
    if (item.result) setAnalysisResult(item.result);
  };

  const handleClearHistory = () => {
    if (window.confirm('确定要清空全部反推历史记录吗？')) {
      setHistoryList([]);
      localStorage.removeItem(HISTORY_KEY);
    }
  };

  // Trigger Reverse Analysis
  const handleStartReverse = async () => {
    if (!imageDataUrl) return;

    setIsLoading(true);
    try {
      const result = await reverseImageToPrompt({
        imageDataUrl,
        imageInfo,
        categoryId: selectedCategoryId,
        engineId: selectedEngineId,
        userNotes
      });

      setAnalysisResult(result);

      // Save to History
      const category = CATEGORIES.find(c => c.id === selectedCategoryId);
      const newHistoryItem = {
        id: 'hist_' + Date.now(),
        timestamp: Date.now(),
        categoryId: selectedCategoryId,
        categoryName: category?.name || '通用模式',
        image: imageDataUrl,
        imageInfo,
        result
      };

      const updatedHistory = [newHistoryItem, ...historyList.slice(0, 49)];
      setHistoryList(updatedHistory);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updatedHistory));
    } catch (err) {
      alert('反推执行出错: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const currentCategory = CATEGORIES.find(c => c.id === selectedCategoryId) || CATEGORIES[0];

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-brand-500 selection:text-white">
      
      {/* Top Header */}
      <Header
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenGallery={() => setIsGalleryOpen(true)}
        historyCount={historyList.length}
        apiProvider={apiSettings.provider}
      />

      {/* Main Workspace Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Step 1: Category Selector */}
        <section className="glass-panel p-5 rounded-3xl shadow-xl">
          <CategorySelector
            selectedCategoryId={selectedCategoryId}
            onSelectCategory={handleSelectCategory}
          />
        </section>

        {/* Step 2 & 3: Upload Image & Parameter Panel */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: Image Uploader */}
          <div className="lg:col-span-6 glass-panel p-5 rounded-3xl shadow-xl flex flex-col justify-between">
            <ImageUploader
              imageSrc={imageDataUrl}
              imageInfo={imageInfo}
              onImageLoaded={handleImageLoaded}
              onClearImage={handleClearImage}
              onLoadSample={handleLoadSample}
              selectedCategoryId={selectedCategoryId}
            />
          </div>

          {/* Right Column: Engine & Trigger */}
          <div className="lg:col-span-6 glass-panel p-5 rounded-3xl shadow-xl flex flex-col justify-between">
            <ParameterPanel
              selectedEngineId={selectedEngineId}
              onSelectEngine={setSelectedEngineId}
              userNotes={userNotes}
              onChangeUserNotes={setUserNotes}
              onStartReverse={handleStartReverse}
              isLoading={isLoading}
              hasImage={Boolean(imageDataUrl)}
            />
          </div>

        </section>

        {/* Analysis Results Display */}
        {analysisResult && (
          <section className="glass-panel p-5 sm:p-6 rounded-3xl shadow-2xl">
            <AnalysisResult
              result={analysisResult}
              category={currentCategory}
              selectedEngineId={selectedEngineId}
              imageInfo={imageInfo}
            />
          </section>
        )}

      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AI 图像反向工程与精准 Prompt 工作台 · 支持 7 大全要素反推模式</span>
          <span>纯私有化运行 · 适配 Midjourney / FLUX / SD / 可灵</span>
        </div>
      </footer>

      {/* Modals */}
      <ApiSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaved={(newSettings) => setApiSettings(newSettings)}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        historyList={historyList}
        onSelectHistoryItem={handleSelectHistoryItem}
        onClearHistory={handleClearHistory}
      />

      <PresetGalleryModal
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
        onSelectPreset={handleSelectPresetFromGallery}
      />

    </div>
  );
}
