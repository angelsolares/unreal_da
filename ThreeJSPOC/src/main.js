import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Engine } from './core/Engine.js';
import { Input } from './core/Input.js';
import { Assets } from './core/Assets.js';
import { GameAudio } from './core/Audio.js';
import { createSky, createPollen } from './world/SkyDome.js';
import { FX } from './world/FX.js';
import { MalkuthLevel } from './world/MalkuthLevel.js';
import { Player } from './gameplay/Player.js';
import { Messenger, Archangel } from './gameplay/Enemies.js';
import { Gabriel } from './gameplay/Gabriel.js';
import { Farsa, CelestialSnare, Altar, WaveEncounter } from './gameplay/Systems.js';
import { HUD } from './ui/HUD.js';

const ASSET_LIST = [
  'SK_Malakh_Placeholder', 'SM_AngelTerrestrial',
  'SK_MAP_Messenger', 'SK_MAP_Archangel', 'SK_MAP_Gabriel_Base',
  'SM_MAP_Sword_Ceremonial',
  'SM_MGK_Trellis_Arch', 'SM_MGK_Path_Straight_300',
  'SM_MGK_Hedge_Straight_400', 'SM_MGK_Fountain_Octagonal', 'SM_MGK_Fountain_Round_Small',
  'SM_MGK_Bench_Straight_A', 'SM_MGK_Bench_Stone_B', 'SM_MGK_GardenLamp',
  'SM_MGK_Topiary_Sphere', 'SM_MGK_Topiary_Spiral', 'SM_MGK_Flowerbed_Round',
  'SM_MRK_Pedestal_Square_150', 'SM_MRK_Column_Intact_400', 'SM_MRK_Column_Intact_600',
  'SM_MRK_Column_Broken_A', 'SM_MRK_Column_Fallen_400', 'SM_MRK_Column_CollapsedCluster',
  'SM_MRK_Obelisk_400', 'SM_MRK_Obelisk_700', 'SM_MRK_Dome_HalfBroken_800',
  'SM_MRK_RuinedArch_300', 'SM_MRK_RubbleCluster_A', 'SM_MRK_InscribedSlab',
  'SM_MSK_Trunk_Twisted_800', 'SM_MSK_CanopyCluster', 'SM_MSK_Altar_Main_300',
  'SM_MSK_RitualCircle_400', 'SM_MSK_RootCluster_A', 'SM_MSK_FlowerCluster',
  'SM_MSK_Barrier_ThornStraight_300', 'SM_MSK_SanctuaryArch',
  'SM_MMLK_Mirror_Straight_200x300', 'SM_MMLK_Mirror_Cracked_A',
  'SM_MMLK_CentralOculus', 'SM_MMLK_Post_Ornate',
  'SM_MP_Throne_Malkuth_Main', 'SM_MP_Throne_Dais_400',
  'SM_MP_Portal_Arch_500', 'SM_MP_Portal_RuneRing', 'SM_MP_PortalSurface_Preview',
  'SM_MP_PortalSteps', 'SM_MP_Bridge_Straight_300x1200', 'SM_MP_BridgeRailing_300',
  'SM_MP_Bridge_Pillar', 'SM_MP_Stair_Wide_600x600',
];

async function boot() {
  const engine = new Engine(document.getElementById('app'));
  const { scene, camera, renderer } = engine;
  const hud = new HUD();
  const audio = new GameAudio();
  const input = new Input(renderer.domElement);

  // Brightness: persisted, adjustable from the pause menu
  const savedBrightness = parseFloat(localStorage.getItem('da_brightness'));
  if (!Number.isNaN(savedBrightness)) {
    engine.setBrightness(savedBrightness);
    hud.el.brightness.value = savedBrightness;
    hud.el.brightnessVal.textContent = savedBrightness.toFixed(2);
  }
  hud.el.brightness.addEventListener('input', (e) => {
    const v = parseFloat(e.target.value);
    engine.setBrightness(v);
    hud.el.brightnessVal.textContent = v.toFixed(2);
    localStorage.setItem('da_brightness', v);
  });

  // Environment reflections for marble/mirrors/water
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.45;

  // Load models with progress on the start button
  const assets = new Assets();
  const startBtn = document.getElementById('start-btn');
  await assets.loadAll(ASSET_LIST, (k) => {
    startBtn.textContent = `Cargando ${(k * 100).toFixed(0)}%`;
  });
  startBtn.textContent = 'Entrar al Reino';

  // World
  const sky = createSky(scene);
  const pollen = createPollen(scene);
  const level = new MalkuthLevel(scene, assets);
  const fx = new FX(scene);

  // Player + systems
  const player = new Player(scene, assets, level, camera);
  player.glideUnlocked = false;
  const farsa = new Farsa();
  const snare = new CelestialSnare(level, fx, audio);
  const altar = new Altar(level.anchors.altar);
  snare.onHitPlayer = () => hud.blindFlash();

  // ---------------- Enemies per LDD beat chart ----------------
  const enemies = [];
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);

  // Beat 2 — First Watchers (hedge path)
  const watchers = [
    new Messenger(scene, assets, level, v3(-1.5, 0, 71), { active: false, patrol: [v3(-1.5, 0, 71), v3(1.5, 0, 78)] }),
    new Messenger(scene, assets, level, v3(1.5, 0, 78), { active: false, patrol: [v3(1.5, 0, 78), v3(-1.5, 0, 71)] }),
  ];
  // Beat 3 — Open Fields (coordinated patrol)
  const fieldAngels = [
    new Messenger(scene, assets, level, v3(-10, 0, 100), { active: false, patrol: [v3(-10, 0, 100), v3(-4, 0, 114), v3(-14, 0, 110)] }),
    new Messenger(scene, assets, level, v3(10, 0, 104), { active: false, patrol: [v3(10, 0, 104), v3(5, 0, 116), v3(13, 0, 96)] }),
    new Messenger(scene, assets, level, v3(0, 0, 118), { active: false, patrol: [v3(0, 0, 118), v3(-6, 0, 110), v3(6, 0, 110)] }),
  ];
  // Beat 4 — The False Peace (elite)
  const archangel = new Archangel(scene, assets, level, v3(0, 0, 140), { active: false, yaw: Math.PI });
  // Beat 9 — Gabriel
  const gabriel = new Gabriel(scene, assets, level, v3(0, 6, 331));
  enemies.push(...watchers, ...fieldAngels, archangel, gabriel);
  const baseEnemies = [...fieldAngels, archangel]; // watchers are handled by their trial reset
  let gabrielAdd = null;

  // Beat 8 — The Host Descends (waves at the amphitheater)
  const waves = new WaveEncounter((count) => {
    const spawned = [];
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2;
      const m = new Messenger(scene, assets, level, v3(Math.cos(a) * 8, 0, 280 + Math.sin(a) * 8), { active: true });
      m.aggro = true;
      m.state = 'chase';
      m.addEventListener('died', (e) => onAngelDied(e));
      enemies.push(m);
      spawned.push(m);
      fx.featherBurst(m.pos, 0xfff4d0, 40, 1.5);
    }
    audio.bell(520, 2, 0.2);
    return spawned;
  });

  // ---------------- wiring ----------------
  const stats = { kills: 0, deaths: 0, t0: performance.now() };
  let shadowStain = null; // {pos, corruptio, mesh}
  let paused = false;
  let ended = false;

  function setPaused(v, { relock = false } = {}) {
    if (!started || player.dead || ended || hud.dialogueOpen) return;
    if (paused === v) return;
    paused = v;
    if (v) {
      hud.showPause();
      document.exitPointerLock();
    } else {
      hud.hidePause();
      if (relock) renderer.domElement.requestPointerLock();
    }
  }

  document.getElementById('resume-btn').onclick = () => setPaused(false, { relock: true });

  // Losing pointer lock mid-game (Esc, Alt-Tab) opens the pause menu
  document.addEventListener('pointerlockchange', () => {
    const locked = document.pointerLockElement === renderer.domElement;
    if (!locked && started && !paused && !player.dead && !ended && !hud.dialogueOpen) {
      setPaused(true);
    }
  });

  function onAngelDied(e) {
    stats.kills++;
    fx.featherBurst(e.pos, 0xfff4d0, 110, 2.6);
    audio.bell(760, 1.6, 0.16);
    if (e.angel === gabriel) {
      hud.updateBoss(0);
      hud.hideBoss();
      hud.showSubtitle('Gabriel: «El Fundamento aguarda… y no es tan misericordioso como yo.»', 6);
      hud.setObjective('La escalera de luz te espera. Asciende.');
      player.glideUnlocked = true;
      player.corruptio = Math.min(100, player.corruptio + 50);
    }
  }
  enemies.forEach((e) => e.addEventListener('died', onAngelDied));
  archangel.addEventListener('shield-break', () => {
    fx.featherBurst(archangel.pos, 0xfff8e0, 70, 2);
    audio.hit();
  });
  gabriel.addEventListener('phase', (e) => {
    if (e.phase === 2) {
      hud.updateBoss(null, 'II — La Duda');
      hud.showSubtitle('Gabriel: «Tu sombra es demasiado larga. Tus pasos, demasiado silenciosos.»', 4.5);
      const add = new Messenger(scene, assets, level, v3(6, 6, 318), { active: true });
      add.aggro = true; add.state = 'chase';
      add.addEventListener('died', onAngelDied);
      enemies.push(add);
      gabrielAdd = add;
    } else if (e.phase === 3) {
      hud.updateBoss(null, 'III — El Juicio');
      hud.showSubtitle('Gabriel: «Las Puertas no se abren para los penitentes. Se abren para los pacientes. Pero tú, Malakh… no eres ninguno.»', 6);
      audio.bell(98, 3.5, 0.35);
    }
  });
  gabriel.addEventListener('gabriel-trap', () => {
    audio.rayCharge();
    for (const off of [[2, 1], [-2, -1]]) {
      fx.spawnRayTelegraph(player.pos.clone().add(v3(off[0], 0, off[1])), 1.2, (p) => {
        audio.rayStrike();
        if (player.pos.distanceTo(p) < 1.6) player.damage(25, null, { unblockable: true });
      });
    }
  });

  player.addEventListener('damaged', () => { hud.damageFlash(); audio.hit(); });
  player.addEventListener('attack-start', (e) => {
    const heavy = e.kind === 'heavy';
    fx.slashArc(player.pos, player.yaw, {
      color: heavy ? 0xffe9bb : 0xd9c8ff,
      radius: heavy ? 2.3 : 1.9,
      dir: player.comboStep % 2 === 0 ? 1 : -1,
    });
    audio.whoosh(heavy);
  });
  player.addEventListener('hit-enemy', (e) => {
    if (e.enemy) fx.featherBurst(e.enemy.pos.clone().add(v3(0, 1.2, 0)), 0xfff4d0, 16, 0.9);
  });
  player.addEventListener('died', () => {
    stats.deaths++;
    farsa.onDeathPenalty();
    shadowStain = {
      pos: player.pos.clone(),
      corruptio: player.corruptio,
      mesh: null,
    };
    player.corruptio = 0;
    const blob = new THREE.Mesh(
      new THREE.CircleGeometry(1.1, 20),
      new THREE.MeshBasicMaterial({ color: 0x1a0520, transparent: true, opacity: 0.85 })
    );
    blob.rotation.x = -Math.PI / 2;
    blob.position.copy(shadowStain.pos).add(v3(0, 0.05, 0));
    scene.add(blob);
    shadowStain.mesh = blob;
    hud.showDeath();
    document.exitPointerLock();
  });
  player.addEventListener('hit-enemy', () => audio.hit());
  player.addEventListener('lunge', () => {
    fx.corruptioBurst(player.center);
    fx.slashArc(player.pos, player.yaw, { color: 0x9e4dd8, radius: 2.3, dur: 0.3 });
    audio.whoosh(true);
  });
  player.addEventListener('parry', () => audio.bell(1200, 1.2, 0.25));

  farsa.addEventListener('threshold', (e) => {
    if (e.state === 'SOSPECHOSO') hud.showSubtitle('Los ángeles inclinan la cabeza a tu paso. Sospechan.', 3.5);
    if (e.state === 'REVELADO') hud.showSubtitle('El Cielo te ha reconocido. No hay vuelta atrás.', 3.5);
  });

  // ---------------- zone triggers ----------------
  const triggerActions = {
    'garden': () => {
      hud.banner('I. EL JARDÍN QUE DESPIERTA', 'Los pájaros no cantan — repiten. Las flores se mueven al unísono.');
      hud.setObjective('Camina el sendero del Reino. Aprende a moverte.');
    },
    'statue-approach': () => {
      hud.showSubtitle('Una voz: «No perteneces aquí… y sin embargo, aquí estás.»', 4);
      audio.bell(440, 3, 0.15);
    },
    'first-watchers': () => {
      hud.banner('II. LOS PRIMEROS VIGILANTES', 'Alas cerradas observan; alas abiertas declaran hostilidad.');
      watchers.forEach((w) => w.setActive(true));
      level.sealHedgePath();
    },
    'open-fields': () => {
      hud.banner('III. CAMPO ABIERTO', 'El suelo sagrado juzga al intruso.');
      fieldAngels.forEach((a) => a.setActive(true));
    },
    'false-peace': () => {
      hud.banner('IV. LA FALSA PAZ', 'El guardián del estanque desenvaina fuego blanco.');
      archangel.setActive(true);
      audio.bell(220, 3, 0.25);
    },
    'celestial-snare': () => {
      hud.banner('V. LA TRAMPA CELESTIAL', 'El Reino no te odia. Simplemente no te reconoce.');
      hud.setObjective('Cruza el puente: el suelo brilla oro → blanco antes de cada rayo. Esquiva (C) o corre (Shift).');
      snare.start();
    },
    'snare-end': () => {
      snare.stop();
      hud.setObjective('Sigue el sendero hacia la luz violeta del Santuario.');
    },
    'sanctuary': () => {
      hud.banner('VII. SANTUARIO DE MALKUTH', 'Zona segura. El coro canta sin prisa.');
      snare.stop();
    },
    'host-descends': () => {
      hud.banner('VIII. LA HUESTE DESCIENDE', 'El cielo se oscurece. No hay asientos para ti.');
      waves.start();
    },
    'gabriel': () => {
      hud.banner('IX. GABRIEL DE LAS PUERTAS', 'El laberinto de espejos no perdona la arrogancia.');
      hud.showBoss('GABRIEL DE LAS PUERTAS', 'I — El Laberinto');
      gabriel.beginEncounter(hud, farsa, audio);
    },
    'ascension': () => {
      if (gabriel.bossPhase === 4) {
        endGame();
      } else {
        hud.showSubtitle('Las Puertas no se abren para los impacientes. Gabriel aguarda.', 3.5);
      }
    },
  };

  // ---------------- objective gating ----------------
  // The Kingdom judges in order: no golden gate opens until its trial is complete.
  const triggerFired = (id) => level.triggers.find((t) => t.id === id)?.fired;
  const gateTrials = [
    {
      id: 'watchers',
      active: () => triggerFired('first-watchers'),
      done: () => watchers.every((e) => e.dead),
      objective: () => `Derrota a los 2 Vigilantes (${watchers.filter((e) => e.dead).length}/2). Esquiva con C, bloquea con click der, ataca con click izq.`,
      next: 'El seto se abre. El Reino te permite seguir.',
      nextObjective: 'Cruza el seto hacia el claro.',
    },
    {
      id: 'fields',
      active: () => triggerFired('open-fields'),
      done: () => fieldAngels.every((e) => e.dead),
      objective: () => `Elimina la patrulla del claro (${fieldAngels.filter((e) => e.dead).length}/3). Evita el mosaico central: quema tu Farsa.`,
      next: 'El claro queda en silencio. El gazebo te aguarda.',
      nextObjective: 'Acércate al gazebo del estanque espejo.',
    },
    {
      id: 'archangel',
      active: () => triggerFired('false-peace'),
      done: () => archangel.dead,
      objective: () => 'Derrota al Arcángel. Su Escudo de Luz (70% vida) solo cae con Umbral Lunge (Q · 30 Corruptio); al 40% invoca el Rayo del Juicio — muévete.',
      next: 'El guardián se disuelve en plumas. El puente está abierto.',
      nextObjective: 'Cruza el puente: el suelo brilla oro → blanco antes de cada rayo.',
    },
    {
      id: 'altar',
      active: () => triggerFired('sanctuary'),
      done: () => altar.restCount > 0,
      objective: () => 'Arrodíllate ante el Altar (E) para curarte y fijar tu checkpoint. Opcional: ofrece una Lágrima (F) por +20% daño.',
      next: 'El Santuario te reconoce. El coro resuelve en mayor.',
      nextObjective: 'Entra al anfiteatro.',
    },
    {
      id: 'host',
      active: () => triggerFired('host-descends'),
      done: () => waves.done,
      objective: () => `Sobrevive a la Hueste — oleada ${Math.min(Math.max(waves.current + 1, 1), 3)}/3. No dejes que te rodeen.`,
      next: 'La Hueste se disuelve. El Trono queda al descubierto.',
      nextObjective: 'Asciende la gran escalera hacia el Trono.',
    },
    {
      id: 'gabriel',
      active: () => triggerFired('gabriel'),
      done: () => gabriel.bossPhase === 4,
      objective: () => 'Supera el juicio de Gabriel: responde con humildad (la arrogancia invoca rayos), rompe su escudo con Q, y en el Juicio tus golpes oscuros hieren +50%.',
      next: 'Gabriel se arrodilla. La escalera de luz es tuya.',
      nextObjective: 'Sube la escalera de luz y entra al portal de Yesod.',
    },
  ];

  function checkGates() {
    let currentSet = false;
    for (const trial of gateTrials) {
      if (!trial.active()) continue;
      if (trial.done()) {
        if (level.gates[trial.id]) {
          const pos = level.openGate(trial.id);
          if (pos) fx.featherBurst(pos, 0xffe9bb, 80, 4);
          audio.bell(880, 2.5, 0.2);
          hud.showSubtitle(trial.next, 3.5);
          hud.setObjective(trial.nextObjective);
        }
      } else if (!currentSet) {
        hud.setObjective(trial.objective());
        currentSet = true;
      }
    }
  }

  function endGame() {
    ended = true;
    const mins = ((performance.now() - stats.t0) / 60000).toFixed(1);
    document.exitPointerLock();
    hud.showEnd(
      `Malakh asciende a Yesod. Sus alas ya muestran puntas negras.<br/><br/>
       Tiempo: <b>${mins} min</b> · Ángeles disueltos: <b>${stats.kills}</b> · Muertes: <b>${stats.deaths}</b><br/>
       Farsa final: <b>${farsa.state} (${farsa.value.toFixed(0)}%)</b><br/><br/>
       <i>«El Reino queda atrás. La mentira, contigo.»</i>`
    );
  }

  document.getElementById('respawn-btn').onclick = () => {
    hud.hideDeath();
    hud.closeDialogue();
    player.respawn(altar.checkpoint.clone().add(v3(0, 0, -2)));

    // Souls rule: the Host returns home and returns to life
    for (const e of baseEnemies) {
      if (!e.dead) continue;
      e.dead = false;
      e.hp = e.maxHp;
      e.state = 'patrol';
      e.aggro = false;
      e.pos.copy(e.homePos);
      e.group.visible = e.active;
    }

    // The thorn seal always drops so the garden spawn stays reachable
    level.unsealHedgePath();
    if (level.gates['watchers']) {
      // Watchers trial incomplete: reset the whole beat so it can't soft-lock
      const tr = level.triggers.find((t) => t.id === 'first-watchers');
      if (tr) tr.fired = false;
      for (const w of watchers) {
        w.dead = false;
        w.hp = w.maxHp;
        w.state = 'patrol';
        w.aggro = false;
        w.pos.copy(w.homePos);
        w.setActive(false);
      }
    } else {
      for (const w of watchers) {
        if (!w.dead) continue;
        w.dead = false;
        w.hp = w.maxHp;
        w.state = 'patrol';
        w.aggro = false;
        w.pos.copy(w.homePos);
        w.group.visible = w.active;
      }
    }

    // Gabriel resets fully — the trial of patience starts over
    if (gabriel.bossPhase > 0 && gabriel.bossPhase < 4) {
      gabriel.bossPhase = 0;
      gabriel.hp = gabriel.maxHp;
      gabriel.questionIdx = 0;
      gabriel.state = 'patrol';
      gabriel.aggro = false;
      gabriel.setActive(false);
      gabriel.pos.copy(gabriel.homePos);
      if (gabriel.shielded) gabriel.breakShield();
      hud.hideBoss();
      const tr = level.triggers.find((t) => t.id === 'gabriel');
      if (tr) tr.fired = false;
      if (gabrielAdd && !gabrielAdd.dead) {
        gabrielAdd.dead = true;
        gabrielAdd.group.visible = false;
      }
      gabrielAdd = null;
    }
  };
  document.getElementById('restart-btn').onclick = () => location.reload();

  // Title screen start
  let started = false;
  startBtn.onclick = () => {
    if (started) return;
    started = true;
    document.getElementById('title-screen').classList.add('hidden');
    hud.show();
    hud.showMenuHint();
    audio.start();
    renderer.domElement.requestPointerLock();
    hud.banner('MALKUTH — EL REINO', 'Esfera 10 · El paraíso terrenal');
  };

  // ---------------- interaction helpers ----------------
  let mosaicCooldown = 0;
  function updateInteractions(dt) {
    // Altar
    const nearAltar = player.pos.distanceTo(altar.pos) < 2.6;
    if (nearAltar && !player.dead) {
      hud.prompt('<b>E</b> Arrodillarse (curar + checkpoint) · <b>F</b> Ofrecer Lágrima (+20% daño)');
      if (input.justPressed('KeyE')) {
        altar.rest(player, farsa);
        audio.bell(660, 2.5, 0.2);
        hud.showSubtitle('El Altar te restaura. El coro resuelve en mayor.', 2.5);
      }
      if (input.justPressed('KeyF')) {
        if (altar.offerTear(player)) {
          audio.bell(330, 2.5, 0.22);
          hud.showSubtitle('Lágrima ofrecida: +20% daño por 3 minutos.', 2.5);
        } else {
          hud.showSubtitle('No te quedan Lágrimas.', 2);
        }
      }
    } else {
      hud.prompt(null);
    }

    // Sacred mosaic burns the disguise
    mosaicCooldown -= dt;
    if (mosaicCooldown <= 0 && player.pos.distanceTo(level.anchors.mosaic) < 3.1 && player.pos.y < 1) {
      mosaicCooldown = 4;
      farsa.onSacredStep();
      audio.bell(196, 2.5, 0.25);
      hud.showSubtitle('El suelo lo recuerda. (−10% Farsa)', 2.2);
    }

    // Falling into the reflecting pool
    if (player.pos.y < -2.9) {
      player.damage(15, null, { unblockable: true });
      hud.blindFlash();
      player.pos.copy(level.anchors.bridgeStart);
      player.vel.set(0, 0, 0);
    }

    // Shadow Stain recovery
    if (shadowStain && player.pos.distanceTo(shadowStain.pos) < 1.6) {
      player.corruptio = Math.min(100, shadowStain.corruptio);
      scene.remove(shadowStain.mesh);
      shadowStain = null;
      hud.showSubtitle('Mancha de Sombra recuperada. Tus Esencias vuelven.', 2.5);
      audio.bell(520, 2, 0.18);
    }

    // Tears heal
    if (input.justPressed('KeyR') && player.tears > 0 && player.hp < player.maxHp && !player.dead) {
      player.tears--;
      player.heal(50);
      audio.bell(587, 2, 0.2);
    }
  }

  // ---------------- combat input ----------------
  // Light attack on quick click, heavy on held release (> 0.35 s) — souls-style.
  function updateCombatInput() {
    if (player.dead) return;
    if (input.mouseDown(0)) {
      player._lmbHold = (player._lmbHold ?? 0) + lastDt;
    } else if ((player._lmbHold ?? 0) > 0) {
      const hold = player._lmbHold;
      player._lmbHold = 0;
      if (player.state !== 'attack') {
        player.tryAttack(hold > 0.35 ? 'heavy' : 'light', enemies, farsa);
      }
    }
    if (input.justPressed('KeyQ')) player.tryLunge(farsa);
    if (input.justPressed('KeyC')) player.tryDodge();
  }

  // ---------------- main loop ----------------
  const clock = new THREE.Clock();
  let lastDt = 0.016;
  let fpsAcc = 0, fpsN = 0, fpsT = 0;

  function loop() {
    requestAnimationFrame(loop);
    const dt = Math.min(clock.getDelta(), 0.05);
    lastDt = dt;
    const t = clock.elapsedTime;

    if (started) {
      if (input.justPressed('KeyH')) setPaused(!paused, { relock: true });

      if (!paused) {
        updateCombatInput();
        player.update(dt, input, enemies, farsa);
        updateInteractions(dt);

        for (const e of enemies) {
          if (e === gabriel) e.update(dt, player, farsa, audio, fx, level);
          else if (e instanceof Archangel) e.update(dt, player, farsa, audio, fx);
          else e.update(dt, player, farsa, audio);
        }
        snare.update(dt, player);
        waves.update(dt, enemies.filter((e) => !e.dead && e !== gabriel && e !== archangel && e.active && e.aggro).length);

        // Zone triggers
        for (const tr of level.triggers) {
          if (!tr.fired && player.pos.z > tr.z) {
            tr.fired = true;
            triggerActions[tr.id]?.();
          }
        }

        // Golden gates open only when their trial is complete
        checkGates();

        // Audio intensity follows danger
        const inCombat = enemies.some((e) => e.active && !e.dead && (e.state === 'chase' || e.state === 'attack'));
        audio.setIntensity(inCombat ? 1 : gabriel.bossPhase > 0 && gabriel.bossPhase < 4 ? 0.7 : 0);

        // Boss bar
        if (gabriel.active && gabriel.bossPhase > 0 && gabriel.bossPhase < 4) {
          hud.updateBoss(gabriel.hp / gabriel.maxHp);
        }

        hud.updateBars(player, farsa);
      }
      input.consume();
    }

    if (!paused) {
      sky.update(t, player.pos);
      pollen.update(t);
      level.update(t, dt);
      fx.update(dt);
    }
    engine.render();

    // FPS meter
    fpsAcc += dt; fpsN++; fpsT += dt;
    if (fpsT > 0.5) { hud.setFps(fpsN / fpsAcc); fpsAcc = 0; fpsN = 0; fpsT = 0; }
  }
  loop();
}

boot().catch((err) => {
  console.error(err);
  const btn = document.getElementById('start-btn');
  if (btn) btn.textContent = 'Error al cargar — revisa consola';
});
