import * as THREE from 'three';
import { Archangel } from './Enemies.js';

// Gabriel of the Gates — not a fight of strength but of patience.
// Phase 1: The Labyrinth (dialogue trial). Phase 2: The Doubt (mirror-gaze drain).
// Phase 3: The Judgment (shattered arena, open combat).
const QUESTIONS = [
  {
    text: '¿Qué te trae al Reino, alma penitente?',
    options: [
      { label: 'Busco redención.', farsa: 0, reply: 'La redención es la moneda del Reino. Procede.' },
      { label: 'Busco paso. Nada más.', farsa: -2, reply: 'Franqueza curiosa en un penitente. Procede… por ahora.' },
      { label: '(Silencio)', farsa: -5, reply: 'El silencio también responde. Te observaré.' },
    ],
  },
  {
    text: '¿Cuándo fue la última vez que oraste?',
    options: [
      { label: 'Cada amanecer, con humildad.', farsa: 0, reply: 'La humildad abre más puertas que la fuerza.' },
      { label: 'No necesito orar.', farsa: -12, trap: true, reply: 'La arrogancia es una llave que no cabe en esta cerradura.' },
      { label: '(Silencio)', farsa: -5, reply: 'Tus pasos son demasiado silenciosos, alma.' },
    ],
  },
  {
    text: '¿A quién sirves?',
    options: [
      { label: 'Al orden divino. A la Luz.', farsa: 0, reply: 'Entonces camina en la Luz… si puedes.' },
      { label: 'A mí mismo.', farsa: -12, trap: true, reply: 'Tu sombra es demasiado larga para servir a la Luz.' },
      { label: '(Silencio)', farsa: -5, reply: 'La duda te delata, Malakh.' },
    ],
  },
];

export class Gabriel extends Archangel {
  constructor(scene, assets, level, pos) {
    super(scene, assets, level, pos, { active: false, assetName: 'SK_MAP_Gabriel_Base', hpBar: false });
    this.hp = 800;
    this.maxHp = 800;
    this.damageValue = 40;
    this.speed = 1.9;
    this.bossPhase = 0;      // 0 dormant, 1 labyrinth, 2 doubt, 3 judgment, 4 defeated
    this.questionIdx = 0;
    this.mirrorGazeT = 0;
    this.shieldRegen = 15;
    this.defeatT = 0;
  }

  // Called by the game when the boss trigger fires
  beginEncounter(hud, farsa, audio) {
    this.setActive(true);
    this.bossPhase = 1;
    this.questionIdx = 0;
    this.askQuestion(hud, farsa, audio);
  }

  askQuestion(hud, farsa, audio) {
    const q = QUESTIONS[this.questionIdx];
    hud.showDialogue('Gabriel de las Puertas', q.text, q.options, (opt) => {
      farsa.decay(Math.abs(opt.farsa), 'gabriel-answer');
      hud.showSubtitle(`Gabriel: «${opt.reply}»`, 3.5);
      if (opt.trap) this.dispatchEvent({ type: 'gabriel-trap' });
      this.questionIdx++;
      if (this.questionIdx < QUESTIONS.length) {
        setTimeout(() => this.askQuestion(hud, farsa, audio), 2200);
      } else {
        setTimeout(() => this.startDoubt(), 2400);
      }
    });
  }

  startDoubt() {
    this.bossPhase = 2;
    this.aggro = true;
    this.state = 'chase';
    this.raiseShield();
    this.dispatchEvent({ type: 'phase', phase: 2 });
  }

  startJudgment(level, fx) {
    this.bossPhase = 3;
    level.shatterMirrors(fx);
    this.breakShield();
    this.speed = 2.3;
    this.dispatchEvent({ type: 'phase', phase: 3 });
  }

  update(dt, player, farsa, audio, fx, level) {
    if (this.bossPhase === 4) {
      // Crystallization: kneel and crumble into salt
      this.defeatT += dt;
      this.model.rotation.x = Math.min(this.defeatT * 0.4, 0.5);
      this.model.position.y = Math.max(this.model.position.y - dt * 0.3, -0.5);
      this.model.traverse((o) => {
        if (o.isMesh && o.material && 'opacity' in o.material) {
          o.material.transparent = true;
          o.material.opacity = Math.max(1 - this.defeatT / 3, 0);
        }
      });
      if (this.defeatT > 3 && !this._gone) {
        this._gone = true;
        this.group.visible = false;
        this.dispatchEvent({ type: 'boss-end' });
      }
      return;
    }
    if (!this.active || this.dead) return;

    if (this.bossPhase === 1) {
      // The Labyrinth: Gabriel does not fight — he watches from his throne
      const toPlayer = player.pos.clone().sub(this.pos);
      this.yaw = Math.atan2(toPlayer.x, toPlayer.z);
      this.group.rotation.y = this.yaw;
      this.model.position.y = 0.25 + Math.sin(performance.now() / 1000 * 1.2) * 0.1;
      return;
    }

    if (this.bossPhase === 2) {
      // The Doubt: mirrors show the truth — gazing drains Farsa
      const camDir = new THREE.Vector3();
      // mirror-gaze: player near any visible mirror panel
      let nearMirror = false;
      for (const panel of level.mirrorPanels) {
        if (!panel.visible) continue;
        if (panel.position.distanceTo(player.pos) < 4.5) { nearMirror = true; break; }
      }
      if (nearMirror) {
        this.mirrorGazeT += dt;
        if (this.mirrorGazeT > 2) farsa.decay(5 * dt, 'mirror-gaze');
      } else {
        this.mirrorGazeT = 0;
      }
      if (this.hp / this.maxHp <= 0.4) this.startJudgment(level, fx);
    }

    if (this.bossPhase === 3) {
      // Shield cycles; shadow weakness: +50% damage handled via damageTakenMult
      this.shieldRegen -= dt;
      if (this.shieldRegen <= 0 && !this.shielded) {
        this.shieldRegen = 15;
        this.raiseShield();
      }
    }

    super.update(dt, player, farsa, audio, fx);
  }

  damage(amount, isDark = false) {
    if (this.bossPhase === 0 || this.bossPhase === 1 || this.bossPhase === 4) return false;
    // The Judgment: his broken reflection betrays him — dark strikes bite deeper
    if (this.bossPhase === 3 && isDark) amount *= 1.5;
    return super.damage(amount, isDark);
  }

  die() {
    if (this.bossPhase === 4) return;
    // Gabriel does not die — he kneels, crystallizes, and lets you pass
    this.bossPhase = 4;
    this.hp = 0;
    this.defeatT = 0;
    this.breakShield();
    this.dispatchEvent({ type: 'died', pos: this.pos.clone(), angel: this });
  }
}
