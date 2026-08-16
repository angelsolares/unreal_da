import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const MODEL_PATH = './models/';

// Loads every GLB once, then hands out cheap clones.
// Skinned prototypes are cloned with SkeletonUtils so bones stay functional.
export class Assets {
  constructor() {
    this.prototypes = new Map();
    this.loader = new GLTFLoader();
  }

  async loadAll(names, onProgress) {
    let done = 0;
    await Promise.all(names.map(async (name) => {
      const gltf = await this.loader.loadAsync(MODEL_PATH + name + '.glb');
      const root = gltf.scene;
      root.traverse((o) => {
        if (o.isMesh || o.isSkinnedMesh) {
          o.castShadow = true;
          o.receiveShadow = true;
          if (o.material) {
            o.material.side = THREE.FrontSide;
          }
        }
      });
      this.prototypes.set(name, root);
      done++;
      if (onProgress) onProgress(done / names.length);
    }));
  }

  // Returns a clone positioned/rotated/scaled. overrideMaterial is optional.
  spawn(name, { position = [0, 0, 0], rotationY = 0, scale = 1, materialOverride = null } = {}) {
    const proto = this.prototypes.get(name);
    if (!proto) {
      console.warn('Missing asset:', name);
      return null;
    }
    const hasSkin = !!proto.getObjectByProperty('isSkinnedMesh', true);
    const clone = hasSkin ? SkeletonUtils.clone(proto) : proto.clone(true);
    clone.position.set(...position);
    clone.rotation.y = rotationY;
    if (scale !== 1) clone.scale.setScalar(scale);
    if (materialOverride) {
      clone.traverse((o) => { if (o.isMesh) o.material = materialOverride; });
    }
    return clone;
  }

  get(name) { return this.prototypes.get(name); }
}

// Palette from LDD Malkuth v3 / Art Bible V2.
export const PALETTE = {
  gardenGreen: 0x7cb342,
  paleGold: 0xd4af37,
  pureWhite: 0xffffff,
  creamStone: 0xf5f5dc,
  deepBrown: 0x5d4037,
  shadowPurple: 0x4a148c,
  // Art Bible V2 Malkuth ramp
  earth: 0x5c3b24,
  bark: 0x8a6845,
  grass: 0x6f8f45,
  marble: 0xd8c7a1,
  ivory: 0xf3e9d2,
};
