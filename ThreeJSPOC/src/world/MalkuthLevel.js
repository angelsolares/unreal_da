import * as THREE from 'three';
import { PALETTE } from '../core/Assets.js';

// Malkuth: The Kingdom — compressed POC layout following LDD v3 beat chart.
// Nine zones along +Z: Garden, Hedge Path, Clearing, Gazebo, Bridge,
// Sanctuary, Amphitheater, Throne, Ascension.
export class MalkuthLevel {
  constructor(scene, assets) {
    this.scene = scene;
    this.assets = assets;
    this.group = new THREE.Group();
    this.group.name = 'Malkuth';
    scene.add(this.group);

    this.colliders = [];      // {minX,maxX,minZ,maxZ,maxY}
    this.triggers = [];       // {z, id, fired}
    this.anchors = {};        // named Vector3 positions
    this.mirrorPanels = [];
    this.fountainsUp = [];    // upward water jets to animate
    this.thornBarrier = null;
    this.thornCollider = null;
    this.gates = {};          // id -> {mesh, col, z} — divine barriers gating each trial

    this.mats = this.createMaterials();
    this.build();
  }

  createMaterials() {
    const m = {};
    m.grass = new THREE.MeshStandardMaterial({ color: PALETTE.grass, roughness: 0.95 });
    m.earth = new THREE.MeshStandardMaterial({ color: PALETTE.earth, roughness: 1 });
    m.marble = new THREE.MeshStandardMaterial({ color: PALETTE.marble, roughness: 0.5, metalness: 0.05 });
    m.ivory = new THREE.MeshStandardMaterial({ color: PALETTE.ivory, roughness: 0.6 });
    m.gold = new THREE.MeshStandardMaterial({ color: PALETTE.paleGold, roughness: 0.3, metalness: 0.85 });
    m.bark = new THREE.MeshStandardMaterial({ color: PALETTE.bark, roughness: 0.95 });
    m.water = new THREE.MeshStandardMaterial({
      color: 0xcfe8d8, roughness: 0.08, metalness: 0.75,
      transparent: true, opacity: 0.75,
      emissive: 0xd4af37, emissiveIntensity: 0.12,
    });
    m.mirror = new THREE.MeshStandardMaterial({
      color: 0xffffff, roughness: 0.04, metalness: 1.0, envMapIntensity: 1.6,
    });
    m.pool = new THREE.MeshStandardMaterial({
      color: 0x8a6845, roughness: 0.05, metalness: 0.9, envMapIntensity: 1.4,
    });
    m.portal = new THREE.MeshStandardMaterial({
      color: 0x2a0a4a, emissive: PALETTE.shadowPurple, emissiveIntensity: 2.2,
      transparent: true, opacity: 0.92, side: THREE.DoubleSide,
    });
    m.rune = new THREE.MeshStandardMaterial({
      color: 0x1a0530, emissive: 0x8a2be2, emissiveIntensity: 1.6,
    });
    m.holy = new THREE.MeshStandardMaterial({
      color: 0xfff8e0, emissive: 0xffe9bb, emissiveIntensity: 1.4,
    });
    m.thorn = new THREE.MeshStandardMaterial({ color: 0x2e4a1c, roughness: 1 });
    m.stairLight = new THREE.MeshStandardMaterial({
      color: 0xfff4d0, emissive: 0xd4af37, emissiveIntensity: 0.7,
      transparent: true, opacity: 0.45, depthWrite: false,
    });
    m.mountain = new THREE.MeshStandardMaterial({ color: 0x4a5a33, roughness: 1, flatShading: true });
    m.mountainRock = new THREE.MeshStandardMaterial({ color: 0x6b5b43, roughness: 1, flatShading: true });
    return m;
  }

  // ---------- helpers ----------
  place(name, x, z, ry = 0, scale = 1, { y = null, collide = false, colSize = null, enhance = true } = {}) {
    const obj = this.assets.spawn(name, { position: [x, y ?? this.groundHeight(x, z), z], rotationY: ry, scale });
    if (!obj) return null;
    if (enhance) this.enhanceMaterials(obj);
    this.group.add(obj);
    if (collide) {
      const box = new THREE.Box3().setFromObject(obj);
      if (colSize) {
        this.addCollider(x - colSize[0] / 2, x + colSize[0] / 2, z - colSize[1] / 2, z + colSize[1] / 2, box.max.y);
      } else {
        this.addCollider(box.min.x, box.max.x, box.min.z, box.max.z, box.max.y);
      }
    }
    return obj;
  }

  enhanceMaterials(obj) {
    obj.traverse((o) => {
      if (!o.isMesh && !o.isSkinnedMesh) return;
      const n = (o.name + ' ' + (o.material?.name || '')).toLowerCase();
      if (n.includes('watersurface') || n.includes('_water') || n.includes('water')) {
        o.material = this.mats.water;
        o.castShadow = false;
      } else if (n.includes('mirrorsurface')) {
        o.material = this.mats.mirror;
      } else if (n.includes('portalsurface')) {
        o.material = this.mats.portal;
      } else if (n.includes('runering') || n.includes('rune')) {
        o.material = this.mats.rune;
      }
    });
  }

  addCollider(minX, maxX, minZ, maxZ, maxY = 3) {
    this.colliders.push({ minX, maxX, minZ, maxZ, maxY });
  }

  groundHeight(x, z) {
    const ax = Math.abs(x);
    // Ascension ramp to Yesod portal
    if (z >= 340 && z <= 353 && ax <= 5) return 6 + ((z - 340) / 13) * 8;
    // Throne plateau + grand stair
    if (z >= 295 && z < 340 && ax <= 30) {
      if (z < 305) return ((z - 295) / 10) * 6;
      return 6;
    }
    // Bridge deck over the reflecting pool
    if (z >= 150 && z <= 230 && ax <= 5.5) return 0;
    // Pool basin
    if (z >= 146 && z <= 234 && ax <= 34) return -4;
    return 0;
  }

  // Circle-vs-AABB pushout. Returns corrected position.
  resolveCollisions(pos, radius = 0.42) {
    for (const c of this.colliders) {
      if (pos.y > c.maxY) continue;
      const nx = Math.max(c.minX, Math.min(pos.x, c.maxX));
      const nz = Math.max(c.minZ, Math.min(pos.z, c.maxZ));
      const dx = pos.x - nx, dz = pos.z - nz;
      const d2 = dx * dx + dz * dz;
      if (d2 < radius * radius) {
        if (d2 < 1e-8) {
          // Center inside the box: push along smallest penetration axis
          const pxl = pos.x - c.minX, pxr = c.maxX - pos.x;
          const pzl = pos.z - c.minZ, pzr = c.maxZ - pos.z;
          const m = Math.min(pxl, pxr, pzl, pzr);
          if (m === pxl) pos.x = c.minX - radius;
          else if (m === pxr) pos.x = c.maxX + radius;
          else if (m === pzl) pos.z = c.minZ - radius;
          else pos.z = c.maxZ + radius;
        } else {
          const d = Math.sqrt(d2);
          pos.x = nx + (dx / d) * radius;
          pos.z = nz + (dz / d) * radius;
        }
      }
    }
    return pos;
  }

  addTrigger(z, id) { this.triggers.push({ z, id, fired: false }); }

  // ---------- zone builders ----------
  build() {
    this.buildTerrain();
    this.buildGarden();
    this.buildHedgePath();
    this.buildClearing();
    this.buildGazebo();
    this.buildBridge();
    this.buildSanctuary();
    this.buildAmphitheater();
    this.buildThrone();
    this.buildAscension();
    this.buildBounds();
    this.buildGates();
  }

  buildTerrain() {
    // Main grass plane
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, 420), this.mats.grass);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(0, -0.02, 190);
    ground.receiveShadow = true;
    this.group.add(ground);

    // Subtle color patches — the garden is too perfect, but never flat
    for (let i = 0; i < 26; i++) {
      const r = 4 + Math.random() * 9;
      const patch = new THREE.Mesh(
        new THREE.CircleGeometry(r, 20),
        new THREE.MeshStandardMaterial({
          color: i % 2 ? 0x7cb342 : 0x5f8a38, roughness: 1,
          transparent: true, opacity: 0.35,
        })
      );
      patch.rotation.x = -Math.PI / 2;
      patch.position.set((Math.random() - 0.5) * 90, 0.0, Math.random() * 360 - 5);
      patch.receiveShadow = true;
      this.group.add(patch);
    }

    // Pool basin walls (visible inner faces)
    const basin = new THREE.Mesh(new THREE.PlaneGeometry(68, 88), this.mats.earth);
    basin.rotation.x = -Math.PI / 2;
    basin.position.set(0, -4, 190);
    this.group.add(basin);
    // Reflecting pool surface — pale mirror of the golden sky
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(66, 86), this.mats.pool);
    pool.rotation.x = -Math.PI / 2;
    pool.position.set(0, -3.1, 190);
    this.group.add(pool);
    this.anchors.poolBounds = { minX: -33, maxX: 33, minZ: 147, maxZ: 233, surfaceY: -3.1 };

    // Distant mountains framing the kingdom (Art Bible: landscape first)
    const mountains = [
      [-70, 40, 55, 34, this.mats.mountain], [75, 90, 62, 40, this.mats.mountainRock],
      [-78, 150, 60, 44, this.mats.mountainRock], [72, 210, 66, 38, this.mats.mountain],
      [-72, 270, 58, 36, this.mats.mountain], [60, 330, 70, 46, this.mats.mountainRock],
      [-60, 345, 64, 42, this.mats.mountain], [0, 395, 90, 55, this.mats.mountainRock],
      [-40, -45, 60, 30, this.mats.mountain], [45, -50, 66, 36, this.mats.mountainRock],
    ];
    for (const [x, z, r, h, mat] of mountains) {
      const mtn = new THREE.Mesh(new THREE.ConeGeometry(r, h, 7), mat);
      mtn.position.set(x, h / 2 - 3, z);
      mtn.rotation.y = Math.random() * Math.PI;
      mtn.castShadow = false;
      mtn.receiveShadow = true;
      this.group.add(mtn);
    }
  }

  buildGarden() {
    // Entry trellis
    this.place('SM_MGK_Trellis_Arch', 0, 2, 0, 1.4);

    // Tree-of-Life central path: marble walkway + hedge walls + topiary sephiroth
    for (let z = 6; z <= 48; z += 6) {
      this.place('SM_MGK_Path_Straight_300', 0, z, 0, 2);
    }
    // Hedge rows flanking the path (colliders form the ordained route)
    for (let z = 6; z <= 50; z += 4) {
      this.place('SM_MGK_Hedge_Straight_400', -4.2, z, Math.PI / 2, 1, { collide: true, colSize: [1.2, 4.2] });
      this.place('SM_MGK_Hedge_Straight_400', 4.2, z, Math.PI / 2, 1, { collide: true, colSize: [1.2, 4.2] });
    }
    // Sephiroth clusters: topiary spheres on pedestals along both sides
    let flip = 1;
    for (let z = 10; z <= 44; z += 8.5) {
      this.place('SM_MRK_Pedestal_Square_150', -8.5 * flip, z, 0, 1, { collide: true });
      this.place('SM_MGK_Topiary_Sphere', -8.5 * flip, z, 0, 1, { y: 1.2 });
      this.place('SM_MRK_Pedestal_Square_150', 8.5 * flip, z + 4, 0, 1, { collide: true });
      this.place('SM_MGK_Topiary_Spiral', 8.5 * flip, z + 4, 0, 1, { y: 1.2 });
      flip *= -1;
    }
    // Upward-flowing fountains — navigational landmarks
    this.place('SM_MGK_Fountain_Octagonal', -13, 22, 0, 1, { collide: true, colSize: [5, 5] });
    this.place('SM_MGK_Fountain_Octagonal', 13, 38, 0, 1, { collide: true, colSize: [5, 5] });
    this.place('SM_MGK_Fountain_Round_Small', 0, 52, 0, 1, { collide: true, colSize: [2.5, 2.5] });
    // Benches, lamps, flowerbeds
    this.place('SM_MGK_Bench_Straight_A', -6.5, 16, Math.PI / 2, 1, { collide: true });
    this.place('SM_MGK_Bench_Straight_A', 6.5, 30, -Math.PI / 2, 1, { collide: true });
    for (const [x, z] of [[-5.5, 8], [5.5, 20], [-5.5, 34], [5.5, 46]]) {
      this.place('SM_MGK_GardenLamp', x, z, 0, 1, { collide: true, colSize: [0.5, 0.5] });
    }
    this.place('SM_MGK_Flowerbed_Round', -12, 8, 0, 1.2);
    this.place('SM_MGK_Flowerbed_Round', 12, 14, 0, 1.2);
    for (let i = 0; i < 14; i++) {
      this.place('SM_MSK_FlowerCluster', (Math.random() - 0.5) * 26, 4 + Math.random() * 46, Math.random() * 6, 1);
    }

    // The Angel Terrestrial — feet rooted in earth, wings touching sky, facing the path
    const statue = this.place('SM_AngelTerrestrial', 0, 58, Math.PI, 1, { collide: true, colSize: [3.4, 3.4] });
    this.anchors.statueGarden = statue;

    this.addTrigger(2, 'garden');
    this.addTrigger(46, 'statue-approach');
  }

  buildHedgePath() {
    // Narrow corridor z 55 -> 85, walls at x = ±4.6
    for (let z = 62; z <= 84; z += 4) {
      this.place('SM_MGK_Hedge_Straight_400', -4.6, z, Math.PI / 2, 1.15, { collide: true, colSize: [1.3, 4.4] });
      this.place('SM_MGK_Hedge_Straight_400', 4.6, z, Math.PI / 2, 1.15, { collide: true, colSize: [1.3, 4.4] });
    }
    for (let z = 58; z <= 82; z += 6) {
      this.place('SM_MGK_Path_Straight_300', 0, z, 0, 1.6);
    }
    // Cover: benches + fallen column
    this.place('SM_MGK_Bench_Stone_B', -2.8, 70, 0.3, 1, { collide: true });
    this.place('SM_MGK_Bench_Stone_B', 2.8, 76, -0.2, 1, { collide: true });
    this.place('SM_MRK_Column_Fallen_400', 1.5, 66, 1.1, 1, { collide: true, colSize: [3.5, 1.2] });
    // Thorn barrier that seals retreat once the watchers engage (activated by trigger)
    this.thornBarrier = this.place('SM_MSK_Barrier_ThornStraight_300', 0, 57, 0, 2.9, { enhance: true });
    this.thornBarrier.visible = false;

    this.addTrigger(60, 'first-watchers');
  }

  buildClearing() {
    const cz = 105;
    // Sacred mosaic — the ground remembers (Farsa -10 on step)
    this.anchors.mosaic = new THREE.Vector3(0, 0.02, cz);
    const mosaic = this.place('SM_MSK_RitualCircle_400', 0, cz, 0, 1.25);
    if (mosaic) mosaic.traverse((o) => { if (o.isMesh) o.receiveShadow = true; });

    // Elevation ridges east/west (visual berms)
    for (const [x, z, ry] of [[-14, cz - 4, 0.4], [14, cz + 2, -0.5]]) {
      const berm = new THREE.Mesh(new THREE.SphereGeometry(7, 12, 8), this.mats.earth);
      berm.scale.set(1.4, 0.28, 1);
      berm.position.set(x, 0, z);
      berm.rotation.y = ry;
      berm.receiveShadow = true;
      this.group.add(berm);
    }
    // Broken obelisk hill to the north + columns as cover
    this.place('SM_MRK_Obelisk_400', 0, cz + 16, 0.4, 1, { collide: true, colSize: [1.6, 1.6] });
    this.place('SM_MRK_Column_Broken_A', -7, cz - 6, 0, 1, { collide: true, colSize: [1, 1] });
    this.place('SM_MRK_Column_Broken_A', 7.5, cz + 5, 0.8, 1, { collide: true, colSize: [1, 1] });
    this.place('SM_MRK_Column_CollapsedCluster', -9, cz + 9, 2.1, 1, { collide: true, colSize: [3.4, 2.4] });
    this.place('SM_MRK_RubbleCluster_A', 10, cz - 9, 0, 1, { collide: true, colSize: [2, 2] });
    // Hedge ring around the clearing with two gate openings (N/S)
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 10) {
      const deg = a * 180 / Math.PI;
      if (Math.abs(Math.sin(a)) > 0.92) continue; // leave north/south openings
      const x = Math.cos(a) * 21, z = cz + Math.sin(a) * 21;
      this.place('SM_MGK_Hedge_Straight_400', x, z, -a + Math.PI / 2, 1.1, { collide: true, colSize: [3.6, 1.2] });
    }
    for (let i = 0; i < 10; i++) {
      this.place('SM_MSK_FlowerCluster', (Math.random() - 0.5) * 30, cz + (Math.random() - 0.5) * 34, Math.random() * 6, 1);
    }
    this.addTrigger(88, 'open-fields');
  }

  buildGazebo() {
    const cz = 138;
    // Polished mirror floor — the Masquerade Mirror of the LDD
    const floor = new THREE.Mesh(new THREE.CircleGeometry(9, 36), this.mats.mirror);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(0, 0.03, cz);
    floor.receiveShadow = true;
    this.group.add(floor);
    const rim = new THREE.Mesh(new THREE.RingGeometry(9, 10.2, 36), this.mats.marble);
    rim.rotation.x = -Math.PI / 2;
    rim.position.set(0, 0.02, cz);
    this.group.add(rim);

    // Four pillars + broken dome overhead
    for (const [x, z] of [[-6, cz - 6], [6, cz - 6], [-6, cz + 6], [6, cz + 6]]) {
      this.place('SM_MRK_Column_Intact_400', x, z, 0, 1, { collide: true, colSize: [1, 1] });
    }
    const dome = this.place('SM_MRK_Dome_HalfBroken_800', 0, cz, 0, 1, { y: 4.6 });
    if (dome) dome.rotation.z = 0.12;
    this.place('SM_MRK_RuinedArch_300', 0, cz - 10.5, 0, 1.2, { collide: true, colSize: [1, 1] });
    this.place('SM_MRK_InscribedSlab', -8.5, cz + 3, 0.9, 1, { collide: true, colSize: [1.2, 0.5] });

    this.anchors.gazebo = new THREE.Vector3(0, 0, cz);
    this.addTrigger(128, 'false-peace');
  }

  buildBridge() {
    // 80 m bridge deck (z 150 -> 230): 3 modular GLB segments abreast -> 9 m wide
    for (let z = 156; z <= 228; z += 12) {
      for (const x of [-3, 0, 3]) {
        this.place('SM_MP_Bridge_Straight_300x1200', x, z, 0, 1, { y: -0.45, enhance: true });
      }
    }
    // Continuous railings at the deck edges
    for (let z = 154; z <= 227; z += 3) {
      this.place('SM_MP_BridgeRailing_300', -4.8, z, 0, 1, { y: 0, collide: true, colSize: [0.4, 3.1] });
      this.place('SM_MP_BridgeRailing_300', 4.8, z, 0, 1, { y: 0, collide: true, colSize: [0.4, 3.1] });
    }
    // Bridge pillars down into the pool
    for (let z = 162; z <= 222; z += 20) {
      this.place('SM_MP_Bridge_Pillar', -3.5, z, 0, 1.4, { y: -4 });
      this.place('SM_MP_Bridge_Pillar', 3.5, z, 0, 1.4, { y: -4 });
    }
    // Upward-flowing fountains on marble pads flanking the deck (Snare landmarks)
    for (let z = 158; z <= 226; z += 8) {
      for (const x of [-7.2, 7.2]) {
        const pad = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 2.2, 0.5, 10), this.mats.marble);
        pad.position.set(x, -0.65, z);
        pad.castShadow = true;
        this.group.add(pad);
        const f = this.place('SM_MGK_Fountain_Round_Small', x, z, 0, 0.8, { y: -0.4 });
        if (f) this.fountainsUp.push(f);
      }
    }
    // Sanctuary beacon visible from the far end (purple point light, LDD spec)
    const beacon = new THREE.PointLight(0x8a2be2, 60, 90, 1.8);
    beacon.position.set(0, 6, 247);
    this.group.add(beacon);

    this.anchors.bridgeStart = new THREE.Vector3(0, 0, 152);
    this.anchors.bridgeEnd = new THREE.Vector3(0, 0, 228);
    this.addTrigger(152, 'celestial-snare');
    this.addTrigger(229, 'snare-end');
  }

  buildSanctuary() {
    const cz = 247;
    // Natural cathedral: 8 massive trunks in a circle, canopies interlaced above
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const x = Math.cos(a) * 13, z = cz + Math.sin(a) * 13;
      this.place('SM_MSK_Trunk_Twisted_800', x, z, -a, 1.9, { collide: true, colSize: [2.6, 2.6] });
      this.place('SM_MSK_CanopyCluster', x * 0.55, cz + (z - cz) * 0.55, Math.random() * 6, 2.6, { y: 11 + Math.random() * 2 });
    }
    // Fake god-ray shafts through the vault
    for (let i = 0; i < 5; i++) {
      const shaft = new THREE.Mesh(
        new THREE.CylinderGeometry(0.35, 1.6, 14, 8, 1, true),
        new THREE.MeshBasicMaterial({
          color: 0xffe9bb, transparent: true, opacity: 0.10,
          blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
        })
      );
      shaft.position.set((Math.random() - 0.5) * 10, 7, cz + (Math.random() - 0.5) * 10);
      shaft.rotation.z = 0.22;
      this.group.add(shaft);
    }
    // Central dais + the Angel Terrestrial + Altar of Contemplation
    this.place('SM_MP_Throne_Dais_400', 0, cz + 4, 0, 1.1);
    const statue = this.place('SM_AngelTerrestrial', 0, cz + 6, Math.PI, 0.85, { y: 0.75, collide: true, colSize: [3, 3] });
    this.anchors.statueSanctuary = statue;
    this.place('SM_MSK_Altar_Main_300', 0, cz - 2, Math.PI, 1, { collide: true, colSize: [3, 1.6] });
    this.anchors.altar = new THREE.Vector3(0, 0, cz - 3.4);
    this.place('SM_MSK_SanctuaryArch', 0, cz - 14, 0, 1.2, { collide: true, colSize: [1, 1] });
    this.place('SM_MSK_RootCluster_A', -5, cz + 2, 0.7, 1.4);
    this.place('SM_MSK_RootCluster_A', 5, cz + 3, 2.4, 1.4);
    for (let i = 0; i < 8; i++) {
      this.place('SM_MSK_FlowerCluster', (Math.random() - 0.5) * 18, cz + (Math.random() - 0.5) * 18, Math.random() * 6, 1);
    }
    // Warm interior light
    const warm = new THREE.PointLight(0xffe0a8, 40, 40, 1.6);
    warm.position.set(0, 6, cz);
    this.group.add(warm);

    this.addTrigger(236, 'sanctuary');
  }

  buildAmphitheater() {
    const cz = 280;
    // Stepped stone tiers rising on three sides
    for (let i = 0; i < 5; i++) {
      const r = 13 + i * 3.2;
      const tier = new THREE.Mesh(
        new THREE.CylinderGeometry(r, r, 1.1, 40, 1, false, Math.PI * 0.08, Math.PI * 1.84),
        this.mats.marble
      );
      tier.position.set(0, 0.55 + i * 1.05, cz);
      tier.rotation.y = Math.PI; // seating opening faces the south entrance
      tier.receiveShadow = true;
      tier.castShadow = i < 2;
      this.group.add(tier);
    }
    // Collider ring so the player stays on the stage — gaps S (entrance) and N (exit)
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 12) {
      if (Math.abs(Math.sin(a)) > 0.85) continue;
      const x = Math.cos(a) * 12.4, z = cz + Math.sin(a) * 12.4;
      this.addCollider(x - 1.6, x + 1.6, z - 1.6, z + 1.6, 4);
    }
    // Polished stage
    const stage = new THREE.Mesh(new THREE.CircleGeometry(12.5, 40), this.mats.ivory);
    stage.rotation.x = -Math.PI / 2;
    stage.position.set(0, 0.02, cz);
    stage.receiveShadow = true;
    this.group.add(stage);

    this.anchors.amphitheater = new THREE.Vector3(0, 0, cz);
    this.addTrigger(268, 'host-descends');
  }

  buildThrone() {
    const cz = 322; // plateau center, y = 6
    // Plateau rock mass
    const plateau = new THREE.Mesh(new THREE.CylinderGeometry(30, 36, 6, 24), this.mats.mountainRock);
    plateau.position.set(0, 3, cz);
    plateau.receiveShadow = true;
    this.group.add(plateau);
    // Grand stair from the amphitheater (visual steps matching the ramp)
    this.place('SM_MP_Stair_Wide_600x600', 0, 297.4, Math.PI, 1.7, { y: 0 });
    this.place('SM_MP_Stair_Wide_600x600', 0, 302.6, Math.PI, 1.7, { y: 2.9 });

    // Arena floor
    const arena = new THREE.Mesh(new THREE.CircleGeometry(20, 44), this.mats.marble);
    arena.rotation.x = -Math.PI / 2;
    arena.position.set(0, 6.02, cz);
    arena.receiveShadow = true;
    this.group.add(arena);
    // Arena edge colliders — gaps S (grand stair entrance) and N (ascension exit)
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 16) {
      if (Math.abs(Math.sin(a)) > 0.85) continue;
      const x = Math.cos(a) * 20.4, z = cz + Math.sin(a) * 20.4;
      this.addCollider(x - 1.8, x + 1.8, z - 1.8, z + 1.8, 11);
    }
    // Four pillars at cardinal points
    for (const [x, z] of [[-14, cz], [14, cz], [0, cz - 14], [0, cz + 14]]) {
      this.place('SM_MRK_Column_Intact_600', x, z, 0, 1, { y: 6, collide: true, colSize: [1.3, 1.3] });
    }
    this.place('SM_MRK_Obelisk_700', -10, cz + 10, 0.6, 1, { y: 6, collide: true, colSize: [2, 2] });
    this.place('SM_MRK_Obelisk_700', 10, cz + 10, -0.6, 1, { y: 6, collide: true, colSize: [2, 2] });

    // Throne of roots and stone
    this.place('SM_MP_Throne_Malkuth_Main', 0, cz + 12, Math.PI, 1.3, { y: 6, collide: true, colSize: [2.4, 1.8] });
    this.anchors.throne = new THREE.Vector3(0, 6, cz + 10);

    // Mirror labyrinth: 12 panels in a shifting-maze arrangement (Gabriel phase 1-2)
    const mirrorLayout = [
      [-8, cz - 6, 0], [8, cz - 6, 0], [-8, cz + 2, 0], [8, cz + 2, 0],
      [-4, cz - 2, Math.PI / 2], [4, cz - 2, Math.PI / 2],
      [-12, cz - 2, Math.PI / 4], [12, cz - 2, -Math.PI / 4],
      [-5, cz + 7, Math.PI / 2], [5, cz + 7, Math.PI / 2],
      [-13, cz + 6, 0], [13, cz + 6, 0],
    ];
    mirrorLayout.forEach(([x, z, ry], i) => {
      const name = i % 4 === 3 ? 'SM_MMLK_Mirror_Cracked_A' : 'SM_MMLK_Mirror_Straight_200x300';
      const panel = this.place(name, x, z, ry, 1.15, { y: 6 });
      if (panel) {
        panel.userData.isMirror = true;
        this.mirrorPanels.push(panel);
        const cs = ry === 0 || Math.abs(ry) === Math.PI ? [2.4, 0.6] : [0.6, 2.4];
        const col = { minX: x - cs[0] / 2, maxX: x + cs[0] / 2, minZ: z - cs[1] / 2, maxZ: z + cs[1] / 2, maxY: 10, mirror: true };
        this.colliders.push(col);
        panel.userData.collider = col;
      }
    });
    // Central oculus + ornate posts
    this.place('SM_MMLK_CentralOculus', 0, cz - 10, 0, 1, { y: 6, collide: true, colSize: [1.6, 1.6] });
    for (const [x, z] of [[-16, cz - 10], [16, cz - 10], [-16, cz + 10], [16, cz + 10]]) {
      this.place('SM_MMLK_Post_Ornate', x, z, 0, 1, { y: 6, collide: true, colSize: [0.7, 0.7] });
    }
    // Vortex sky light over the arena
    const vortex = new THREE.PointLight(0xd4af37, 80, 60, 1.7);
    vortex.position.set(0, 18, cz);
    this.group.add(vortex);
    const rootGlow = new THREE.PointLight(0xb3571f, 30, 26, 1.8);
    rootGlow.position.set(0, 6.6, cz + 10);
    this.group.add(rootGlow);

    this.anchors.throneCenter = new THREE.Vector3(0, 6, cz);
    this.addTrigger(306, 'gabriel');
  }

  buildAscension() {
    // Translucent stairway of light rising to the Yesod portal
    for (let i = 0; i < 12; i++) {
      const step = new THREE.Mesh(new THREE.BoxGeometry(6, 0.35, 1.15), this.mats.stairLight);
      step.position.set(0, 6.3 + i * 0.66, 340.6 + i * 1.08);
      this.group.add(step);
    }
    // Portal arch + rune ring + surface
    this.place('SM_MP_PortalSteps', 0, 353.5, 0, 1.4, { y: 13.8 });
    this.place('SM_MP_Portal_Arch_500', 0, 355, 0, 1.3, { y: 14 });
    this.place('SM_MP_Portal_RuneRing', 0, 355, 0, 1.15, { y: 14.6 });
    const surface = this.place('SM_MP_PortalSurface_Preview', 0, 355, 0, 1.15, { y: 14.6 });
    this.anchors.portal = new THREE.Vector3(0, 15.2, 354);
    this.anchors.portalSurface = surface;
    const portalLight = new THREE.PointLight(0x8a2be2, 120, 50, 1.7);
    portalLight.position.set(0, 17, 352);
    this.group.add(portalLight);
    this.anchors.portalLight = portalLight;

    this.addTrigger(352, 'ascension');
  }

  buildBounds() {
    // Level edges — side walls run continuously so the pool can't be flanked
    this.addCollider(-60, -34, -20, 234, 30);
    this.addCollider(34, 60, -20, 234, 30);
    this.addCollider(-60, -36, 234, 400, 30);
    this.addCollider(36, 60, 234, 400, 30);
    this.addCollider(-60, 60, -30, -8, 30);
    this.addCollider(-60, 60, 398, 420, 30);
    // Throne plateau north cliff flanks — only the stair of light exits north
    this.addCollider(-21, -5, 340, 342.5, 14);
    this.addCollider(5, 21, 340, 342.5, 14);
    // Ascension stair rails (invisible; the stair is 6 m wide)
    this.addCollider(-7, -5, 340, 356, 26);
    this.addCollider(5, 7, 340, 356, 26);
  }

  // The Kingdom only allows passage along its ordained lines: each golden
  // barrier opens solely when the trial before it is complete.
  buildGates() {
    this.addGate('watchers', 84.5, 60);   // hedge path -> clearing
    this.addGate('fields', 126.5, 60);    // clearing -> gazebo
    this.addGate('archangel', 150.2, 12); // gazebo -> bridge
    this.addGate('altar', 267.8, 60);     // sanctuary -> amphitheater
    this.addGate('host', 292.6, 60);      // amphitheater -> throne stair
    this.addGate('gabriel', 339.5, 60);   // throne -> ascension
  }

  addGate(id, z, width) {
    const gy = this.groundHeight(0, z);
    const mat = new THREE.MeshBasicMaterial({
      color: 0xd4af37, transparent: true, opacity: 0.16,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, 3.6), mat);
    mesh.position.set(0, gy + 1.8, z);
    this.group.add(mesh);
    const col = { minX: -width / 2, maxX: width / 2, minZ: z - 0.5, maxZ: z + 0.5, maxY: gy + 5 };
    this.colliders.push(col);
    this.gates[id] = { mesh, col, z };
  }

  // Returns the gate center for FX, or null if it was already open
  openGate(id) {
    const g = this.gates[id];
    if (!g) return null;
    this.group.remove(g.mesh);
    g.mesh.geometry.dispose();
    g.mesh.material.dispose();
    const i = this.colliders.indexOf(g.col);
    if (i >= 0) this.colliders.splice(i, 1);
    delete this.gates[id];
    return new THREE.Vector3(0, this.groundHeight(0, g.z) + 1.5, g.z);
  }

  // Thorn barrier seals the hedge path once the watchers engage
  sealHedgePath() {
    if (this.thornBarrier && !this.thornCollider) {
      this.thornBarrier.visible = true;
      this.thornCollider = { minX: -4.5, maxX: 4.5, minZ: 56.4, maxZ: 57.6, maxY: 3 };
      this.colliders.push(this.thornCollider);
    }
  }

  // Drops the seal so a respawned player can re-enter the hedge path
  unsealHedgePath() {
    if (this.thornBarrier) this.thornBarrier.visible = false;
    if (this.thornCollider) {
      const i = this.colliders.indexOf(this.thornCollider);
      if (i >= 0) this.colliders.splice(i, 1);
      this.thornCollider = null;
    }
  }

  // Gabriel phase 3: the labyrinth shatters
  shatterMirrors(fx) {
    for (const panel of this.mirrorPanels) {
      fx.featherBurst(panel.position, 0xdfe8ff, 60, 3);
      panel.visible = false;
      const col = panel.userData.collider;
      const idx = this.colliders.indexOf(col);
      if (idx >= 0) this.colliders.splice(idx, 1);
    }
  }

  update(t, dt) {
    // Divine gates shimmer — a held breath of golden light
    for (const id in this.gates) {
      const g = this.gates[id];
      g.mesh.material.opacity = 0.13 + Math.sin(t * 2.4 + g.z) * 0.06;
    }
    if (this.anchors.portalSurface) {
      this.anchors.portalSurface.rotation.y = t * 0.4;
    }
    if (this.anchors.portalLight) {
      this.anchors.portalLight.intensity = 110 + Math.sin(t * 2.2) * 25;
    }
  }
}
