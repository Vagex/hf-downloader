import * as THREE from 'three';

export class ParticleSystem {
  constructor(scene) {
    this.scene = scene;

    // Teapot Steam Particles
    this.steamCount = 60;
    this.steamGeo = new THREE.BufferGeometry();
    this.steamPos = new Float32Array(this.steamCount * 3);
    this.steamVel = [];

    for (let i = 0; i < this.steamCount; i++) {
      this.steamPos[i * 3] = (Math.random() - 0.5) * 0.4;
      this.steamPos[i * 3 + 1] = Math.random() * 2;
      this.steamPos[i * 3 + 2] = (Math.random() - 0.5) * 0.4;
      this.steamVel.push({
        x: (Math.random() - 0.5) * 0.01,
        y: 0.02 + Math.random() * 0.02,
        z: (Math.random() - 0.5) * 0.01
      });
    }

    this.steamGeo.setAttribute('position', new THREE.BufferAttribute(this.steamPos, 3));
    this.steamMat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.25,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending
    });
    this.steamPoints = new THREE.Points(this.steamGeo, this.steamMat);
    this.steamPoints.position.set(0, 3.2, 0); // At teapot spout
    this.scene.add(this.steamPoints);

    // Floating Rose Petals Particles
    this.petalCount = 120;
    this.petalGeo = new THREE.BufferGeometry();
    this.petalPos = new Float32Array(this.petalCount * 3);
    this.petalRot = [];

    for (let i = 0; i < this.petalCount; i++) {
      this.petalPos[i * 3] = (Math.random() - 0.5) * 50;
      this.petalPos[i * 3 + 1] = Math.random() * 20 + 2;
      this.petalPos[i * 3 + 2] = (Math.random() - 0.5) * 50;
      this.petalRot.push({
        speedX: (Math.random() - 0.5) * 0.02,
        speedY: (Math.random() - 0.5) * 0.03,
        fallSpeed: 0.01 + Math.random() * 0.02
      });
    }

    this.petalGeo.setAttribute('position', new THREE.BufferAttribute(this.petalPos, 3));
    this.petalMat = new THREE.PointsMaterial({
      color: 0xf43f5e,
      size: 0.35,
      transparent: true,
      opacity: 0.75,
      blending: THREE.NormalBlending
    });
    this.petalPoints = new THREE.Points(this.petalGeo, this.petalMat);
    this.scene.add(this.petalPoints);

    // Magic Sparkles (around mushrooms & items)
    this.sparkleCount = 150;
    this.sparkleGeo = new THREE.BufferGeometry();
    this.sparklePos = new Float32Array(this.sparkleCount * 3);

    for (let i = 0; i < this.sparkleCount; i++) {
      this.sparklePos[i * 3] = (Math.random() - 0.5) * 60;
      this.sparklePos[i * 3 + 1] = Math.random() * 10;
      this.sparklePos[i * 3 + 2] = (Math.random() - 0.5) * 60;
    }

    this.sparkleGeo.setAttribute('position', new THREE.BufferAttribute(this.sparklePos, 3));
    this.sparkleMat = new THREE.PointsMaterial({
      color: 0xfde047,
      size: 0.2,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending
    });
    this.sparklePoints = new THREE.Points(this.sparkleGeo, this.sparkleMat);
    this.scene.add(this.sparklePoints);
  }

  setTeapotPosition(pos) {
    if (this.steamPoints) {
      this.steamPoints.position.set(pos.x + 0.6, pos.y + 1.2, pos.z);
    }
  }

  update(delta) {
    // 1. Update Steam
    const steamPosAttr = this.steamGeo.attributes.position;
    for (let i = 0; i < this.steamCount; i++) {
      let y = steamPosAttr.getY(i) + this.steamVel[i].y;
      let x = steamPosAttr.getX(i) + this.steamVel[i].x;
      let z = steamPosAttr.getZ(i) + this.steamVel[i].z;

      if (y > 3.0) {
        y = 0;
        x = (Math.random() - 0.5) * 0.2;
        z = (Math.random() - 0.5) * 0.2;
      }
      steamPosAttr.setXYZ(i, x, y, z);
    }
    steamPosAttr.needsUpdate = true;

    // 2. Update Petals
    const petalPosAttr = this.petalGeo.attributes.position;
    for (let i = 0; i < this.petalCount; i++) {
      let y = petalPosAttr.getY(i) - this.petalRot[i].fallSpeed;
      let x = petalPosAttr.getX(i) + Math.sin(Date.now() * 0.001 + i) * 0.01;
      let z = petalPosAttr.getZ(i) + Math.cos(Date.now() * 0.001 + i) * 0.01;

      if (y < 0) {
        y = 20 + Math.random() * 5;
        x = (Math.random() - 0.5) * 50;
        z = (Math.random() - 0.5) * 50;
      }
      petalPosAttr.setXYZ(i, x, y, z);
    }
    petalPosAttr.needsUpdate = true;

    // 3. Shimmer Sparkles
    this.sparkleMat.opacity = 0.5 + Math.sin(Date.now() * 0.004) * 0.4;
  }
}
