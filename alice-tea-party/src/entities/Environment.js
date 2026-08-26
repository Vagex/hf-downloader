import * as THREE from 'three';

export class WonderlandEnvironment {
  constructor(scene, physicsEngine) {
    this.scene = scene;
    this.physics = physicsEngine;
    this.animatedObjects = [];

    this.createTerrain();
    this.createMushrooms();
    this.createRoseGarden();
    this.createMagicPotionsAndCakes();
    this.createCollectibleItems();
    this.createClockworkSkyIslands();
  }

  createTerrain() {
    // 1. Base Terrain Grass
    const grassMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.8 });
    const groundGeo = new THREE.PlaneGeometry(120, 120);
    const ground = new THREE.Mesh(groundGeo, grassMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // 2. Central Checkerboard Lawn around Tea Table
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, 256, 256);
    ctx.fillStyle = '#f8fafc';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        if ((r + c) % 2 === 0) {
          ctx.fillRect(c * 32, r * 32, 32, 32);
        }
      }
    }
    const checkerTexture = new THREE.CanvasTexture(canvas);
    checkerTexture.wrapS = THREE.RepeatWrapping;
    checkerTexture.wrapT = THREE.RepeatWrapping;
    checkerTexture.repeat.set(4, 4);

    const checkerMat = new THREE.MeshStandardMaterial({ map: checkerTexture, roughness: 0.3 });
    const checkerLawn = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 0.1, 32), checkerMat);
    checkerLawn.position.set(0, 0.05, 0);
    checkerLawn.receiveShadow = true;
    this.scene.add(checkerLawn);
  }

  createMushrooms() {
    const mushroomStemMat = new THREE.MeshStandardMaterial({ color: 0xffedd5 });
    const mushroomCapMat1 = new THREE.MeshStandardMaterial({ color: 0xc084fc, roughness: 0.3 });
    const mushroomCapMat2 = new THREE.MeshStandardMaterial({ color: 0xf43f5e, roughness: 0.3 });

    const positions = [
      { x: -16, z: -10, scale: 1.8, mat: mushroomCapMat1 },
      { x: 18, z: 12, scale: 2.2, mat: mushroomCapMat2 },
      { x: -22, z: 18, scale: 2.0, mat: mushroomCapMat1 },
      { x: 20, z: -20, scale: 1.6, mat: mushroomCapMat2 }
    ];

    positions.forEach((p, idx) => {
      const group = new THREE.Group();
      group.position.set(p.x, 0, p.z);
      group.scale.setScalar(p.scale);

      // Stem
      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.5, 2, 12), mushroomStemMat);
      stem.position.y = 1;
      stem.castShadow = true;

      // Cap (Dome)
      const cap = new THREE.Mesh(new THREE.SphereGeometry(1.2, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), p.mat);
      cap.position.y = 2;
      cap.castShadow = true;

      group.add(stem, cap);
      this.scene.add(group);

      // Register spring bounce mushroom in physics
      this.physics.addBounceMushroom(group, 16 + p.scale * 2);
    });
  }

  createRoseGarden() {
    // Queen of Hearts Rose Garden Hedges
    const hedgeMat = new THREE.MeshStandardMaterial({ color: 0x166534, roughness: 0.9 });
    const hedgeGeo = new THREE.BoxGeometry(16, 2.5, 1.2);

    const h1 = new THREE.Mesh(hedgeGeo, hedgeMat);
    h1.position.set(-18, 1.25, -20);
    const h2 = new THREE.Mesh(hedgeGeo, hedgeMat);
    h2.position.set(-18, 1.25, -34);
    h2.rotation.y = Math.PI / 2;

    this.scene.add(h1, h2);
    this.physics.addCollider(h1, 'box', new THREE.Vector3(16, 2.5, 1.2));
    this.physics.addCollider(h2, 'box', new THREE.Vector3(1.2, 2.5, 16));

    // 4 White Rose Bushes (Interactive)
    this.roseBushes = [];
    const rosePositions = [
      { id: 'rose-1', x: -14, z: -24 },
      { id: 'rose-2', x: -22, z: -24 },
      { id: 'rose-3', x: -14, z: -30 },
      { id: 'rose-4', x: -22, z: -30 }
    ];

    rosePositions.forEach((pos) => {
      const bushGroup = new THREE.Group();
      bushGroup.position.set(pos.x, 0, pos.z);

      const bushMat = new THREE.MeshStandardMaterial({ color: 0x15803d });
      const bush = new THREE.Mesh(new THREE.SphereGeometry(1.0, 12, 12), bushMat);
      bush.position.y = 1.0;
      bushGroup.add(bush);

      // Rose Head Mesh
      const roseMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 }); // Starts white
      const roseHead = new THREE.Mesh(new THREE.SphereGeometry(0.35, 12, 12), roseMat);
      roseHead.position.set(0, 1.8, 0);
      bushGroup.add(roseHead);

      this.scene.add(bushGroup);

      // Register interactive trigger to paint red
      this.physics.addInteractable(
        pos.id,
        roseHead,
        2.5,
        '按 [E] 将白玫瑰刷成鲜红色 🌹',
        () => {
          roseMat.color.setHex(0xd97706); // Paint red!
        }
      );
    });
  }

  createMagicPotionsAndCakes() {
    // 1. DRINK ME Potion Bottle
    const bottleGroup = new THREE.Group();
    bottleGroup.position.set(-6, 0.05, 4);

    const bottleMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.8 });
    const liquidMat = new THREE.MeshStandardMaterial({ color: 0x0284c7 });
    const bottle = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.3, 0.8, 12), bottleMat);
    bottle.position.y = 0.4;
    const liquid = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 0.5, 12), liquidMat);
    liquid.position.y = 0.3;

    bottleGroup.add(bottle, liquid);
    this.scene.add(bottleGroup);

    this.physics.addInteractable(
      'drink-me-potion',
      bottleGroup,
      2.0,
      '按 [E] 喝下“DRINK ME”药水 (缩至 0.3x) 🧪',
      (alice) => {
        alice.setSizeScale(0.3);
      }
    );

    // 2. EAT ME Cake Plate
    const cakeGroup = new THREE.Group();
    cakeGroup.position.set(6, 0.05, 4);

    const cakeMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.5 });
    const icingMat = new THREE.MeshStandardMaterial({ color: 0xf43f5e, roughness: 0.3 });
    const cake = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.4, 12), cakeMat);
    cake.position.y = 0.2;
    const icing = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.1, 12), icingMat);
    icing.position.y = 0.4;

    cakeGroup.add(cake, icing);
    this.scene.add(cakeGroup);

    this.physics.addInteractable(
      'eat-me-cake',
      cakeGroup,
      2.0,
      '按 [E] 吃下“EAT ME”蛋糕 (放大至 2.2x) 🍰',
      (alice) => {
        alice.setSizeScale(2.2);
      }
    );

    // 3. NORMAL SIZE Mirror/Reset Fountain
    const fountainGroup = new THREE.Group();
    fountainGroup.position.set(0, 0, 8);
    const marbleMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0 });
    const fountain = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 1.0, 0.6, 16), marbleMat);
    fountain.position.y = 0.3;
    fountainGroup.add(fountain);
    this.scene.add(fountainGroup);

    this.physics.addInteractable(
      'reset-size',
      fountainGroup,
      2.0,
      '按 [E] 饮用仙境清泉 (恢复 1.0x 标准体型) 💧',
      (alice) => {
        alice.setSizeScale(1.0);
      }
    );
  }

  createCollectibleItems() {
    // 3 Sugar Cubes
    const sugarMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 });
    const sugarPositions = [
      { id: 'sugar-1', x: -3, z: -5 },
      { id: 'sugar-2', x: 5, z: -8 },
      { id: 'sugar-3', x: 2, z: 12 }
    ];
    sugarPositions.forEach(p => {
      const sugar = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 0.35), sugarMat);
      sugar.position.set(p.x, 0.35, p.z);
      this.scene.add(sugar);
      this.animatedObjects.push({ mesh: sugar, speed: 2, rot: 0.02 });

      this.physics.addInteractable(
        p.id,
        sugar,
        1.5,
        '按 [E] 搜集巨型方糖 🍬',
        (alice, questMgr) => {
          this.scene.remove(sugar);
          questMgr.collectItem('sugar');
        }
      );
    });

    // 3 Macarons
    const macaronColors = [0xf43f5e, 0x10b981, 0xc084fc];
    const macaronPositions = [
      { id: 'mac-1', x: 8, z: -2 },
      { id: 'mac-2', x: -8, z: 6 },
      { id: 'mac-3', x: -12, z: -10 }
    ];
    macaronPositions.forEach((p, idx) => {
      const macMat = new THREE.MeshStandardMaterial({ color: macaronColors[idx] });
      const mac = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.2, 12), macMat);
      mac.position.set(p.x, 0.35, p.z);
      this.scene.add(mac);
      this.animatedObjects.push({ mesh: mac, speed: 2.5, rot: 0.03 });

      this.physics.addInteractable(
        p.id,
        mac,
        1.5,
        '按 [E] 搜集彩色马卡龙 🧁',
        (alice, questMgr) => {
          this.scene.remove(mac);
          questMgr.collectItem('macaron');
        }
      );
    });

    // 2 Tea Leaves Baskets
    const teaLeafMat = new THREE.MeshStandardMaterial({ color: 0x15803d });
    const leafPositions = [
      { id: 'leaf-1', x: 12, z: 8 },
      { id: 'leaf-2', x: -10, z: -18 }
    ];
    leafPositions.forEach(p => {
      const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.3, 8, 8), teaLeafMat);
      leaf.position.set(p.x, 0.35, p.z);
      this.scene.add(leaf);
      this.animatedObjects.push({ mesh: leaf, speed: 1.8, rot: 0.01 });

      this.physics.addInteractable(
        p.id,
        leaf,
        1.5,
        '按 [E] 搜集仙境茶叶 🌿',
        (alice, questMgr) => {
          this.scene.remove(leaf);
          questMgr.collectItem('tea');
        }
      );
    });
  }

  createClockworkSkyIslands() {
    // Rotating Clockwork Pocket Watch Platforms
    const gearMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 });
    const platformMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5 });

    this.skyGears = [];
    const gearConfigs = [
      { x: 24, y: 5, z: 20, radius: 3.5, rotSpeed: 0.5 },
      { x: 32, y: 9, z: 24, radius: 3.0, rotSpeed: -0.8 },
      { x: 40, y: 13, z: 20, radius: 4.0, rotSpeed: 0.6 }
    ];

    gearConfigs.forEach((c, idx) => {
      const gearGroup = new THREE.Group();
      gearGroup.position.set(c.x, c.y, c.z);

      const plat = new THREE.Mesh(new THREE.CylinderGeometry(c.radius, c.radius, 0.6, 16), platformMat);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(c.radius, 0.15, 8, 24), gearMat);
      ring.rotation.x = Math.PI / 2;

      // Clock Hands on gear
      const hand = new THREE.Mesh(new THREE.BoxGeometry(c.radius * 0.8, 0.15, 0.15), gearMat);
      hand.position.y = 0.35;

      gearGroup.add(plat, ring, hand);
      this.scene.add(gearGroup);

      this.skyGears.push({ group: gearGroup, speed: c.rotSpeed, hand });

      // Add terrain colliders for jumping platforms
      this.physics.addCollider(plat, 'cylinder', { r: c.radius });
    });

    // High Sky Platform with Golden Time Key Chest
    const chestGroup = new THREE.Group();
    chestGroup.position.set(40, 14.5, 20);

    const chestMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.1 });
    const chest = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.6, 0.5), chestMat);
    chestGroup.add(chest);
    this.scene.add(chestGroup);

    this.physics.addInteractable(
      'time-key',
      chestGroup,
      2.5,
      '按 [E] 打开时间宝箱获取黄金钥匙 🔑',
      (alice, questMgr) => {
        this.scene.remove(chestGroup);
        questMgr.collectItem('key');
      }
    );
  }

  update(delta) {
    // Animate floating collectibles
    const time = Date.now() * 0.003;
    this.animatedObjects.forEach(obj => {
      if (obj.mesh.parent) {
        obj.mesh.position.y = 0.35 + Math.sin(time * obj.speed) * 0.12;
        obj.mesh.rotation.y += obj.rot;
      }
    });

    // Rotate Sky Gear Platforms
    this.skyGears.forEach(g => {
      g.group.rotation.y += g.speed * delta;
      if (g.hand) g.hand.rotation.y += g.speed * delta * 1.5;
    });
  }
}
