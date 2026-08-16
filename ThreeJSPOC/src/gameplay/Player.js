import * as THREE from 'three';

const WALK = 4.2, SPRINT = 6.4, JUMP_V = 7.2, GRAVITY = 18;
const DODGE_SPEED = 9.5, DODGE_TIME = 0.34;

// Malakh — the demon wearing a saint. Third-person souls-like controller.
export class Player extends THREE.EventDispatcher {
  constructor(scene, assets, level, camera) {
    super();
    this.level = level;
    this.camera = camera;
    this.scene = scene;

    this.group = new THREE.Group();
    scene.add(this.group);

    // Model
    this.model = assets.spawn('SK_Malakh_Placeholder');
    this.group.add(this.model);
    this.wingL = this.model.getObjectByName('Malakh_Wing_L');
    this.wingR = this.model.getObjectByName('Malakh_Wing_R');
    this.wingRestL = this.wingL ? this.wingL.rotation.clone() : null;
    this.wingRestR = this.wingR ? this.wingR.rotation.clone() : null;

    // Shadow blade: ceremonial sword on a procedural swing pivot.
    // Re-materialed as an umbral weapon — dark violet against the pale Kingdom.
    this.weaponPivot = new THREE.Group();
    this.weaponPivot.position.set(0.38, 1.05, 0.12);
    this.group.add(this.weaponPivot);
    this.sword = assets.spawn('SM_MAP_Sword_Ceremonial', { scale: 1.15 });
    if (this.sword) {
      this.sword.traverse((o) => {
        if (o.isMesh) {
          o.material = new THREE.MeshStandardMaterial({
            color: 0x1a1024, roughness: 0.3, metalness: 0.75,
            emissive: 0x8a2be2, emissiveIntensity: 0.55,
          });
        }
      });
      this.sword.rotation.x = Math.PI / 2; // blade tip up
      this.sword.rotation.z = 0.12;
      this.weaponPivot.add(this.sword);
    }

    // State
    this.pos = new THREE.Vector3(0, 0, 4);
    this.vel = new THREE.Vector3();
    this.yaw = 0;            // facing
    this.camYaw = 0;         // orbit
    this.camPitch = 0.32;
    this.onGround = true;

    this.hp = 100; this.maxHp = 100;
    this.stamina = 100; this.maxStamina = 100;
    this.staminaDelay = 0;
    this.tears = 3;
    this.corruptio = 0;
    this.damageBuff = 1;
    this.buffTimer = 0;

    this.state = 'idle';     // idle|move|dodge|attack|block|hit|dead
    this.stateT = 0;
    this.attackKind = null;  // light|heavy|lunge
    this.attackHits = new Set();
    this.comboStep = 0;
    this.comboWindow = 0;
    this.iframes = 0;
    this.lungeDir = new THREE.Vector3();
    this.blocking = false;
    this.parryWindow = 0;
    this.dead = false;
    this.glide = false;
    this.glideUnlocked = false;
  }

  get center() { return this.pos.clone().add(new THREE.Vector3(0, 1.1, 0)); }

  damage(amount, fromDir = null, opts = {}) {
    if (this.dead || this.iframes > 0) return false;
    // Block: reduces 60%, drains stamina; perfect parry in first 0.2 s
    if (this.blocking && !opts.unblockable) {
      const facing = new THREE.Vector3(Math.sin(this.yaw), 0, Math.cos(this.yaw));
      if (fromDir && facing.dot(fromDir.clone().negate()) > 0.2) {
        if (this.parryWindow > 0) {
          this.dispatchEvent({ type: 'parry' });
          return false;
        }
        this.stamina = Math.max(0, this.stamina - amount * 0.8);
        amount *= 0.4;
        if (this.stamina <= 0) this.stagger();
      } else if (fromDir) {
        // hit from behind while blocking
      }
    }
    this.hp -= amount;
    this.dispatchEvent({ type: 'damaged', amount });
    if (this.hp <= 0) {
      this.hp = 0;
      this.die();
    } else if (!this.blocking) {
      this.state = 'hit';
      this.stateT = 0.28;
    }
    return true;
  }

  stagger() {
    this.state = 'hit';
    this.stateT = 0.8;
    this.blocking = false;
  }

  stun(t) {
    if (this.dead) return;
    this.state = 'hit';
    this.stateT = t;
    this.blocking = false;
  }

  die() {
    if (this.dead) return;
    this.dead = true;
    this.state = 'dead';
    this.dispatchEvent({ type: 'died' });
  }

  respawn(at) {
    this.pos.copy(at);
    this.hp = this.maxHp;
    this.stamina = this.maxStamina;
    this.tears = 3;
    this.dead = false;
    this.state = 'idle';
    this.vel.set(0, 0, 0);
  }

  heal(v) { this.hp = Math.min(this.maxHp, this.hp + v); }

  spendStamina(v) {
    this.stamina = Math.max(0, this.stamina - v);
    this.staminaDelay = 1.1;
  }

  tryAttack(kind, enemies, farsa) {
    if (this.dead || this.state === 'dodge' || this.state === 'hit') return;
    if (kind === 'light' && this.stamina < 10) return;
    if (kind === 'heavy' && this.stamina < 25) return;
    this.state = 'attack';
    this.attackKind = kind;
    this.attackHits.clear();
    if (kind === 'light') {
      this.spendStamina(10);
      this.stateT = 0.42;
      this.comboStep = this.comboWindow > 0 ? (this.comboStep + 1) % 3 : 0;
      this.comboWindow = 0.9;
    } else {
      this.spendStamina(25);
      this.stateT = 0.78;
    }
    this.dispatchEvent({ type: 'attack-start', kind });
  }

  tryLunge(farsa) {
    if (this.corruptio < 30 || this.state === 'dodge' || this.dead) return false;
    this.corruptio -= 30;
    this.state = 'attack';
    this.attackKind = 'lunge';
    this.attackHits.clear();
    this.stateT = 0.5;
    this.lungeDir.set(Math.sin(this.yaw), 0, Math.cos(this.yaw));
    farsa.decay(5, 'dark-ability');
    this.dispatchEvent({ type: 'lunge' });
    return true;
  }

  tryDodge() {
    if (this.state === 'dodge' || this.stamina < 15 || this.dead) return;
    this.spendStamina(15);
    this.state = 'dodge';
    this.stateT = DODGE_TIME;
    this.iframes = 0.32;
    this.blocking = false;
    this.dispatchEvent({ type: 'dodge' });
  }

  update(dt, input, enemies, farsa) {
    if (this.dead) return;

    // ---- camera orbit from mouse
    this.camYaw -= input.mouseDX * 0.0026;
    this.camPitch = THREE.MathUtils.clamp(this.camPitch + input.mouseDY * 0.0022, -0.5, 1.1);

    // ---- timers
    this.iframes = Math.max(0, this.iframes - dt);
    this.parryWindow = Math.max(0, this.parryWindow - dt);
    this.comboWindow = Math.max(0, this.comboWindow - dt);
    this.buffTimer = Math.max(0, this.buffTimer - dt);
    if (this.buffTimer <= 0) this.damageBuff = 1;
    this.staminaDelay -= dt;
    if (this.staminaDelay <= 0 && !this.blocking) {
      this.stamina = Math.min(this.maxStamina, this.stamina + 15 * dt);
    }

    // ---- movement input (camera relative)
    const fwd = new THREE.Vector3(-Math.sin(this.camYaw), 0, -Math.cos(this.camYaw));
    const right = new THREE.Vector3(-fwd.z, 0, fwd.x);
    const move = new THREE.Vector3();
    if (input.down('KeyW')) move.add(fwd);
    if (input.down('KeyS')) move.sub(fwd);
    if (input.down('KeyD')) move.add(right);
    if (input.down('KeyA')) move.sub(right);
    const hasMove = move.lengthSq() > 0;
    if (hasMove) move.normalize();

    // ---- block
    const wasBlocking = this.blocking;
    this.blocking = input.mouseDown(2) && this.state !== 'dodge' && this.state !== 'attack' && this.stamina > 0;
    if (this.blocking && !wasBlocking) this.parryWindow = 0.2;
    if (this.blocking) this.stamina = Math.max(0, this.stamina - 4 * dt);

    // ---- state machine
    if (this.state === 'hit' || this.state === 'attack' || this.state === 'dodge') {
      this.stateT -= dt;
      if (this.stateT <= 0) this.state = hasMove ? 'move' : 'idle';
    }

    const sprinting = input.down('ShiftLeft') && hasMove && this.stamina > 0 && !this.blocking;
    if (sprinting) this.spendStamina(10 * dt);

    let speed = this.blocking ? WALK * 0.45 : sprinting ? SPRINT : WALK;

    if (this.state === 'dodge') {
      const dir = hasMove ? move : new THREE.Vector3(Math.sin(this.yaw), 0, Math.cos(this.yaw));
      this.vel.x = dir.x * DODGE_SPEED;
      this.vel.z = dir.z * DODGE_SPEED;
      this.yaw = Math.atan2(dir.x, dir.z);
    } else if (this.state === 'attack' && this.attackKind === 'lunge') {
      this.vel.x = this.lungeDir.x * 16;
      this.vel.z = this.lungeDir.z * 16;
    } else if (this.state === 'hit') {
      this.vel.x *= 0.8; this.vel.z *= 0.8;
    } else if (hasMove && this.state !== 'attack') {
      this.vel.x = move.x * speed;
      this.vel.z = move.z * speed;
      this.yaw = Math.atan2(move.x, move.z);
      if (this.state === 'idle') this.state = 'move';
    } else {
      this.vel.x *= 0.7; this.vel.z *= 0.7;
      if (this.state === 'move') this.state = 'idle';
    }

    // ---- jump & gravity
    if (input.justPressed('Space') && this.onGround && this.stamina >= 10 && this.state !== 'dodge') {
      this.vel.y = JUMP_V;
      this.onGround = false;
      this.spendStamina(10);
    }
    // Glide (unlocked after Gabriel): hold Space in air
    this.glide = !this.onGround && this.vel.y < 0 && input.down('Space') && this.glideUnlocked;
    this.vel.y -= GRAVITY * dt * (this.glide ? 0.28 : 1);

    // ---- integrate
    this.pos.x += this.vel.x * dt;
    this.pos.z += this.vel.z * dt;
    this.pos.y += this.vel.y * dt;

    // ---- ground
    const gh = this.level.groundHeight(this.pos.x, this.pos.z);
    if (this.pos.y <= gh) {
      this.pos.y = gh;
      this.vel.y = 0;
      this.onGround = true;
    } else if (this.pos.y > gh + 0.05) {
      this.onGround = false;
    }

    // ---- collisions
    this.level.resolveCollisions(this.pos);

    // ---- attack hit detection
    if (this.state === 'attack') {
      const elapsed = this.attackDuration() - this.stateT;
      const active = this.attackKind === 'light' ? (elapsed > 0.12 && elapsed < 0.3)
        : this.attackKind === 'heavy' ? (elapsed > 0.35 && elapsed < 0.62)
        : true; // lunge active throughout
      if (active) this.applyHits(enemies, farsa);
    }

    // ---- visuals
    this.group.position.copy(this.pos);
    this.group.rotation.y = this.yaw;
    this.animate(dt);

    // ---- camera follow
    const camDist = 4.6, camHeight = 1.9;
    const cx = this.pos.x + Math.sin(this.camYaw) * Math.cos(this.camPitch) * camDist;
    const cz = this.pos.z + Math.cos(this.camYaw) * Math.cos(this.camPitch) * camDist;
    const cy = this.pos.y + camHeight + Math.sin(this.camPitch) * camDist;
    const camPos = new THREE.Vector3(cx, Math.max(cy, this.level.groundHeight(cx, cz) + 0.5), cz);
    this.camera.position.lerp(camPos, 1 - Math.pow(0.0001, dt));
    const look = this.pos.clone().add(new THREE.Vector3(0, 1.5, 0));
    this.camera.lookAt(look);
  }

  attackDuration() {
    return this.attackKind === 'light' ? 0.42 : this.attackKind === 'heavy' ? 0.78 : 0.5;
  }

  attackDamage() {
    const base = this.attackKind === 'light' ? 20 : this.attackKind === 'heavy' ? 45 : 60;
    return base * this.damageBuff;
  }

  applyHits(enemies, farsa) {
    const reach = this.attackKind === 'lunge' ? 1.8 : 2.1;
    const facing = new THREE.Vector3(Math.sin(this.yaw), 0, Math.cos(this.yaw));
    for (const e of enemies) {
      if (e.dead || e.active === false || this.attackHits.has(e)) continue;
      const to = e.pos.clone().sub(this.pos);
      to.y = 0;
      const dist = to.length();
      if (dist > reach + e.radius) continue;
      if (this.attackKind !== 'lunge' && facing.dot(to.normalize()) < 0.35) continue;
      this.attackHits.add(e);
      const killed = e.damage(this.attackDamage(), this.attackKind === 'lunge');
      this.dispatchEvent({ type: 'hit-enemy', enemy: e, killed });
      if (killed) {
        this.corruptio = Math.min(100, this.corruptio + 15);
        farsa.onAngelKilled(e);
      }
    }
  }

  animate(dt) {
    const t = performance.now() / 1000;
    // Wing behavior: folded at rest, spread on dodge/jump/lunge
    if (this.wingL && this.wingR) {
      const spread = (this.state === 'dodge' || !this.onGround || this.attackKind === 'lunge' && this.state === 'attack') ? 1 : 0;
      this._wingK = THREE.MathUtils.lerp(this._wingK ?? 0, spread, dt * 8);
      const flap = Math.sin(t * (this.glide ? 3 : 9)) * 0.35 * this._wingK;
      this.wingL.rotation.set(
        this.wingRestL.x - 0.5 * this._wingK,
        this.wingRestL.y + (0.95 + flap) * this._wingK,
        this.wingRestL.z + 0.25 * this._wingK
      );
      this.wingR.rotation.set(
        this.wingRestR.x - 0.5 * this._wingK,
        this.wingRestR.y - (0.95 + flap) * this._wingK,
        this.wingRestR.z - 0.25 * this._wingK
      );
    }
    // Sword swing arcs
    if (this.state === 'attack') {
      const k = 1 - this.stateT / this.attackDuration();
      if (this.attackKind === 'light') {
        const dir = this.comboStep % 2 === 0 ? 1 : -1;
        this.weaponPivot.rotation.y = THREE.MathUtils.lerp(-1.4 * dir, 1.4 * dir, k);
        this.weaponPivot.rotation.x = -0.4;
      } else if (this.attackKind === 'heavy') {
        this.weaponPivot.rotation.x = THREE.MathUtils.lerp(-2.4, 0.9, k);
        this.weaponPivot.rotation.y = 0;
      } else {
        this.weaponPivot.rotation.x = 1.2;
        this.weaponPivot.rotation.y = 0;
      }
    } else if (this.blocking) {
      // Guard pose: blade raised across the body
      this.weaponPivot.rotation.x = -0.85;
      this.weaponPivot.rotation.y = 0.55;
      this.weaponPivot.rotation.z = 0.3;
    } else {
      this.weaponPivot.rotation.set(0, 0, 0);
    }
    // Dodge roll
    if (this.state === 'dodge') {
      const k = 1 - this.stateT / DODGE_TIME;
      this.model.rotation.x = k * Math.PI * 2;
    } else {
      this.model.rotation.x = 0;
    }
    // Idle breathing / walk bob
    const bob = this.state === 'move' ? Math.abs(Math.sin(t * 9)) * 0.05 : Math.sin(t * 1.8) * 0.015;
    this.model.position.y = bob;
  }
}
