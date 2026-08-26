import * as THREE from 'three';

export class TeaTableEntity {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);

    this.group.position.set(0, 0, 0); // Center of garden

    this.createTable();
    this.createPouringTeapot();
    this.createBanquetGuests();
  }

  createTable() {
    const woodMat = new THREE.MeshStandardMaterial({ color: 0x582f0e, roughness: 0.4 });
    const clothMat = new THREE.MeshStandardMaterial({ color: 0xfff7ed, roughness: 0.2 });
    const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 });
    const teaLiquidMat = new THREE.MeshStandardMaterial({ color: 0xd97706, transparent: true, opacity: 0.85 });

    // Tabletop (Long oval/box)
    const tableTopGeo = new THREE.BoxGeometry(8, 0.4, 4);
    const tableTop = new THREE.Mesh(tableTopGeo, woodMat);
    tableTop.position.y = 1.8;
    tableTop.castShadow = true;
    tableTop.receiveShadow = true;
    this.group.add(tableTop);

    // Tablecloth
    const clothGeo = new THREE.BoxGeometry(8.2, 0.45, 4.2);
    const cloth = new THREE.Mesh(clothGeo, clothMat);
    cloth.position.y = 1.78;
    cloth.receiveShadow = true;
    this.group.add(cloth);

    // Table Legs
    const legGeo = new THREE.CylinderGeometry(0.18, 0.12, 1.8, 12);
    const legPositions = [
      [-3.6, 0.9, -1.7], [3.6, 0.9, -1.7],
      [-3.6, 0.9, 1.7], [3.6, 0.9, 1.7]
    ];
    legPositions.forEach(([x, y, z]) => {
      const leg = new THREE.Mesh(legGeo, woodMat);
      leg.position.set(x, y, z);
      leg.castShadow = true;
      this.group.add(leg);
    });

    // Teacups & Saucers around table
    const cupGeo = new THREE.CylinderGeometry(0.2, 0.12, 0.25, 12);
    const saucerGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.05, 12);

    const cupPositions = [
      [-2, 2.15, -1], [0, 2.15, -1], [2, 2.15, -1],
      [-2, 2.15, 1], [0, 2.15, 1], [2, 2.15, 1]
    ];

    cupPositions.forEach(([x, y, z]) => {
      const cupGroup = new THREE.Group();
      cupGroup.position.set(x, y, z);

      const saucer = new THREE.Mesh(saucerGeo, clothMat);
      const cup = new THREE.Mesh(cupGeo, clothMat);
      cup.position.y = 0.15;

      const teaLiquid = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.02, 12), teaLiquidMat);
      teaLiquid.position.y = 0.24;

      cupGroup.add(saucer, cup, teaLiquid);
      this.group.add(cupGroup);
    });

    // Tiered Cake Stand
    const standPole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.2, 8), goldMat);
    standPole.position.set(-1, 2.6, 0);
    const plate1 = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 0.04, 16), clothMat);
    plate1.position.set(-1, 2.3, 0);
    const plate2 = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 0.04, 16), clothMat);
    plate2.position.set(-1, 2.8, 0);
    this.group.add(standPole, plate1, plate2);
  }

  createPouringTeapot() {
    const teapotMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.6, roughness: 0.2 });
    const teaStreamMat = new THREE.MeshStandardMaterial({ color: 0xd97706, transparent: true, opacity: 0.85 });

    // Floating Teapot
    this.teapotGroup = new THREE.Group();
    this.teapotGroup.position.set(2, 3.8, 0);
    this.teapotGroup.rotation.z = -0.55; // Tilted to pour

    const bodyGeo = new THREE.SphereGeometry(0.6, 16, 16);
    const body = new THREE.Mesh(bodyGeo, teapotMat);
    
    const spoutGeo = new THREE.CylinderGeometry(0.08, 0.15, 0.8, 12);
    const spout = new THREE.Mesh(spoutGeo, teapotMat);
    spout.position.set(-0.6, 0.3, 0);
    spout.rotation.z = 1.1;

    const handleGeo = new THREE.TorusGeometry(0.4, 0.06, 8, 16);
    const handle = new THREE.Mesh(handleGeo, teapotMat);
    handle.position.set(0.6, 0, 0);

    this.teapotGroup.add(body, spout, handle);
    this.group.add(this.teapotGroup);

    // Continuous Tea Stream
    const streamGeo = new THREE.CylinderGeometry(0.06, 0.08, 1.8, 8);
    this.teaStream = new THREE.Mesh(streamGeo, teaStreamMat);
    this.teaStream.position.set(1.15, 2.8, 0);
    this.group.add(this.teaStream);
  }

  createBanquetGuests() {
    // Mad Hatter NPC
    const hatterGroup = new THREE.Group();
    hatterGroup.position.set(-3.8, 0, 0);
    hatterGroup.rotation.y = Math.PI / 2;

    const suitMat = new THREE.MeshStandardMaterial({ color: 0x7c3aed });
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xffdfd3 });
    const hatMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b });

    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.35, 1.2, 12), suitMat);
    body.position.y = 1.4;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.35, 16, 16), skinMat);
    head.position.y = 2.2;
    
    // Top Hat
    const hatCrown = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.28, 0.6, 16), hatMat);
    hatCrown.position.y = 2.7;
    const hatBrim = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.05, 16), hatMat);
    hatBrim.position.y = 2.4;
    
    this.hatterHeadGroup = new THREE.Group();
    this.hatterHeadGroup.add(head, hatCrown, hatBrim);

    hatterGroup.add(body, this.hatterHeadGroup);
    this.group.add(hatterGroup);

    // March Hare NPC
    const hareGroup = new THREE.Group();
    hareGroup.position.set(0, 0, -2.2);

    const hareMat = new THREE.MeshStandardMaterial({ color: 0xd97706 });
    const hareBody = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.3, 1.1, 12), hareMat);
    hareBody.position.y = 1.35;

    const hareHead = new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 16), hareMat);
    hareHead.position.y = 2.1;

    const earGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.7, 8);
    const ear1 = new THREE.Mesh(earGeo, hareMat);
    ear1.position.set(-0.15, 2.6, 0);
    ear1.rotation.z = -0.15;
    const ear2 = new THREE.Mesh(earGeo, hareMat);
    ear2.position.set(0.15, 2.6, 0);
    ear2.rotation.z = 0.15;

    this.hareHeadGroup = new THREE.Group();
    this.hareHeadGroup.add(hareHead, ear1, ear2);

    hareGroup.add(hareBody, this.hareHeadGroup);
    this.group.add(hareGroup);
  }

  update(delta) {
    // Gentle floating & pouring motion of teapot
    if (this.teapotGroup) {
      this.teapotGroup.position.y = 3.8 + Math.sin(Date.now() * 0.002) * 0.1;
    }
    // Guest head animations
    if (this.hatterHeadGroup) {
      this.hatterHeadGroup.rotation.y = Math.sin(Date.now() * 0.0015) * 0.2;
    }
    if (this.hareHeadGroup) {
      this.hareHeadGroup.rotation.x = Math.sin(Date.now() * 0.002) * 0.15;
    }
  }
}
