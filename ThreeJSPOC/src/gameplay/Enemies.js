import * as THREE from 'three';

// Base class for the Third Hierarchy: faceless humanoid perfection.
// Wing bones (wing_root_l/r ...) are flapped procedurally; the head bone
// tracks the player during Observation — the watcher that does not sleep.
export class Angel extends THREE.EventDispatcher {
  constructor(scene, assets, level, assetName, pos, opts = {}) {
    super();
    this.scene = scene;
    this.level = level;
    this.opts = opts;

    // Model stays at local origin — the group carries the world position
    this.model = assets.spawn(assetName);
    this.group = new THREE.Group();
    this.group.position.copy(pos);
    scene.add(this.group);
    if (this.model) this.group.add(this.model);

    // Collect deform bones
    this.bones = {};
    this.restQuat = new Map();
    this.group.traverse((o) => {
      if (o.isBone && /wing|head|spine_03/.test(o.name)) {
        this.bones[o.name] = o;
        this.restQuat.set(o.name, o.quaternion.clone());
      }
    });

    this.pos = this.group.position;
    this.homePos = pos.clone(); // souls rule: enemies return home on player death
    this.radius = opts.radius ?? 0.55;
    this.hp = opts.hp ?? 60;
    this.maxHp = this.hp;
    this.speed = opts.speed ?? 2.6;
    this.damageValue = opts.damage ?? 15;
    this.dead = false;
    this.state = 'patrol';   // patrol|observe|chase|attack|stunned|dead
    this.stateT = 0;
    this.yaw = opts.yaw ?? 0;
    this.hoverPhase = Math.random() * Math.PI * 2;
    this.patrol = opts.patrol ?? null;
    this.patrolIdx = 0;
    this.attackCooldown = 0;
    this.stunCooldown = 6;
    this.aggro = false;
    this.hitFlash = 0;
    this.active = opts.active ?? true; // dormant until its beat triggers
    this.called = false;               // reinforcement call already used

    if (!this.active) this.group.visible = false;

    // Face of light: small emissive sphere where a face should be
    const faceMat = new THREE.MeshStandardMaterial({
      color: 0xfff6dd, emissive: 0xffedb8, emissiveIntensity: 2.4,
    });
    this.face = new THREE.Mesh(new THREE.SphereGeometry(0.09 * (opts.faceScale ?? 1), 10, 8), faceMat);
    this.face.position.set(0, (opts.faceHeight ?? 1.75), 0.12);
    this.group.add(this.face);

    // Floating HP bar: camera-facing sprites, shown once the angel is engaged
    if (opts.hpBar !== false) {
      this.hpBarBg = new THREE.Sprite(new THREE.SpriteMaterial({
        color: 0x140f06, depthTest: false, transparent: true, opacity: 0.72,
      }));
      this.hpBarBg.scale.set(0.94, 0.1, 1);
      this.hpBarBg.renderOrder = 90;
      this.hpBarFill = new THREE.Sprite(new THREE.SpriteMaterial({
        color: 0xe8d48a, depthTest: false, transparent: true, opacity: 0.95,
      }));
      this.hpBarFill.scale.set(0.88, 0.062, 1);
      this.hpBarFill.renderOrder = 91;
      const barY = (opts.faceHeight ?? 1.75) + 0.55;
      this.hpBarBg.position.set(0, barY, 0);
      this.hpBarFill.position.set(0, barY, 0);
      this.hpBarBg.visible = this.hpBarFill.visible = false;
      this.group.add(this.hpBarBg, this.hpBarFill);
    }
  }

  setActive(v) {
    this.active = v;
    this.group.visible = v && !this.dead;
  }

  damage(amount, isDark = false) {
    if (this.dead) return false;
    // Light shield: only dark strikes pass
    if (this.shielded && !isDark) {
      this.dispatchEvent({ type: 'shield-block' });
      return false;
    }
    if (this.shielded && isDark) this.breakShield();
    this.hp -= amount;
    this.hitFlash = 0.18;
    this.aggro = true;
    this.dispatchEvent({ type: 'damaged', amount });
    if (this.hp <= 0) {
      this.die();
      return true;
    }
    if (this.state !== 'attack') {
      this.state = 'chase';
    }
    return false;
  }

  breakShield() {
    this.shielded = false;
    if (this.shieldMesh) {
      this.scene.remove(this.shieldMesh);
      this.shieldMesh = null;
    }
    this.dispatchEvent({ type: 'shield-break' });
  }

  die() {
    this.dead = true;
    this.state = 'dead';
    this.group.visible = false;
    this.dispatchEvent({ type: 'died', pos: this.pos.clone(), angel: this });
  }

  // Shared per-frame behavior
  updateAngel(dt, player, farsa, audio) {
    if (this.dead || !this.active) return;
    const t = performance.now() / 1000;
    this.attackCooldown = Math.max(0, this.attackCooldown - dt);

    // Hover: angels do not walk — they float (GDD audio rule: no footsteps)
    this.model.position.y = 0.25 + Math.sin(t * 1.6 + this.hoverPhase) * 0.12;

    // Wing flap from bones
    const flapSpeed = this.state === 'chase' || this.state === 'attack' ? 7.5 : 2.2;
    const flapAmp = this.state === 'chase' || this.state === 'attack' ? 0.55 : 0.18;
    const flap = Math.sin(t * flapSpeed + this.hoverPhase) * flapAmp;
    for (const side of ['l', 'r']) {
      const root = this.bones['wing_root_' + side];
      if (root) {
        const rest = this.restQuat.get('wing_root_' + side);
        root.quaternion.copy(rest);
        root.rotateZ((side === 'l' ? 1 : -1) * flap);
      }
      const w1 = this.bones['wing_01_' + side];
      if (w1) {
        const rest = this.restQuat.get('wing_01_' + side);
        w1.quaternion.copy(rest);
        w1.rotateZ((side === 'l' ? 1 : -1) * flap * 0.5);
      }
    }

    // Hit flash
    if (this.hitFlash > 0) {
      this.hitFlash -= dt;
      this.face.material.emissiveIntensity = 6;
    } else if (this.state === 'attack' && !this.didHit) {
      this.face.material.emissiveIntensity = 5.5; // windup glare — dodge now
    } else {
      this.face.material.emissiveIntensity = 2.4;
    }

    // HP bar: visible while engaged, fill tracks remaining life
    if (this.hpBarBg) {
      const engaged = this.hp < this.maxHp || this.state === 'chase' || this.state === 'attack';
      this.hpBarBg.visible = this.hpBarFill.visible = engaged;
      if (engaged) this.hpBarFill.scale.x = 0.88 * Math.max(this.hp / this.maxHp, 0);
    }

    const toPlayer = player.pos.clone().sub(this.pos);
    toPlayer.y = 0;
    const dist = toPlayer.length();

    // Farsa gates hostility: the Heaven trusts the disguise while it holds
    const suspicious = farsa.value < 70;
    const revealed = farsa.value < 40;

    switch (this.state) {
      case 'patrol': {
        if (this.patrol && this.patrol.length > 1) {
          const target = this.patrol[this.patrolIdx];
          const to = target.clone().sub(this.pos); to.y = 0;
          if (to.length() < 0.6) {
            this.patrolIdx = (this.patrolIdx + 1) % this.patrol.length;
          } else {
            to.normalize();
            this.pos.addScaledVector(to, this.speed * 0.5 * dt);
            this.yaw = Math.atan2(to.x, to.z);
          }
        }
        // Observation: heads tilt in unison toward the intruder
        if (dist < 10 && !revealed) {
          this.state = 'observe';
          this.stateT = 1.4;
        } else if (dist < 12 && revealed) {
          this.becomeHostile(audio);
        }
        break;
      }
      case 'observe': {
        this.yaw = Math.atan2(toPlayer.x, toPlayer.z);
        this.stateT -= dt;
        if (revealed || this.aggro) this.becomeHostile(audio);
        else if (this.stateT <= 0) this.state = 'patrol';
        break;
      }
      case 'chase': {
        this.yaw = Math.atan2(toPlayer.x, toPlayer.z);
        if (dist > this.attackRange()) {
          this.pos.addScaledVector(toPlayer.normalize(), this.speed * dt);
        } else if (this.attackCooldown <= 0) {
          this.state = 'attack';
          this.stateT = this.attackWindup();
          this.didHit = false;
        }
        break;
      }
      case 'attack': {
        this.yaw = Math.atan2(toPlayer.x, toPlayer.z);
        this.stateT -= dt;
        if (!this.didHit && this.stateT <= this.attackWindup() * 0.45) {
          this.didHit = true;
          if (dist < this.attackRange() + 0.4) {
            const dir = toPlayer.clone().normalize();
            player.damage(this.damageValue, dir);
            this.dispatchEvent({ type: 'attack-hit' });
          }
        }
        if (this.stateT <= 0) {
          this.state = 'chase';
          this.attackCooldown = this.attackRate();
        }
        break;
      }
      case 'stunned': {
        this.stateT -= dt;
        if (this.stateT <= 0) this.state = 'chase';
        break;
      }
    }

    // Head tracks the player while observed — subtle wrongness
    const head = this.bones['head'];
    if (head && dist < 14) {
      const rest = this.restQuat.get('head');
      head.quaternion.copy(rest);
      const tilt = this.state === 'observe' ? 0.22 : 0;
      head.rotateZ(tilt);
    }

    this.group.rotation.y = this.yaw;
    this.level.resolveCollisions(this.pos, this.radius);
    const gh = this.level.groundHeight(this.pos.x, this.pos.z);
    this.pos.y = Math.max(gh, this.pos.y - 4 * dt) ;
    if (this.pos.y < gh) this.pos.y = gh;
  }

  becomeHostile(audio) {
    if (this.state !== 'chase' && this.state !== 'attack') {
      this.state = 'chase';
      this.dispatchEvent({ type: 'aggro' });
    }
  }

  attackRange() { return 1.9; }
  attackRate() { return 1.2; }
  attackWindup() { return 0.7; }
}

// ---------------- Angel Messenger (Malkuth grunt) ----------------
export class Messenger extends Angel {
  constructor(scene, assets, level, pos, opts = {}) {
    super(scene, assets, level, 'SK_MAP_Messenger', pos, {
      hp: 60, speed: 2.7, damage: 15, radius: 0.5, faceHeight: 1.78, ...opts,
    });
    this.trumpetTimer = 8;
  }

  update(dt, player, farsa, audio) {
    super.updateAngel(dt, player, farsa, audio);
    if (this.dead || !this.active) return;
    // Trumpet stun: pure tone, no breath — once every 8 s in combat
    if (this.state === 'chase' || this.state === 'attack') {
      this.trumpetTimer -= dt;
      if (this.trumpetTimer <= 0) {
        this.trumpetTimer = 8;
        const dist = this.pos.distanceTo(player.pos);
        if (dist < 7) {
          player.stun(0.8);
          audio.trumpetStun();
          this.dispatchEvent({ type: 'trumpet' });
        }
      }
    }
  }
}

// ---------------- Archangel (elite guardian) ----------------
export class Archangel extends Angel {
  constructor(scene, assets, level, pos, opts = {}) {
    super(scene, assets, level, opts.assetName ?? 'SK_MAP_Archangel', pos, {
      hp: 400, speed: 1.7, damage: 35, radius: 0.7, faceHeight: 2.1, faceScale: 1.3, ...opts,
    });
    this.assets = assets;
    this.shielded = false;
    this.shieldMesh = null;
    this.beamTimer = 12;
    this.phase = 1;
    // Sword of white fire
    this.blade = assets.spawn('SM_MAP_Sword_Ceremonial', { scale: 1.5 });
    if (this.blade) {
      this.blade.traverse((o) => {
        if (o.isMesh) {
          o.material = new THREE.MeshStandardMaterial({
            color: 0xfff6dd, emissive: 0xffedb8, emissiveIntensity: 2.0,
          });
        }
      });
      this.blade.position.set(0.5, 1.3, 0.15);
      this.blade.rotation.x = Math.PI / 2;
      this.group.add(this.blade);
    }
  }

  raiseShield() {
    this.shielded = true;
    const geo = new THREE.SphereGeometry(1.6, 18, 12);
    const mat = new THREE.MeshBasicMaterial({
      color: 0xfff3c8, transparent: true, opacity: 0.28,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
    });
    this.shieldMesh = new THREE.Mesh(geo, mat);
    this.shieldMesh.position.set(0, 1.4, 0);
    this.group.add(this.shieldMesh);
    this.dispatchEvent({ type: 'shield-up' });
  }

  attackRange() { return 2.6; }
  attackRate() { return 2.5; }
  attackWindup() { return 1.1; }

  update(dt, player, farsa, audio, fx) {
    super.updateAngel(dt, player, farsa, audio);
    if (this.dead || !this.active) return;

    // Phases per LDD: shield at 70%, judgment beam at 40%
    const hpFrac = this.hp / this.maxHp;
    if (this.phase === 1 && hpFrac <= 0.7) {
      this.phase = 2;
      this.raiseShield();
    }
    if (this.phase === 2 && hpFrac <= 0.4) {
      this.phase = 3;
      this.speed *= 1.2;
    }
    if (this.phase >= 3 && (this.state === 'chase' || this.state === 'attack')) {
      this.beamTimer -= dt;
      if (this.beamTimer <= 0 && fx) {
        this.beamTimer = 12;
        audio.rayCharge();
        fx.spawnRayTelegraph(player.pos.clone(), 1.5, (strikePos) => {
          audio.rayStrike();
          if (player.pos.distanceTo(strikePos) < 1.6) {
            player.damage(20, null, { unblockable: true });
          }
        });
        this.dispatchEvent({ type: 'judgment-beam' });
      }
    }
    if (this.shieldMesh) {
      this.shieldMesh.rotation.y += dt * 0.8;
      this.shieldMesh.material.opacity = 0.22 + Math.sin(performance.now() / 300) * 0.08;
    }
  }
}
