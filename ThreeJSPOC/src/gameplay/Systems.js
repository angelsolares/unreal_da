import * as THREE from 'three';

// ---------------- Farsa (Masquerade) ----------------
// The signature system: how much Heaven believes the lie.
// 70-100 Aceptado | 40-69 Sospechoso | 0-39 Revelado
export class Farsa extends THREE.EventDispatcher {
  constructor() {
    super();
    this.value = 100;
    this.maxValue = 100;
  }

  get state() {
    if (this.value >= 70) return 'ACEPTADO';
    if (this.value >= 40) return 'SOSPECHOSO';
    return 'REVELADO';
  }

  get color() {
    if (this.value >= 70) return '#a5d66d';
    if (this.value >= 40) return '#e8c547';
    return '#d84a4a';
  }

  decay(amount, cause) {
    if (amount <= 0) return;
    const before = this.state;
    this.value = Math.max(0, this.value - amount);
    this.dispatchEvent({ type: 'changed', cause });
    if (this.state !== before) this.dispatchEvent({ type: 'threshold', state: this.state });
  }

  gain(amount, cause) {
    const before = this.state;
    this.value = Math.min(this.maxValue, this.value + amount);
    this.dispatchEvent({ type: 'changed', cause });
    if (this.state !== before) this.dispatchEvent({ type: 'threshold', state: this.state });
  }

  onAngelKilled() { this.decay(5, 'kill'); }
  onSacredStep() { this.decay(10, 'sacred-ground'); }
  onDeathPenalty() {
    this.maxValue = Math.max(50, this.maxValue - 10);
    this.value = Math.min(this.value, this.maxValue);
  }
}

// ---------------- Celestial Snare ----------------
// Pattern-recognition light rays over the bridge. The pattern follows a
// liturgical rhythm: single -> double -> rapid cross/checkerboard.
export class CelestialSnare {
  constructor(level, fx, audio) {
    this.level = level;
    this.fx = fx;
    this.audio = audio;
    this.active = false;
    this.timer = 0;
    this.strikeCount = 0;
  }

  start() { this.active = true; this.timer = 1.2; this.strikeCount = 0; }
  stop() { this.active = false; }

  update(dt, player) {
    if (!this.active) return;
    // The Snare only judges whoever stands on the bridge
    if (player.pos.z < 148 || player.pos.z > 232) return;
    this.timer -= dt;
    if (this.timer > 0) return;

    const z = player.pos.z;
    const progress = THREE.MathUtils.clamp((z - 150) / 80, 0, 1);
    this.strikeCount++;

    // Rhythm escalates along the bridge (LDD 7.3)
    if (progress < 0.3) {
      this.timer = 3.0;
      this.strikeAt(player, 1);
    } else if (progress < 0.65) {
      this.timer = 2.2;
      this.strikeAt(player, 2);
    } else {
      this.timer = 1.2;
      this.strikeAt(player, this.strikeCount % 2 === 0 ? 3 : 2, true);
    }
  }

  strikeAt(player, count, pattern = false) {
    this.audio.rayCharge();
    const base = player.pos.clone();
    const offsets = pattern
      ? [[0, 0], [2.5, 2], [-2.5, -2], [2.5, -2]].slice(0, count)
      : Array.from({ length: count }, () => [(Math.random() - 0.5) * 6, 2 + Math.random() * 5]);
    for (const [ox, oz] of offsets) {
      const pos = new THREE.Vector3(
        THREE.MathUtils.clamp(base.x + ox, -4.5, 4.5), 0,
        THREE.MathUtils.clamp(base.z + oz, 151, 229)
      );
      this.fx.spawnRayTelegraph(pos, 1.5, (strikePos) => {
        this.audio.rayStrike();
        if (player.pos.distanceTo(strikePos) < 1.6 && Math.abs(player.pos.y) < 1.5) {
          player.damage(25, null, { unblockable: true });
          this.onHitPlayer && this.onHitPlayer();
        }
      });
    }
  }
}

// ---------------- Altar of Contemplation ----------------
export class Altar {
  constructor(pos) {
    this.pos = pos;
    this.restCount = 0;
    // Until the first rest, death returns Malakh to the garden spawn
    this.checkpoint = new THREE.Vector3(0, 0, 2);
  }

  rest(player, farsa) {
    player.heal(100);
    player.tears = 3;
    this.checkpoint.copy(this.pos);
    if (this.restCount > 0) farsa.decay(3, 'over-rest');
    this.restCount++;
  }

  offerTear(player) {
    if (player.tears <= 0) return false;
    player.tears--;
    player.damageBuff = 1.2;
    player.buffTimer = 180;
    return true;
  }
}

// ---------------- The Host Descends (wave encounter) ----------------
export class WaveEncounter {
  constructor(spawnWave) {
    this.spawnWave = spawnWave;
    this.waves = [2, 3, 3];
    this.current = -1;
    this.active = false;
    this.pending = [];
    this.timer = 0;
  }

  start() {
    this.active = true;
    this.current = 0;
    this.pending = this.spawnWave(this.waves[0]);
    this.timer = 40; // next wave on timer or clear, LDD pacing
  }

  update(dt, aliveCount) {
    if (!this.active) return;
    this.timer -= dt;
    if ((aliveCount === 0 || this.timer <= 0) && this.current < this.waves.length - 1) {
      this.current++;
      this.pending = this.spawnWave(this.waves[this.current]);
      this.timer = 40;
    } else if (aliveCount === 0 && this.current === this.waves.length - 1) {
      this.active = false;
      this.done = true;
    }
  }
}
