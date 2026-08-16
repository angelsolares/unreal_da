// Headless smoke test: level construction, systems logic, GLB parsing.
// Run: node test/smoke.mjs
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
let failures = 0;
const ok = (cond, label) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + label);
  if (!cond) failures++;
};

// ---------- 1. MalkuthLevel with mock assets ----------
const { MalkuthLevel } = await import('../src/world/MalkuthLevel.js');

const mockAssets = {
  spawn(name) {
    const g = new THREE.Group();
    g.name = name;
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial());
    mesh.name = name + '_Mesh';
    g.add(mesh);
    return g;
  },
};

const scene = new THREE.Scene();
const level = new MalkuthLevel(scene, mockAssets);
ok(level.colliders.length > 100, `level colliders built (${level.colliders.length})`);
ok(level.triggers.length === 11, `11 zone triggers (${level.triggers.length})`);
ok(level.mirrorPanels.length === 12, `12 mirror panels (${level.mirrorPanels.length})`);
ok(!!level.anchors.altar && !!level.anchors.mosaic && !!level.anchors.bridgeStart && !!level.anchors.portal, 'anchors present');

// ground height profile
ok(level.groundHeight(0, 20) === 0, 'garden floor at y=0');
ok(level.groundHeight(0, 190) === 0, 'bridge deck at y=0');
ok(level.groundHeight(20, 190) === -4, 'pool basin at y=-4');
ok(level.groundHeight(0, 322) === 6, 'throne plateau at y=6');
ok(level.groundHeight(0, 346.5) > 6 && level.groundHeight(0, 346.5) < 14, 'ascension ramp rises');

// collision pushout
const p = new THREE.Vector3(-4.2, 0, 20); // inside a garden hedge collider
level.resolveCollisions(p, 0.42);
ok(Math.abs(p.x) > 4.2 || Math.abs(p.z - 20) > 2, 'hedge collider pushes player out');

// corridors are walkable once their gates open (gating itself is tested below)
level.openGate('altar');
level.openGate('host');
level.openGate('gabriel');

// amphitheater south entrance must be passable (z 267 -> 280, x=0)
let blocked = false;
for (let z = 266; z <= 294; z += 0.5) {
  const q = new THREE.Vector3(0, 0, z);
  const before = q.clone();
  level.resolveCollisions(q, 0.42);
  if (q.distanceTo(before) > 0.01) blocked = true;
}
ok(!blocked, 'amphitheater S->N corridor walkable (gates open)');

// throne plateau: south stair entrance and north ascension exit walkable
blocked = false;
for (let z = 295; z <= 353; z += 0.5) {
  const q = new THREE.Vector3(0, level.groundHeight(0, z), z);
  const before = q.clone();
  level.resolveCollisions(q, 0.42);
  if (q.distanceTo(before) > 0.01) blocked = true;
}
ok(!blocked, 'throne S->N + ascension corridor walkable (gates open)');

// mirror shatter removes colliders
const fxStub = { featherBurst() {} };
const colBefore = level.colliders.length;
level.shatterMirrors(fxStub);
ok(level.colliders.length === colBefore - 12, 'mirror shatter removes 12 colliders');

// divine gates: 6 created, 3 opened above for the corridor tests, 3 remain
ok(Object.keys(level.gates).length === 3, `3 gates remain after opening 3 (${Object.keys(level.gates).length})`);
const gateZ = 84.5;
let blockedByGate = false;
{
  const q = new THREE.Vector3(0, 0, gateZ);
  level.resolveCollisions(q, 0.42);
  blockedByGate = Math.abs(q.z - gateZ) > 0.01;
}
ok(blockedByGate, 'watchers gate blocks passage');
const colBeforeGate = level.colliders.length;
level.openGate('watchers');
ok(level.colliders.length === colBeforeGate - 1 && !level.gates['watchers'], 'opening a gate removes its collider');

// pool flanks are walled — no walking around the Celestial Snare
{
  const q = new THREE.Vector3(38, 0, 190);
  level.resolveCollisions(q, 0.42);
  ok(q.x <= 34.5 || q.x >= 59.5, `pool flank walled at x=38 (pushed to ${q.x.toFixed(1)})`);
}

// thorn seal can be dropped for respawns
level.sealHedgePath();
ok(!!level.thornCollider, 'thorn seal adds collider');
level.unsealHedgePath();
ok(!level.thornCollider, 'thorn seal drops cleanly');

// ---------- 2. Systems ----------
const { Farsa, CelestialSnare, Altar, WaveEncounter } = await import('../src/gameplay/Systems.js');

const farsa = new Farsa();
ok(farsa.state === 'ACEPTADO', 'farsa starts ACEPTADO');
farsa.decay(35, 'test');
ok(farsa.state === 'SOSPECHOSO', 'farsa 65 -> SOSPECHOSO');
farsa.decay(30, 'test');
ok(farsa.state === 'REVELADO', 'farsa 35 -> REVELADO');
farsa.onDeathPenalty();
ok(farsa.maxValue === 90, 'death penalty reduces max farsa');

const playerStub = { pos: new THREE.Vector3(0, 0, 210), hp: 100, tears: 3, heal() {}, damage(v) { this.hp -= v; } };
const audioStub = { rayCharge() {}, rayStrike() {} };
const fxStub2 = { spawnRayTelegraph(pos, t, cb) { cb(pos); } };
const snare = new CelestialSnare(level, fxStub2, audioStub);
snare.start();
snare.update(2, playerStub); // deep bridge: pattern strike includes the player's exact tile
ok(playerStub.hp < 100, 'snare pattern strike damages player on the mark');
const hpBefore = playerStub.hp;
playerStub.pos.set(0, 0, 40); // off the bridge — the Snare ignores the garden
snare.update(5, playerStub);
ok(playerStub.hp === hpBefore, 'snare ignores players off the bridge');

const altar = new Altar(new THREE.Vector3(0, 0, 244));
ok(altar.offerTear(playerStub) === true && playerStub.damageBuff === 1.2, 'tear offering grants buff');

let spawned = 0;
const waves = new WaveEncounter((n) => { spawned += n; return new Array(n); });
waves.start();
ok(spawned === 2, 'wave 1 spawns 2 angels');
waves.update(1, 0);
ok(spawned === 5, 'wave 2 spawns 3 after clear');
waves.update(1, 0);
waves.update(1, 0);
ok(waves.done === true, 'waves complete after 3 clears');

// ---------- 3. Real GLB parsing ----------
const loader = new GLTFLoader();
const parse = (file) => new Promise((res, rej) => {
  const buf = readFileSync(join(root, 'public/models', file));
  loader.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', res, rej);
});

const messenger = await parse('SK_MAP_Messenger.glb');
const boneNames = [];
messenger.scene.traverse((o) => { if (o.isBone) boneNames.push(o.name); });
ok(boneNames.includes('wing_root_l') && boneNames.includes('head'), 'Messenger GLB has wing+head bones');
let skinned = 0;
messenger.scene.traverse((o) => { if (o.isSkinnedMesh) skinned++; });
ok(skinned >= 1, `Messenger GLB has skinned mesh (${skinned})`);

const malakh = await parse('SK_Malakh_Placeholder.glb');
ok(!!malakh.scene.getObjectByName('Malakh_Wing_L') && !!malakh.scene.getObjectByName('Malakh_Wing_R'), 'Malakh GLB has named wings');

const statue = await parse('SM_AngelTerrestrial.glb');
ok(statue.scene.children.length > 0, 'AngelTerrestrial GLB parses');

// ---------- 4. Enemy logic with mock scene ----------
const { Messenger, Archangel } = await import('../src/gameplay/Enemies.js');
const { Gabriel } = await import('../src/gameplay/Gabriel.js');
const assetsStub = { spawn: mockAssets.spawn };
const m = new Messenger(scene, assetsStub, level, new THREE.Vector3(0, 0, 70), { active: true });
ok(m.pos.z === 70 && m.model.position.z === 0, 'angel model at local origin (no double offset)');
const killed = m.damage(999, false);
ok(killed === true && m.dead, 'angel dies and reports kill');

const g = new Gabriel(scene, assetsStub, level, new THREE.Vector3(0, 6, 331));
ok(g.damage(100, false) === false && g.hp === 800, 'Gabriel immune while dormant/dialoguing');
g.bossPhase = 3;
g.damage(100, true); // dark strike in judgment: 1.5x
ok(g.hp === 650, `Gabriel takes 1.5x dark damage in phase 3 (hp=${g.hp})`);
g.damage(9999, false);
ok(g.bossPhase === 4, 'Gabriel crystallizes instead of dying');

console.log(failures === 0 ? '\nALL TESTS PASSED' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
