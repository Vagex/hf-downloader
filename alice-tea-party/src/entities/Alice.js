import * as THREE from 'three';
import { audioManager } from '../game/Audio.js';

export class AliceCharacter {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Alice Attributes
    this.scale = 1.0;
    this.targetScale = 1.0;
    this.velocityY = 0;
    this.isGrounded = true;
    this.walkAnimTime = 0;

    // Dress Color & Hat State
    this.dressColor = 0x3b82f6; // Classic blue
    this.activeHatType = 'bow';

    this.createModel();
  }

  createModel() {
    // Clear previous if rebuilding
    while (this.group.children.length > 0) {
      this.group.remove(this.group.children[0]);
    }

    this.meshGroup = new THREE.Group();
    this.group.add(this.meshGroup);

    const dressMat = new THREE.MeshStandardMaterial({ color: this.dressColor, roughness: 0.5 });
    const apronMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xffdfd3, roughness: 0.7 });
    const hairMat = new THREE.MeshStandardMaterial({ color: 0xfde047, roughness: 0.4 });
    const shoeMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.2 });
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x1e3a8a });

    // Head
    const headGeo = new THREE.SphereGeometry(0.35, 16, 16);
    this.head = new THREE.Mesh(headGeo, skinMat);
    this.head.position.y = 1.6;
    this.head.castShadow = true;
    this.meshGroup.add(this.head);

    // Eyes
    const eyeGeo = new THREE.SphereGeometry(0.05, 8, 8);
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(0.12, 1.65, 0.3);
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(-0.12, 1.65, 0.3);
    this.meshGroup.add(leftEye, rightEye);

    // Hair
    const hairGeo = new THREE.ConeGeometry(0.45, 0.7, 16);
    const hair = new THREE.Mesh(hairGeo, hairMat);
    hair.position.set(0, 1.75, -0.05);
    hair.rotation.x = -0.3;
    this.meshGroup.add(hair);

    // Torso / Dress
    const torsoGeo = new THREE.CylinderGeometry(0.2, 0.3, 0.6, 12);
    const torso = new THREE.Mesh(torsoGeo, dressMat);
    torso.position.y = 1.1;
    torso.castShadow = true;
    this.meshGroup.add(torso);

    // Apron Overlay
    const apronGeo = new THREE.BoxGeometry(0.25, 0.4, 0.05);
    const apron = new THREE.Mesh(apronGeo, apronMat);
    apron.position.set(0, 1.05, 0.16);
    this.meshGroup.add(apron);

    // Dress Skirt (Cone shape)
    const skirtGeo = new THREE.ConeGeometry(0.65, 0.7, 16, 1, true);
    const skirt = new THREE.Mesh(skirtGeo, dressMat);
    skirt.position.y = 0.7;
    skirt.rotation.x = Math.PI;
    skirt.castShadow = true;
    this.meshGroup.add(skirt);

    // Arms
    const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.5, 8);
    this.leftArm = new THREE.Mesh(armGeo, skinMat);
    this.leftArm.position.set(0.32, 1.1, 0);
    this.rightArm = new THREE.Mesh(armGeo, skinMat);
    this.rightArm.position.set(-0.32, 1.1, 0);
    this.meshGroup.add(this.leftArm, this.rightArm);

    // Legs
    const legGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.6, 8);
    this.leftLeg = new THREE.Mesh(legGeo, apronMat); // White tights
    this.leftLeg.position.set(0.15, 0.3, 0);
    this.leftLeg.castShadow = true;
    
    this.rightLeg = new THREE.Mesh(legGeo, apronMat);
    this.rightLeg.position.set(-0.15, 0.3, 0);
    this.rightLeg.castShadow = true;

    // Shoes
    const shoeGeo = new THREE.BoxGeometry(0.12, 0.1, 0.2);
    const leftShoe = new THREE.Mesh(shoeGeo, shoeMat);
    leftShoe.position.set(0, -0.3, 0.04);
    this.leftLeg.add(leftShoe);

    const rightShoe = new THREE.Mesh(shoeGeo, shoeMat);
    rightShoe.position.set(0, -0.3, 0.04);
    this.rightLeg.add(rightShoe);

    this.meshGroup.add(this.leftLeg, this.rightLeg);

    // Hat Container
    this.hatGroup = new THREE.Group();
    this.hatGroup.position.set(0, 1.95, 0);
    this.meshGroup.add(this.hatGroup);

    this.updateHatMesh();
  }

  updateHatMesh() {
    while (this.hatGroup.children.length > 0) {
      this.hatGroup.remove(this.hatGroup.children[0]);
    }

    if (this.activeHatType === 'bow') {
      const bowMat = new THREE.MeshStandardMaterial({ color: 0x3b82f6 });
      const bowGeo = new THREE.BoxGeometry(0.3, 0.12, 0.08);
      const bow = new THREE.Mesh(bowGeo, bowMat);
      this.hatGroup.add(bow);
    } else if (this.activeHatType === 'top-hat') {
      const hatMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.3 });
      const brimGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.04, 16);
      const crownGeo = new THREE.CylinderGeometry(0.25, 0.22, 0.4, 16);
      const brim = new THREE.Mesh(brimGeo, hatMat);
      const crown = new THREE.Mesh(crownGeo, hatMat);
      crown.position.y = 0.2;
      const hat = new THREE.Group();
      hat.add(brim, crown);
      hat.rotation.z = -0.15;
      this.hatGroup.add(hat);
    } else if (this.activeHatType === 'cat-ears') {
      const earMat = new THREE.MeshStandardMaterial({ color: 0xc084fc });
      const earGeo = new THREE.ConeGeometry(0.12, 0.25, 4);
      const earL = new THREE.Mesh(earGeo, earMat);
      earL.position.set(-0.2, 0, 0);
      const earR = new THREE.Mesh(earGeo, earMat);
      earR.position.set(0.2, 0, 0);
      this.hatGroup.add(earL, earR);
    } else if (this.activeHatType === 'rabbit-ears') {
      const earMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const earGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.5, 8);
      const earL = new THREE.Mesh(earGeo, earMat);
      earL.position.set(-0.15, 0.2, 0);
      earL.rotation.z = -0.1;
      const earR = new THREE.Mesh(earGeo, earMat);
      earR.position.set(0.15, 0.2, 0);
      earR.rotation.z = 0.1;
      this.hatGroup.add(earL, earR);
    } else if (this.activeHatType === 'crown') {
      const crownMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 });
      const crownGeo = new THREE.CylinderGeometry(0.18, 0.12, 0.2, 8);
      const crown = new THREE.Mesh(crownGeo, crownMat);
      this.hatGroup.add(crown);
    }
  }

  setDressColor(hexColor) {
    this.dressColor = hexColor;
    this.createModel();
  }

  setHat(hatType) {
    this.activeHatType = hatType;
    this.updateHatMesh();
  }

  setSizeScale(targetScale) {
    this.targetScale = targetScale;
    if (targetScale < 0.5) audioManager.playGulp();
    if (targetScale > 1.8) audioManager.playBite();
  }

  update(delta, moveDir, physicsEngine) {
    // 1. Interpolate scale smoothly
    if (Math.abs(this.scale - this.targetScale) > 0.01) {
      this.scale += (this.targetScale - this.scale) * 0.1;
      this.group.scale.setScalar(this.scale);
    }

    // 2. Physics & Gravity
    const gravity = 24.0;
    this.group.position.y += this.velocityY * delta;

    if (!this.isGrounded) {
      this.velocityY -= gravity * delta;
    }

    // Ground level check
    if (this.group.position.y <= 0) {
      this.group.position.y = 0;
      this.velocityY = 0;
      this.isGrounded = true;
    }

    // Check Mushroom Spring Bounce
    const springForce = physicsEngine.checkMushroomBounce(this.group.position, this.velocityY);
    if (springForce && this.velocityY <= 0) {
      this.velocityY = springForce;
      this.isGrounded = false;
      audioManager.playJump();
    }

    // 3. Horizontal Movement
    if (moveDir.lengthSq() > 0) {
      const moveSpeed = (this.scale < 0.5 ? 4.5 : (this.scale > 1.8 ? 9.0 : 6.5));
      this.group.position.x += moveDir.x * moveSpeed * delta;
      this.group.position.z += moveDir.z * moveSpeed * delta;

      // Face movement direction
      const targetAngle = Math.atan2(moveDir.x, moveDir.z);
      this.meshGroup.rotation.y = targetAngle;

      // Walking Leg & Arm Animation
      this.walkAnimTime += delta * 12 * (this.scale < 0.5 ? 1.5 : 1.0);
      this.leftLeg.rotation.x = Math.sin(this.walkAnimTime) * 0.6;
      this.rightLeg.rotation.x = -Math.sin(this.walkAnimTime) * 0.6;
      this.leftArm.rotation.x = -Math.sin(this.walkAnimTime) * 0.5;
      this.rightArm.rotation.x = Math.sin(this.walkAnimTime) * 0.5;
    } else {
      // Idle pose reset
      this.leftLeg.rotation.x = 0;
      this.rightLeg.rotation.x = 0;
      this.leftArm.rotation.x = 0;
      this.rightArm.rotation.x = 0;
    }

    // Resolve Terrain Collisions
    physicsEngine.resolveTerrainCollision(this.group.position, 0.5 * this.scale);
  }

  jump() {
    if (this.isGrounded) {
      this.velocityY = 8.5;
      this.isGrounded = false;
      audioManager.playJump();
    }
  }
}
