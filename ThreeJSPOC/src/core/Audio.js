// Procedural WebAudio: sacred-drone ambient + event SFX. No audio files needed.
// The "wrong paradise" vibe comes from a dry, slightly detuned choir-like pad.
export class GameAudio {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.padGain = null;
    this.started = false;
    this.intensity = 0; // 0 ambient, 1 combat
  }

  start() {
    if (this.started) return;
    this.started = true;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = 0.35;
    this.master.connect(ctx.destination);

    // Sacred pad: stacked fifths, slow beating via slight detune.
    this.padGain = ctx.createGain();
    this.padGain.gain.value = 0.05;
    const padFilter = ctx.createBiquadFilter();
    padFilter.type = 'lowpass';
    padFilter.frequency.value = 900;
    this.padGain.connect(padFilter).connect(this.master);
    this.padFilter = padFilter;

    const notes = [110, 164.8, 220, 277.2, 329.6]; // A2 E3 A3 C#4 E4 — open sacred chord
    this.padOsc = notes.map((f, i) => {
      const o = ctx.createOscillator();
      o.type = i % 2 ? 'sine' : 'triangle';
      o.frequency.value = f;
      o.detune.value = (i - 2) * 4; // subtle wrongness
      const g = ctx.createGain();
      g.gain.value = 0.16;
      o.connect(g).connect(this.padGain);
      o.start();
      return o;
    });

    // Slow LFO breathing on the pad
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.07;
    const lfoGain = ctx.createGain();
    lfoGain.gain.value = 0.02;
    lfo.connect(lfoGain).connect(this.padGain.gain);
    lfo.start();
  }

  setIntensity(v) {
    this.intensity = v;
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    this.padFilter.frequency.linearRampToValueAtTime(900 + v * 2200, t + 1.5);
    this.padGain.gain.linearRampToValueAtTime(0.05 + v * 0.05, t + 1.5);
  }

  bell(freq = 660, dur = 2.2, vol = 0.2) {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const o = ctx.createOscillator();
    o.type = 'sine';
    o.frequency.value = freq;
    const o2 = ctx.createOscillator();
    o2.type = 'sine';
    o2.frequency.value = freq * 2.76; // bell partial
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    const g2 = ctx.createGain();
    g2.gain.setValueAtTime(vol * 0.3, t);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + dur * 0.6);
    o.connect(g).connect(this.master);
    o2.connect(g2).connect(this.master);
    o.start(t); o.stop(t + dur);
    o2.start(t); o2.stop(t + dur);
  }

  hit() {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const bufferSize = ctx.sampleRate * 0.12;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const f = ctx.createBiquadFilter();
    f.type = 'bandpass';
    f.frequency.value = 1800;
    const g = ctx.createGain();
    g.gain.value = 0.25;
    src.connect(f).connect(g).connect(this.master);
    src.start(t);
  }

  trumpetStun() {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    [440, 554, 659].forEach((f) => {
      const o = ctx.createOscillator();
      o.type = 'sawtooth';
      o.frequency.value = f;
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.12, t + 0.05);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.9);
      const flt = ctx.createBiquadFilter();
      flt.type = 'lowpass';
      flt.frequency.value = 2400;
      o.connect(flt).connect(g).connect(this.master);
      o.start(t); o.stop(t + 1);
    });
  }

  // Sword swing: bandpassed noise sweeping down — heavier swings sweep lower
  whoosh(heavy = false) {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const dur = heavy ? 0.35 : 0.2;
    const size = Math.floor(ctx.sampleRate * dur);
    const buffer = ctx.createBuffer(1, size, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < size; i++) data[i] = (Math.random() * 2 - 1) * Math.sin((i / size) * Math.PI);
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const f = ctx.createBiquadFilter();
    f.type = 'bandpass';
    f.Q.value = 1.2;
    f.frequency.setValueAtTime(heavy ? 900 : 1400, t);
    f.frequency.exponentialRampToValueAtTime(heavy ? 220 : 500, t + dur);
    const g = ctx.createGain();
    g.gain.value = heavy ? 0.4 : 0.28;
    src.connect(f).connect(g).connect(this.master);
    src.start(t);
  }

  rayCharge() { this.bell(880, 1.5, 0.08); }
  rayStrike() {
    if (!this.ctx) return;
    this.bell(110, 1.8, 0.3);
    this.hit();
  }
}
