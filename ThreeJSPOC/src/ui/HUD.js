// DOM HUD: bars, Farsa meter, boss bar, zone banners, dialogue wheel, prompts.
export class HUD {
  constructor() {
    this.el = {
      hud: document.getElementById('hud'),
      hp: document.querySelector('#hp-bar .bar-fill'),
      stamina: document.querySelector('#stamina-bar .bar-fill'),
      corruptio: document.querySelector('#corruptio-bar .bar-fill'),
      tears: document.getElementById('tears'),
      farsaState: document.getElementById('farsa-state'),
      farsaFill: document.getElementById('farsa-fill'),
      objective: document.getElementById('objective'),
      bossWrap: document.getElementById('boss-wrap'),
      bossFill: document.getElementById('boss-fill'),
      bossPhase: document.getElementById('boss-phase'),
      zoneBanner: document.getElementById('zone-banner'),
      zoneTitle: document.getElementById('zone-title'),
      zoneSub: document.getElementById('zone-sub'),
      prompt: document.getElementById('prompt'),
      dialogue: document.getElementById('dialogue'),
      dialogueSpeaker: document.getElementById('dialogue-speaker'),
      dialogueText: document.getElementById('dialogue-text'),
      dialogueOpts: document.getElementById('dialogue-opts'),
      dialogueTimer: document.getElementById('dialogue-timer-fill'),
      vignette: document.getElementById('damage-vignette'),
      blind: document.getElementById('blind-flash'),
      title: document.getElementById('title-screen'),
      death: document.getElementById('death-screen'),
      end: document.getElementById('end-screen'),
      endStats: document.getElementById('end-stats'),
      fps: document.getElementById('fps'),
      pause: document.getElementById('pause-screen'),
      pauseObjective: document.getElementById('pause-objective'),
      menuHint: document.getElementById('menu-hint'),
      brightness: document.getElementById('brightness'),
      brightnessVal: document.getElementById('brightness-val'),
    };
    this._bannerTimer = null;
    this._subtitleTimer = null;
    this._dialogueTimer = null;
    this.dialogueOpen = false;
  }

  show() { this.el.hud.classList.remove('hidden'); }

  updateBars(player, farsa) {
    this.el.hp.style.width = (player.hp / player.maxHp * 100) + '%';
    this.el.stamina.style.width = (player.stamina / player.maxStamina * 100) + '%';
    this.el.corruptio.style.width = player.corruptio + '%';
    this.el.farsaFill.style.width = (farsa.value / farsa.maxValue * 100) + '%';
    this.el.farsaFill.style.background = farsa.color;
    this.el.farsaState.textContent = farsa.state;
    this.el.farsaState.style.color = farsa.color;
    const tearEls = this.el.tears.children;
    for (let i = 0; i < tearEls.length; i++) {
      tearEls[i].classList.toggle('empty', i >= player.tears);
    }
  }

  showBoss(name, phaseText) {
    this.el.bossWrap.classList.remove('hidden');
    document.getElementById('boss-name').textContent = name;
    this.el.bossPhase.textContent = phaseText;
  }

  updateBoss(frac, phaseText) {
    if (frac != null) this.el.bossFill.style.width = Math.max(frac * 100, 0) + '%';
    if (phaseText) this.el.bossPhase.textContent = phaseText;
  }

  hideBoss() { this.el.bossWrap.classList.add('hidden'); }

  banner(title, sub = '') {
    this.el.zoneTitle.textContent = title;
    this.el.zoneSub.textContent = sub;
    this.el.zoneBanner.style.opacity = 1;
    clearTimeout(this._bannerTimer);
    this._bannerTimer = setTimeout(() => { this.el.zoneBanner.style.opacity = 0; }, 3600);
  }

  setObjective(text) { this.el.objective.textContent = text; }

  showSubtitle(text, seconds = 3) {
    this.el.zoneSub.textContent = text;
    this.el.zoneTitle.textContent = '';
    this.el.zoneBanner.style.opacity = 1;
    clearTimeout(this._subtitleTimer);
    this._subtitleTimer = setTimeout(() => { this.el.zoneBanner.style.opacity = 0; }, seconds * 1000);
  }

  prompt(html) {
    if (!html) this.el.prompt.classList.add('hidden');
    else {
      this.el.prompt.innerHTML = html;
      this.el.prompt.classList.remove('hidden');
    }
  }

  // Gabriel's dialogue wheel: 3 options + 8 s timer, silence on timeout
  showDialogue(speaker, text, options, onPick) {
    this.dialogueOpen = true;
    document.exitPointerLock(); // free the cursor for the answer buttons
    this.el.dialogue.classList.remove('hidden');
    this.el.dialogueSpeaker.textContent = speaker;
    this.el.dialogueText.textContent = `«${text}»`;
    this.el.dialogueOpts.innerHTML = '';
    let answered = false;
    const pick = (opt) => {
      if (answered) return;
      answered = true;
      clearInterval(this._dialogueTimer);
      this.dialogueOpen = false;
      this.el.dialogue.classList.add('hidden');
      window.removeEventListener('keydown', keyHandler);
      onPick(opt);
    };
    options.forEach((opt, i) => {
      const btn = document.createElement('button');
      btn.className = 'dlg-opt';
      btn.innerHTML = `<span class="key">[${i + 1}]</span>${opt.label}`;
      btn.onclick = () => pick(opt);
      this.el.dialogueOpts.appendChild(btn);
    });
    const keyHandler = (e) => {
      const idx = ['Digit1', 'Digit2', 'Digit3'].indexOf(e.code);
      if (idx >= 0 && options[idx]) pick(options[idx]);
    };
    window.addEventListener('keydown', keyHandler);
    this._dialogueKeyHandler = keyHandler;

    // 8-second timer -> silence (last option is always Silence)
    const t0 = performance.now();
    this._dialogueTimer = setInterval(() => {
      const k = 1 - (performance.now() - t0) / 8000;
      this.el.dialogueTimer.style.width = Math.max(k * 100, 0) + '%';
      if (k <= 0) pick(options[options.length - 1]);
    }, 50);
  }

  // Force-close the dialogue without answering (e.g. player died mid-trial)
  closeDialogue() {
    if (!this.dialogueOpen) return;
    clearInterval(this._dialogueTimer);
    this.dialogueOpen = false;
    this.el.dialogue.classList.add('hidden');
    if (this._dialogueKeyHandler) window.removeEventListener('keydown', this._dialogueKeyHandler);
  }

  damageFlash() {
    this.el.vignette.style.boxShadow = 'inset 0 0 120px rgba(179,38,53,0.55)';
    setTimeout(() => { this.el.vignette.style.boxShadow = 'inset 0 0 120px rgba(179,38,53,0)'; }, 220);
  }

  blindFlash() {
    this.el.blind.style.transition = 'none';
    this.el.blind.style.opacity = 0.9;
    requestAnimationFrame(() => {
      this.el.blind.style.transition = 'opacity 0.9s';
      this.el.blind.style.opacity = 0;
    });
  }

  showDeath() { this.el.death.classList.remove('hidden'); }
  hideDeath() { this.el.death.classList.add('hidden'); }

  showPause() {
    this.el.pauseObjective.textContent = 'Objetivo actual: ' + this.el.objective.textContent;
    this.el.pause.classList.remove('hidden');
  }
  hidePause() { this.el.pause.classList.add('hidden'); }
  get pauseOpen() { return !this.el.pause.classList.contains('hidden'); }

  showMenuHint() { this.el.menuHint.classList.remove('hidden'); }

  showEnd(stats) {
    this.el.endStats.innerHTML = stats;
    this.el.end.classList.remove('hidden');
  }

  setFps(v) { this.el.fps.textContent = v.toFixed(0) + ' fps'; }
}
