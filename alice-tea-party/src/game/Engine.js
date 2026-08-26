import * as THREE from 'three';

export class GraphicsEngine {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    
    // Scene & Fog
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x181028); // Whimsical twilight purple
    this.scene.fog = new THREE.FogExp2(0x181028, 0.012);

    // Camera
    this.camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      200
    );
    this.camera.position.set(0, 8, 16);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    
    this.container.appendChild(this.renderer.domElement);

    // Lights
    this.setupLighting();

    // Resize Listener
    window.addEventListener('resize', () => this.onWindowResize());
  }

  setupLighting() {
    // Soft Ambient Light
    const ambientLight = new THREE.AmbientLight(0xd8b4fe, 0.75); // Lilac pastel ambient
    this.scene.add(ambientLight);

    // Main Sunlight (Warm Gold)
    const dirLight = new THREE.DirectionalLight(0xffedd5, 1.4);
    dirLight.position.set(25, 45, 20);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 1;
    dirLight.shadow.camera.far = 120;
    
    const d = 50;
    dirLight.shadow.camera.left = -d;
    dirLight.shadow.camera.right = d;
    dirLight.shadow.camera.top = d;
    dirLight.shadow.camera.bottom = -d;
    dirLight.shadow.bias = -0.0005;

    this.scene.add(dirLight);

    // Secondary Accent Light (Magenta/Pink glow from tea table)
    const pointLight = new THREE.PointLight(0xf43f5e, 1.8, 40);
    pointLight.position.set(0, 8, 0);
    this.scene.add(pointLight);

    // Blue Sky Fill Light
    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.4);
    fillLight.position.set(-20, 20, -20);
    this.scene.add(fillLight);
  }

  onWindowResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }
}
