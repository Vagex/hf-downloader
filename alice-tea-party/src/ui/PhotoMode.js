export class PhotoModeStudio {
  constructor(renderer, scene, camera) {
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;

    this.overlay = document.getElementById('photo-overlay');
    this.hud = document.getElementById('hud-overlay');

    this.currentFilter = 'none';

    this.initListeners();
  }

  initListeners() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.setFilter(btn.dataset.filter);
      });
    });

    document.getElementById('take-snapshot-btn').addEventListener('click', () => {
      this.takeSnapshot();
    });

    document.getElementById('exit-photo-btn').addEventListener('click', () => {
      this.exitPhotoMode();
    });
  }

  enterPhotoMode() {
    this.overlay.classList.remove('hidden');
    this.hud.style.opacity = '0';
    this.hud.style.pointerEvents = 'none';
  }

  exitPhotoMode() {
    this.overlay.classList.add('hidden');
    this.hud.style.opacity = '1';
    this.hud.style.pointerEvents = 'auto';
    this.setFilter('none');
  }

  setFilter(filter) {
    this.currentFilter = filter;
    const canvas = this.renderer.domElement;

    switch (filter) {
      case 'dreamy':
        canvas.style.filter = 'contrast(1.1) saturate(1.3) hue-rotate(-15deg)';
        break;
      case 'vintage':
        canvas.style.filter = 'sepia(0.4) contrast(1.1) brightness(0.95)';
        break;
      case 'golden':
        canvas.style.filter = 'sepia(0.25) saturate(1.4) brightness(1.1)';
        break;
      case 'cyber':
        canvas.style.filter = 'contrast(1.35) saturate(1.6) hue-rotate(180deg)';
        break;
      default:
        canvas.style.filter = 'none';
        break;
    }
  }

  takeSnapshot() {
    // Render frame
    this.renderer.render(this.scene, this.camera);

    const dataUrl = this.renderer.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `Alice_Tea_Party_Wonderland_${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  }
}
