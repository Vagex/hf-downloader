import * as THREE from 'three';

export class CheshireCatEntity {
  constructor(scene, position) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.group.position.copy(position);
    this.scene.add(this.group);

    this.createCat();
  }

  createCat() {
    this.catMat = new THREE.MeshStandardMaterial({
      color: 0xc084fc,
      roughness: 0.3,
      transparent: true,
      opacity: 0.85
    });

    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const grinMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

    // Head
    const headGeo = new THREE.SphereGeometry(0.7, 16, 16);
    this.head = new THREE.Mesh(headGeo, this.catMat);
    this.group.add(this.head);

    // Cat Ears
    const earGeo = new THREE.ConeGeometry(0.2, 0.4, 4);
    const earL = new THREE.Mesh(earGeo, this.catMat);
    earL.position.set(-0.35, 0.6, 0);
    earL.rotation.z = -0.2;
    const earR = new THREE.Mesh(earGeo, this.catMat);
    earR.position.set(0.35, 0.6, 0);
    earR.rotation.z = 0.2;
    this.group.add(earL, earR);

    // Glowing Cat Eyes
    const eyeGeo = new THREE.SphereGeometry(0.12, 12, 12);
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(0.25, 0.15, 0.58);
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(-0.25, 0.15, 0.58);
    this.group.add(leftEye, rightEye);

    // Iconic Wide Grin (Torus Segment)
    const grinGeo = new THREE.TorusGeometry(0.35, 0.06, 8, 16, Math.PI);
    const grin = new THREE.Mesh(grinGeo, grinMat);
    grin.position.set(0, -0.15, 0.55);
    grin.rotation.x = Math.PI;
    this.group.add(grin);

    // Fluffy Tail behind
    const tailGeo = new THREE.TorusGeometry(0.5, 0.1, 8, 16, Math.PI * 1.2);
    this.tail = new THREE.Mesh(tailGeo, this.catMat);
    this.tail.position.set(0, -0.2, -0.6);
    this.group.add(this.tail);
  }

  update(delta) {
    // Gentle floating bob & tail sway
    const time = Date.now() * 0.002;
    this.group.position.y = 2.5 + Math.sin(time) * 0.25;
    this.group.rotation.y = Math.sin(time * 0.8) * 0.2;

    if (this.tail) {
      this.tail.rotation.z = Math.sin(time * 1.5) * 0.3;
    }

    // Invisibility pulse alpha modulation
    if (this.catMat) {
      this.catMat.opacity = 0.4 + Math.sin(time * 1.2) * 0.45;
    }
  }
}
