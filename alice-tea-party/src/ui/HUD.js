export class HUDController {
  constructor(questMgr) {
    this.questMgr = questMgr;

    // DOM Elements
    this.loadingScreen = document.getElementById('loading-screen');
    this.loadingBar = document.getElementById('loading-bar');
    this.startBtn = document.getElementById('start-btn');
    this.hudOverlay = document.getElementById('hud-overlay');

    this.sizeLabel = document.getElementById('size-label');
    this.actionPrompt = document.getElementById('action-prompt');
    this.actionText = document.getElementById('action-text');

    this.countSugar = document.getElementById('count-sugar');
    this.countMacaron = document.getElementById('count-macaron');
    this.countTea = document.getElementById('count-tea');
    this.countRoses = document.getElementById('count-roses');
    this.countKeys = document.getElementById('count-keys');

    this.questTitle = document.getElementById('current-quest-title');
    this.questDesc = document.getElementById('current-quest-desc');
    this.questProgressFill = document.getElementById('quest-progress-fill');

    this.minimapCanvas = document.getElementById('minimap-canvas');
    this.minimapCtx = this.minimapCanvas ? this.minimapCanvas.getContext('2d') : null;

    this.victoryModal = document.getElementById('victory-modal');
  }

  showStartButton() {
    this.loadingBar.style.width = '100%';
    this.startBtn.classList.remove('hidden');
  }

  hideLoadingScreen() {
    this.loadingScreen.classList.add('fade-out');
    setTimeout(() => {
      this.loadingScreen.style.display = 'none';
      this.hudOverlay.classList.remove('hidden');
    }, 600);
  }

  updateSizeBadge(scale) {
    if (scale < 0.5) {
      this.sizeLabel.textContent = '微观形态 (0.3x)';
    } else if (scale > 1.8) {
      this.sizeLabel.textContent = '巨型形态 (2.2x)';
    } else {
      this.sizeLabel.textContent = '标准形态 (1.0x)';
    }
  }

  setActionPrompt(text) {
    if (text) {
      this.actionText.textContent = text;
      this.actionPrompt.classList.remove('hidden');
    } else {
      this.actionPrompt.classList.add('hidden');
    }
  }

  updateInventoryCounts(inv) {
    this.countSugar.textContent = `${inv.sugar}/3`;
    this.countMacaron.textContent = `${inv.macaron}/3`;
    this.countTea.textContent = `${inv.tea}/2`;
    this.countRoses.textContent = `${inv.rosesPainted}/4`;
    this.countKeys.textContent = `${inv.keys}/1`;
  }

  updateActiveQuest(title, desc, progressPercent) {
    this.questTitle.textContent = title;
    this.questDesc.textContent = desc;
    this.questProgressFill.style.width = `${progressPercent}%`;
  }

  showVictoryModal() {
    this.victoryModal.classList.remove('hidden');
  }

  renderMinimap(alicePos, cardGuards) {
    if (!this.minimapCtx) return;
    const ctx = this.minimapCtx;
    const w = this.minimapCanvas.width;
    const h = this.minimapCanvas.height;
    const cx = w / 2;
    const cy = h / 2;

    // Clear
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, cx - 2, 0, Math.PI * 2);
    ctx.stroke();

    // Map Scale factor (world -50 to 50 maps to canvas 0 to 130)
    const mapScale = 1.1;

    // Tea Table Center
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();

    // Card Guards
    ctx.fillStyle = '#f43f5e';
    cardGuards.forEach(g => {
      const gx = cx + g.group.position.x * mapScale;
      const gz = cy + g.group.position.z * mapScale;
      ctx.beginPath();
      ctx.arc(gx, gz, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Alice Position (Cyan Dot)
    const ax = cx + alicePos.x * mapScale;
    const az = cy + alicePos.z * mapScale;
    ctx.fillStyle = '#38bdf8';
    ctx.beginPath();
    ctx.arc(ax, az, 4, 0, Math.PI * 2);
    ctx.fill();

    // Alice Direction Pointer
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(ax, az);
    ctx.lineTo(ax, az - 6);
    ctx.stroke();
  }
}
