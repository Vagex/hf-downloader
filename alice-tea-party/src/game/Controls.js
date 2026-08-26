import * as THREE from 'three';

export class ThirdPersonControls {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;

    // Movement state
    this.keys = {
      forward: false,
      backward: false,
      left: false,
      right: false,
      jump: false,
      sprint: false
    };

    // Virtual Joystick values (-1 to 1)
    this.joystickVector = { x: 0, y: 0 };

    // Camera orbit parameters
    this.pitch = 0.35; // Vertical angle
    this.yaw = 0;      // Horizontal angle
    this.distance = 9; // Camera distance from Alice
    this.minDistance = 3;
    this.maxDistance = 22;

    this.isDragging = false;
    this.previousMousePos = { x: 0, y: 0 };

    this.initListeners();
  }

  initListeners() {
    // Keydown / Keyup
    window.addEventListener('keydown', (e) => this.handleKey(e.code, true));
    window.addEventListener('keyup', (e) => this.handleKey(e.code, false));

    // Mouse drag orbit
    this.domElement.addEventListener('mousedown', (e) => {
      if (e.target.closest('.hud-container')) return; // Ignore if clicking HUD
      this.isDragging = true;
      this.previousMousePos = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const deltaX = e.clientX - this.previousMousePos.x;
      const deltaY = e.clientY - this.previousMousePos.y;

      this.yaw -= deltaX * 0.006;
      this.pitch = Math.max(0.05, Math.min(Math.PI / 2 - 0.05, this.pitch + deltaY * 0.006));

      this.previousMousePos = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    // Zoom wheel
    this.domElement.addEventListener('wheel', (e) => {
      this.distance = Math.max(this.minDistance, Math.min(this.maxDistance, this.distance + e.deltaY * 0.01));
    }, { passive: true });

    // Touch orbit for non-joystick screen areas
    let touchStartPos = { x: 0, y: 0 };
    this.domElement.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1 && !e.target.closest('#touch-controls')) {
        touchStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });

    this.domElement.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1 && !e.target.closest('#touch-controls')) {
        const deltaX = e.touches[0].clientX - touchStartPos.x;
        const deltaY = e.touches[0].clientY - touchStartPos.y;
        this.yaw -= deltaX * 0.008;
        this.pitch = Math.max(0.05, Math.min(Math.PI / 2 - 0.05, this.pitch + deltaY * 0.008));
        touchStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });
  }

  handleKey(code, isDown) {
    switch (code) {
      case 'KeyW': case 'ArrowUp': this.keys.forward = isDown; break;
      case 'KeyS': case 'ArrowDown': this.keys.backward = isDown; break;
      case 'KeyA': case 'ArrowLeft': this.keys.left = isDown; break;
      case 'KeyD': case 'ArrowRight': this.keys.right = isDown; break;
      case 'Space': this.keys.jump = isDown; break;
      case 'ShiftLeft': case 'ShiftRight': this.keys.sprint = isDown; break;
    }
  }

  setJoystickVector(x, y) {
    this.joystickVector.x = x;
    this.joystickVector.y = y;
  }

  updateCamera(targetPos, aliceScale = 1.0) {
    // Dynamic distance based on Alice scale
    const targetDistance = this.distance * (aliceScale < 0.5 ? 0.6 : (aliceScale > 1.8 ? 1.5 : 1.0));
    const targetHeightOffset = 1.8 * aliceScale;

    const offset = new THREE.Vector3(
      targetDistance * Math.sin(this.yaw) * Math.cos(this.pitch),
      targetDistance * Math.sin(this.pitch) + targetHeightOffset,
      targetDistance * Math.cos(this.yaw) * Math.cos(this.pitch)
    );

    const cameraPos = targetPos.clone().add(offset);
    
    // Smooth camera interpolation
    this.camera.position.lerp(cameraPos, 0.15);
    this.camera.lookAt(targetPos.x, targetPos.y + targetHeightOffset * 0.8, targetPos.z);
  }

  getMovementVector() {
    let moveZ = 0;
    let moveX = 0;

    if (this.keys.forward) moveZ -= 1;
    if (this.keys.backward) moveZ += 1;
    if (this.keys.left) moveX -= 1;
    if (this.keys.right) moveX += 1;

    // Combine keyboard + virtual joystick
    if (this.joystickVector.y !== 0) moveZ = this.joystickVector.y;
    if (this.joystickVector.x !== 0) moveX = this.joystickVector.x;

    const moveDir = new THREE.Vector3(moveX, 0, moveZ);
    if (moveDir.lengthSq() > 0.01) {
      moveDir.normalize();
      // Rotate movement relative to camera yaw angle
      moveDir.applyAxisAngle(new THREE.Vector3(0, 1, 0), this.yaw);
    }
    return moveDir;
  }
}
