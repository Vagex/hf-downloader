import * as THREE from 'three';

export class CardGuardEntity {
  constructor(scene, startPos, waypoints, suite = 'hearts') {
    this.scene = scene;
    this.waypoints = waypoints;
    this.currentWaypointIdx = 0;
    this.suite = suite;

    this.group = new THREE.Group();
    this.group.position.copy(startPos);
    this.scene.add(this.group);

    this.speed = 2.2;
    this.walkAnimTime = 0;

    this.createGuardModel();
  }

  createGuardModel() {
    const cardMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const woodMat = new THREE.MeshStandardMaterial({ color: 0x78350f });
    const spearGoldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.1 });
    const symbolMat = new THREE.MeshStandardMaterial({ color: this.suite === 'hearts' ? 0xd97706 : 0x1e293b });

    // Playing Card Body (Thin Box)
    const bodyGeo = new THREE.BoxGeometry(1.2, 1.8, 0.06);
    this.cardBody = new THREE.Mesh(bodyGeo, cardMat);
    this.cardBody.position.y = 1.2;
    this.cardBody.castShadow = true;
    this.group.add(this.cardBody);

    // Heart / Spade Emblem
    const emblemGeo = new THREE.BoxGeometry(0.35, 0.35, 0.08);
    const emblem = new THREE.Mesh(emblemGeo, symbolMat);
    emblem.position.set(0, 1.3, 0);
    this.group.add(emblem);

    // Head (Cylinder on top of card)
    const headGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.3, 12);
    const headMat = new THREE.MeshStandardMaterial({ color: 0xffdfd3 });
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = 2.25;
    this.group.add(head);

    // Helmet
    const helmetGeo = new THREE.ConeGeometry(0.25, 0.3, 12);
    const helmet = new THREE.Mesh(helmetGeo, symbolMat);
    helmet.position.y = 2.5;
    this.group.add(helmet);

    // Arms & Spear
    const armGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.6, 8);
    this.leftArm = new THREE.Mesh(armGeo, cardMat);
    this.leftArm.position.set(0.68, 1.2, 0);
    
    this.rightArm = new THREE.Mesh(armGeo, cardMat);
    this.rightArm.position.set(-0.68, 1.2, 0);

    // Spear
    const poleGeo = new THREE.CylinderGeometry(0.03, 0.03, 2.5, 8);
    const pole = new THREE.Mesh(poleGeo, woodMat);
    pole.position.set(-0.1, 0.5, 0.2);

    const tipGeo = new THREE.ConeGeometry(0.08, 0.35, 4);
    const tip = new THREE.Mesh(tipGeo, spearGoldMat);
    tip.position.set(-0.1, 1.8, 0.2);

    this.rightArm.add(pole, tip);
    this.group.add(this.leftArm, this.rightArm);

    // Legs
    const legGeo = new THREE.CylinderGeometry(0.06, 0.05, 0.6, 8);
    this.leftLeg = new THREE.Mesh(legGeo, symbolMat);
    this.leftLeg.position.set(0.25, 0.3, 0);

    this.rightLeg = new THREE.Mesh(legGeo, symbolMat);
    this.rightLeg.position.set(-0.25, 0.3, 0);

    this.group.add(this.leftLeg, this.rightLeg);
  }

  update(delta) {
    if (!this.waypoints || this.waypoints.length === 0) return;

    const target = this.waypoints[this.currentWaypointIdx];
    const dir = new THREE.Vector3().subVectors(target, this.group.position);
    dir.y = 0; // Ground plane only

    const dist = dir.length();

    if (dist < 0.4) {
      // Advance to next waypoint
      this.currentWaypointIdx = (this.currentWaypointIdx + 1) % this.waypoints.length;
    } else {
      dir.normalize();
      this.group.position.addScaledVector(dir, this.speed * delta);

      // Rotate towards movement direction
      const targetAngle = Math.atan2(dir.x, dir.z);
      this.group.rotation.y = targetAngle;

      // Patrol Walk Animation
      this.walkAnimTime += delta * 8;
      this.leftLeg.rotation.x = Math.sin(this.walkAnimTime) * 0.4;
      this.rightLeg.rotation.x = -Math.sin(this.walkAnimTime) * 0.4;
      this.leftArm.rotation.x = -Math.sin(this.walkAnimTime) * 0.3;
      this.rightArm.rotation.x = Math.sin(this.walkAnimTime) * 0.3;
    }
  }
}
