// Editor 2D en planta. Pinta en centimetros y con la orientacion del viewport
// cenital de Unreal: X hacia arriba, Y hacia la derecha.
//
// La vista no es decoracion: es donde se comprueban las señales del §5.1 del PDF
// —posicion, presion, silueta, geometria— antes de construir nada.

import { ARQUETIPOS, ORDEN_ARQUETIPOS, FAMILIAS } from './catalogo.js';
import { cajaDelEncuentro, etiquetaDe, plataformaBajo, obstaculosDe, poliDeRect, dentroDeRect, centroDeRect, nuevaRampa, sueltaArma } from './esquema.js';
import { dist, hayVision, desdeYaw, dentroDePoligono, cajaDe } from './geometria.js';
import { ESTADOS } from './sim.js';

const COLOR_MALAKH = '#f2e6c8';

export class Editor {
  constructor(lienzo, obtenerEstado) {
    this.c = lienzo;
    this.ctx = lienzo.getContext('2d');
    this.estado = obtenerEstado;          // () => { enc, cal, seleccion, capas, testigo, fotograma }
    this.cam = { x: 0, y: 0, z: 0.12 };   // z = pixeles por centimetro
    this.alSeleccionar = () => {};
    this.alCambiar = () => {};
    this.modo = 'seleccionar';
    this.arrastre = null;
    this.raton = { x: 0, y: 0, mundo: { x: 0, y: 0 } };
    this._cachePresion = null;

    this._conectar();
    this._ajustarTamano();
    new ResizeObserver(() => { this._ajustarTamano(); this.pintar(); }).observe(lienzo.parentElement);
  }

  // ------------------------------------------------------------ transformada

  aPantalla(p) {
    const { width: w, height: h } = this.c;
    const dpr = this._dpr;
    return {
      x: (w / dpr) / 2 + (p.y - this.cam.y) * this.cam.z,
      y: (h / dpr) / 2 - (p.x - this.cam.x) * this.cam.z
    };
  }

  aMundo(sx, sy) {
    const { width: w, height: h } = this.c;
    const dpr = this._dpr;
    return {
      x: this.cam.x - (sy - (h / dpr) / 2) / this.cam.z,
      y: this.cam.y + (sx - (w / dpr) / 2) / this.cam.z
    };
  }

  encajar() {
    const { enc } = this.estado();
    const caja = cajaDelEncuentro(enc);
    const anchoMundo = Math.max(600, caja.maxY - caja.minY);
    const altoMundo = Math.max(600, caja.maxX - caja.minX);
    const w = this.c.width / this._dpr, h = this.c.height / this._dpr;
    this.cam.z = Math.min(w / (anchoMundo * 1.15), h / (altoMundo * 1.15));
    this.cam.x = (caja.minX + caja.maxX) / 2;
    this.cam.y = (caja.minY + caja.maxY) / 2;
    this.pintar();
  }

  invalidarPresion() { this._cachePresion = null; }

  // -------------------------------------------------------------- interaccion

  _ajustarTamano() {
    const dpr = window.devicePixelRatio || 1;
    this._dpr = dpr;
    const r = this.c.parentElement.getBoundingClientRect();
    this.c.width = Math.max(1, Math.round(r.width * dpr));
    this.c.height = Math.max(1, Math.round(r.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  _conectar() {
    const c = this.c;

    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      const antes = this.aMundo(e.offsetX, e.offsetY);
      const k = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      this.cam.z = Math.max(0.008, Math.min(2, this.cam.z * k));
      const despues = this.aMundo(e.offsetX, e.offsetY);
      this.cam.x += antes.x - despues.x;
      this.cam.y += antes.y - despues.y;
      this.pintar();
    }, { passive: false });

    c.addEventListener('mousedown', (e) => {
      const m = this.aMundo(e.offsetX, e.offsetY);
      const { enc } = this.estado();

      if (this.modo === 'cobertura' || this.modo === 'plataforma') {
        this.arrastre = { tipo: 'caja', desde: m, hasta: m };
        return;
      }
      if (this.modo === 'acceso') {
        // Se pincha AL PIE. La rampa sube hacia el centro de la plataforma, con
        // el largo justo para no pasar de 45 grados. Se puede afinar arrastrando
        // luego cualquiera de sus dos extremos.
        const plat = enc.plataformas.find(p => dentroDeRect(m, p)) || enc.plataformas[0];
        if (plat) {
          const c = centroDeRect(plat);
          const dx = c.x - m.x, dy = c.y - m.y;
          const l = Math.hypot(dx, dy) || 1;
          const largo = Math.max(200, (plat.cota || 0) * 1.5);
          (plat.accesos ||= []).push(nuevaRampa(m, {
            x: m.x + (dx / l) * largo,
            y: m.y + (dy / l) * largo
          }, 300));
          this.alCambiar();
        }
        return;
      }
      if (this.modo === 'entrada') {
        enc.jugador.pos = { x: Math.round(m.x), y: Math.round(m.y) };
        this.alCambiar();
        return;
      }

      const golpe = this._quePillo(m);
      if (golpe) {
        this.alSeleccionar(golpe);
        this.arrastre = { tipo: 'objeto', objeto: golpe, desde: m, original: this._posDe(golpe) };
      } else {
        this.alSeleccionar(null);
        this.arrastre = { tipo: 'camara', desde: { sx: e.offsetX, sy: e.offsetY }, cam: { ...this.cam } };
      }
    });

    window.addEventListener('mousemove', (e) => {
      const r = c.getBoundingClientRect();
      const sx = e.clientX - r.left, sy = e.clientY - r.top;
      this.raton = { x: sx, y: sy, mundo: this.aMundo(sx, sy) };

      if (!this.arrastre) { if (this.modo !== 'seleccionar') this.pintar(); return; }
      const m = this.raton.mundo;

      if (this.arrastre.tipo === 'camara') {
        this.cam.x = this.arrastre.cam.x + (sy - this.arrastre.desde.sy) / this.cam.z;
        this.cam.y = this.arrastre.cam.y - (sx - this.arrastre.desde.sx) / this.cam.z;
        this.pintar();
      } else if (this.arrastre.tipo === 'caja') {
        this.arrastre.hasta = m;
        this.pintar();
      } else if (this.arrastre.tipo === 'objeto') {
        const dx = m.x - this.arrastre.desde.x, dy = m.y - this.arrastre.desde.y;
        this._moverObjeto(this.arrastre.objeto, this.arrastre.original, dx, dy);
        this.invalidarPresion();
        this.alCambiar();
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.arrastre?.tipo === 'caja') {
        const { desde, hasta } = this.arrastre;
        if (Math.abs(desde.x - hasta.x) > 40 && Math.abs(desde.y - hasta.y) > 40) {
          this.alCrearCaja(this.modo, desde, hasta);
        }
      }
      this.arrastre = null;
    });
  }

  _posDe(o) {
    if (o.tipo === 'enemigo') return { ...o.ref.pos };
    if (o.tipo === 'entrada') return { ...this.estado().enc.jugador.pos };
    if (o.tipo === 'rampa') return { desde: { ...o.ref.desde }, hasta: { ...o.ref.hasta } };
    return { min: { ...o.ref.min }, max: { ...o.ref.max } };
  }

  _moverObjeto(o, original, dx, dy) {
    const r = (v) => Math.round(v);
    if (o.tipo === 'enemigo') {
      o.ref.pos = { x: r(original.x + dx), y: r(original.y + dy) };
      const { enc } = this.estado();
      // Invariante del contrato §2.1: la cota de un enemigo es 0 o la de la
      // plataforma que lo contiene. Si no, se cae o se queda flotando.
      const plat = plataformaBajo(enc, o.ref.pos);
      o.ref.cota = plat ? plat.cota : 0;
    } else if (o.tipo === 'rampa') {
      o.ref.desde = { x: r(original.desde.x + dx), y: r(original.desde.y + dy) };
      o.ref.hasta = { x: r(original.hasta.x + dx), y: r(original.hasta.y + dy) };
    } else if (o.tipo === 'entrada') {
      this.estado().enc.jugador.pos = { x: r(original.x + dx), y: r(original.y + dy) };
    } else {
      o.ref.min = { x: r(original.min.x + dx), y: r(original.min.y + dy) };
      o.ref.max = { x: r(original.max.x + dx), y: r(original.max.y + dy) };
    }
  }

  _quePillo(m) {
    const { enc } = this.estado();
    for (const e of enc.enemigos) {
      if (dist(m, e.pos) <= Math.max(60, 70 / this.cam.z * 0.5)) return { tipo: 'enemigo', ref: e, id: e.id };
    }
    if (dist(m, enc.jugador.pos) <= 90) return { tipo: 'entrada', ref: enc.jugador.pos, id: 'entrada' };
    for (const p of enc.plataformas) {
      for (const a of (p.accesos || [])) {
        if (a.desde && dist(m, a.desde) <= 90) return { tipo: 'rampa', ref: a, id: 'rampa', padre: p };
        if (a.hasta && dist(m, a.hasta) <= 90) return { tipo: 'rampa', ref: a, id: 'rampa', padre: p };
      }
    }
    for (const c of enc.coberturas) if (dentroDeRect(m, c)) return { tipo: 'cobertura', ref: c, id: c.id };
    for (const p of enc.plataformas) if (dentroDeRect(m, p)) return { tipo: 'plataforma', ref: p, id: p.id };
    return null;
  }

  // ------------------------------------------------------------------ pintado

  pintar() {
    const { enc, cal, seleccion, capas, fotograma } = this.estado();
    const ctx = this.ctx;
    const w = this.c.width / this._dpr, h = this.c.height / this._dpr;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, w, h);

    this._rejilla(w, h);
    this._arena(enc);
    if (capas.presion) this._presion(enc, cal);
    this._plataformas(enc, seleccion);
    this._coberturas(enc, seleccion);
    this._marcadores(enc, seleccion);

    if (fotograma) this._fotograma(enc, cal, fotograma);
    else this._enemigos(enc, cal, seleccion, capas);

    if (capas.vision && seleccion?.tipo === 'enemigo') this._lineasDeVision(enc, cal, seleccion.ref);
    if (this.arrastre?.tipo === 'caja') this._cajaFantasma();
    this._escala(w, h);
  }

  _rejilla(w, h) {
    const ctx = this.ctx;
    const paso = 100;
    const esq0 = this.aMundo(0, h), esq1 = this.aMundo(w, 0);
    const x0 = Math.floor(esq0.x / paso) * paso, x1 = Math.ceil(esq1.x / paso) * paso;
    const y0 = Math.floor(esq0.y / paso) * paso, y1 = Math.ceil(esq1.y / paso) * paso;
    if ((x1 - x0) / paso > 400) return;

    ctx.lineWidth = 1;
    for (let x = x0; x <= x1; x += paso) {
      const a = this.aPantalla({ x, y: y0 }), b = this.aPantalla({ x, y: y1 });
      ctx.strokeStyle = x % 500 === 0 ? '#1b1b25' : '#111118';
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    for (let y = y0; y <= y1; y += paso) {
      const a = this.aPantalla({ x: x0, y }), b = this.aPantalla({ x: x1, y });
      ctx.strokeStyle = y % 500 === 0 ? '#1b1b25' : '#111118';
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
  }

  _camino(poli) {
    const ctx = this.ctx;
    ctx.beginPath();
    poli.forEach((p, i) => {
      const s = this.aPantalla(p);
      i ? ctx.lineTo(s.x, s.y) : ctx.moveTo(s.x, s.y);
    });
    ctx.closePath();
  }

  _arena(enc) {
    if (!enc.arena.bounds) return;
    const ctx = this.ctx;
    this._camino(poliDeRect(enc.arena.bounds));
    ctx.fillStyle = 'rgba(24,22,18,.7)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(212,175,55,.55)';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  _coberturas(enc, sel) {
    const ctx = this.ctx;
    for (const c of enc.coberturas) {
      this._camino(poliDeRect(c));
      ctx.fillStyle = 'rgba(120,120,140,.28)';
      ctx.fill();
      ctx.strokeStyle = sel?.id === c.id ? '#d4af37' : 'rgba(160,160,185,.6)';
      ctx.lineWidth = sel?.id === c.id ? 2 : 1;
      ctx.stroke();
      this._texto(poliDeRect(c), `${c.etiqueta || 'cobertura'} · ${c.altura}cm`, 'rgba(200,200,220,.75)');
    }
  }

  _plataformas(enc, sel) {
    const ctx = this.ctx;
    for (const p of enc.plataformas) {
      this._camino(poliDeRect(p));
      ctx.fillStyle = 'rgba(90,110,140,.22)';
      ctx.fill();
      ctx.strokeStyle = sel?.id === p.id ? '#d4af37' : 'rgba(140,170,210,.5)';
      ctx.lineWidth = sel?.id === p.id ? 2 : 1;
      ctx.stroke();
      this._texto(poliDeRect(p), `${p.etiqueta || 'plataforma'} · cota ${p.cota}`, 'rgba(170,200,235,.8)');

      // Las rampas se dibujan como lo que son: un tramo con ancho, del pie a la
      // cima. Un punto suelto no decia ni por donde se sube ni si cabe alguien.
      const sinAcceso = !p.accesos || !p.accesos.length;
      for (const a of (p.accesos || [])) {
        if (!a.desde || !a.hasta) continue;
        const d = this.aPantalla(a.desde), h = this.aPantalla(a.hasta);
        const ancho = Math.max(2, (a.ancho || 300) * this.cam.z);
        ctx.save();
        ctx.strokeStyle = 'rgba(124,179,66,.45)';
        ctx.lineWidth = ancho;
        ctx.lineCap = 'butt';
        ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(h.x, h.y); ctx.stroke();
        ctx.restore();
        // El pie, marcado: es por donde se entra.
        ctx.beginPath(); ctx.arc(d.x, d.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#7cb342'; ctx.fill();
        ctx.strokeStyle = '#0b0b10'; ctx.lineWidth = 1.5; ctx.stroke();
      }
      if (sinAcceso) {
        const c = this.aPantalla(centroDeRect(p));
        ctx.fillStyle = '#c4483f';
        ctx.font = '600 11px "Segoe UI", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('SIN ACCESO — inalcanzable a pie', c.x, c.y);
        ctx.textAlign = 'left';
      }
    }
  }

  _texto(poli, txt, color) {
    const caja = cajaDe(poli);
    const s = this.aPantalla({ x: caja.maxX, y: caja.minY });
    this.ctx.fillStyle = color;
    this.ctx.font = '10px "Segoe UI", sans-serif';
    this.ctx.fillText(txt, s.x + 3, s.y + 11);
  }

  _marcadores(enc, sel) {
    const ctx = this.ctx;
    const t = enc.arena.trigger;
    if (t) {
      const s = this.aPantalla(t);
      ctx.beginPath(); ctx.arc(s.x, s.y, t.radio * this.cam.z, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(180,138,216,.75)'; ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(180,138,216,.85)'; ctx.font = '10px "Segoe UI", sans-serif';
      ctx.fillText('trigger del sello', s.x + 8, s.y - 8);
    }
    if (enc.arena.checkpoint) {
      const s = this.aPantalla(enc.arena.checkpoint);
      ctx.fillStyle = '#7cb342';
      ctx.fillRect(s.x - 5, s.y - 5, 10, 10);
      ctx.fillStyle = 'rgba(124,179,66,.9)'; ctx.font = '10px "Segoe UI", sans-serif';
      ctx.fillText('checkpoint', s.x + 8, s.y + 4);
    }
    const e = this.aPantalla(enc.jugador.pos);
    ctx.beginPath(); ctx.arc(e.x, e.y, 9, 0, Math.PI * 2);
    ctx.fillStyle = COLOR_MALAKH; ctx.fill();
    ctx.strokeStyle = sel?.tipo === 'entrada' ? '#d4af37' : '#0b0b10';
    ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = COLOR_MALAKH; ctx.font = '600 10px "Segoe UI", sans-serif';
    ctx.fillText('MALAKH', e.x + 12, e.y + 4);
  }

  _enemigos(enc, cal, sel, capas) {
    const ctx = this.ctx;
    const orden = enc.ordenPrevisto || [];
    for (const e of enc.enemigos) {
      const meta = ARQUETIPOS[e.arquetipo] || {};
      const p = cal.arquetipos[e.arquetipo];
      const s = this.aPantalla(e.pos);
      const r = Math.max(5, (p?.radio || 50) * this.cam.z);
      const elegido = sel?.id === e.id;

      if (capas.rangos && p) {
        ctx.beginPath(); ctx.arc(s.x, s.y, p.alcanceAtaque * this.cam.z, 0, Math.PI * 2);
        ctx.strokeStyle = (meta.color || '#888') + '55'; ctx.lineWidth = 1; ctx.stroke();
        ctx.beginPath(); ctx.arc(s.x, s.y, p.rangoAggro * this.cam.z, 0, Math.PI * 2);
        ctx.setLineDash([3, 6]); ctx.strokeStyle = (meta.color || '#888') + '25'; ctx.stroke();
        ctx.setLineDash([]);
      }
      if (capas.conos && p) {
        const d = desdeYaw(e.yaw ?? 180);
        const apertura = (e.arquetipo === 'arquero_del_firmamento' ? 40 : 90) * Math.PI / 180;
        const base = Math.atan2(d.y, -d.x) - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.arc(s.x, s.y, Math.min(p.rangoAggro, 1600) * this.cam.z, base - apertura / 2, base + apertura / 2);
        ctx.closePath();
        ctx.fillStyle = (meta.color || '#888') + '14';
        ctx.fill();
      }

      ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
      ctx.fillStyle = meta.color || '#888'; ctx.fill();
      ctx.strokeStyle = elegido ? '#fff' : '#0b0b10';
      ctx.lineWidth = elegido ? 2.5 : 1.5; ctx.stroke();

      if (e.drop?.principal || e.drop?.secundaria) {
        ctx.beginPath(); ctx.arc(s.x, s.y, r + 4, 0, Math.PI * 2);
        ctx.strokeStyle = '#d4af37'; ctx.lineWidth = 1.5; ctx.stroke();
      }
      if ((e.cota || 0) > 50) {
        ctx.fillStyle = '#0b0b10'; ctx.font = '700 9px "Segoe UI", sans-serif'; ctx.textAlign = 'center';
        ctx.fillText('▲', s.x, s.y - r - 4);
        ctx.textAlign = 'left';
      }

      ctx.fillStyle = '#0b0b10'; ctx.font = `700 ${Math.max(8, r)}px "Segoe UI", sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(meta.glifo || '?', s.x, s.y);
      ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';

      const i = orden.indexOf(e.id);
      const nombre = (i >= 0 ? `${i + 1}. ` : '') + (e.etiqueta || e.arquetipo.split('_')[0]);
      ctx.fillStyle = elegido ? '#fff' : 'rgba(230,228,221,.72)';
      ctx.font = '10px "Segoe UI", sans-serif';
      ctx.fillText(nombre, s.x + r + 5, s.y + 3);
    }
  }

  /** Un fotograma de la partida testigo, en vez del planteamiento estatico. */
  _fotograma(enc, cal, f) {
    const ctx = this.ctx;

    // Zonas del estandarte, debajo de todo.
    for (const z of (f.zonas || [])) {
      const s = this.aPantalla(z);
      ctx.beginPath(); ctx.arc(s.x, s.y, z.radio * this.cam.z, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(181,138,216,.14)'; ctx.fill();
      ctx.strokeStyle = 'rgba(181,138,216,.5)'; ctx.lineWidth = 1; ctx.stroke();
    }

    // Armas en el suelo: el §4.1 pide que se noten.
    for (const d of (f.drops || [])) {
      const s = this.aPantalla(d);
      const color = FAMILIAS[d.familia]?.color || '#d4af37';
      ctx.save();
      ctx.translate(s.x, s.y);
      ctx.rotate(Math.PI / 4);
      ctx.fillStyle = color;
      ctx.fillRect(-5, -5, 10, 10);
      ctx.restore();
      ctx.beginPath(); ctx.arc(s.x, s.y, 13, 0, Math.PI * 2);
      ctx.strokeStyle = color + '99'; ctx.lineWidth = 1.5; ctx.stroke();
    }

    for (const a of f.agentes) {
      // Los de una oleada que ENTRA todavia no estan en la arena (§6).
      if (a.presente === false) continue;
      const meta = a.id === 'malakh'
        ? { color: COLOR_MALAKH, glifo: 'M' }
        : (ARQUETIPOS[enc.enemigos.find(e => e.id === a.id)?.arquetipo] || {});
      const s = this.aPantalla({ x: a.x, y: a.y });
      const muerto = a.estado === ESTADOS.MUERTO;
      const r = Math.max(5, 48 * this.cam.z);

      // Quien espera su oleada se pinta a media tinta: sin esto la reproduccion
      // enseña cinco peleando cuando pelean dos.
      ctx.globalAlpha = muerto ? 0.22 : (a.dormido ? 0.45 : 1);

      // Destello de impacto, igual que en la 3D: rojo si entro, azul si lo paro
      // la guardia. Un golpe que no aturde no deja estado, y sin esto no se ve.
      if (a.golpeado && !muerto) {
        ctx.beginPath(); ctx.arc(s.x, s.y, r + 6, 0, Math.PI * 2);
        ctx.fillStyle = a.golpeBloqueado ? 'rgba(127,168,232,.45)' : 'rgba(255,92,72,.5)';
        ctx.fill();
      }

      ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
      ctx.fillStyle = meta.color || '#888'; ctx.fill();
      ctx.strokeStyle = '#0b0b10'; ctx.lineWidth = 1.5; ctx.stroke();

      if (!muerto) {
        const d = desdeYaw(a.yaw);
        const p2 = this.aPantalla({ x: a.x + d.x * 130, y: a.y + d.y * 130 });
        ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = '#0b0b10'; ctx.lineWidth = 2; ctx.stroke();

        const hpMax = a.id === 'malakh' ? cal.malakh.hp
          : (cal.arquetipos[enc.enemigos.find(e => e.id === a.id)?.arquetipo]?.hp || 100);
        ctx.fillStyle = 'rgba(0,0,0,.6)';
        ctx.fillRect(s.x - r, s.y - r - 8, r * 2, 3);
        ctx.fillStyle = a.id === 'malakh' ? '#d85c67' : '#7cb342';
        ctx.fillRect(s.x - r, s.y - r - 8, r * 2 * Math.max(0, a.hp / hpMax), 3);

        const marca = { anticipacion: '!', activo: '✳', esquiva: '~', curando: '+', aturdido: '×', bloqueando: '▮', recogiendo: '⌾' }[a.estado];
        if (marca) {
          ctx.fillStyle = '#fff'; ctx.font = '700 11px "Segoe UI", sans-serif'; ctx.textAlign = 'center';
          ctx.fillText(marca, s.x, s.y - r - 12);
          ctx.textAlign = 'left';
        }
      }
      ctx.globalAlpha = 1;
    }
    for (const p of (f.proyectiles || [])) {
      const s = this.aPantalla(p);
      ctx.beginPath(); ctx.arc(s.x, s.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#9fd0e8'; ctx.fill();
    }
  }

  /** Mapa de presion: cuanta cobertura de arqueros hay en cada punto del suelo. */
  _presion(enc, cal) {
    const arqueros = enc.enemigos.filter(e => e.arquetipo === 'arquero_del_firmamento');
    if (!arqueros.length) return;

    if (!this._cachePresion) {
      const caja = cajeaArena(enc);
      const paso = 120;
      const celdas = [];
      for (let x = caja.minX; x <= caja.maxX; x += paso) {
        for (let y = caja.minY; y <= caja.maxY; y += paso) {
          const p = { x, y };
          if (!dentroDeRect(p, enc.arena.bounds)) continue;
          let n = 0;
          for (const a of arqueros) {
            const perfil = cal.arquetipos[a.arquetipo];
            if (dist(p, a.pos) > perfil.alcanceAtaque) continue;
            if (!hayVision(a.pos, a.cota || 0, p, 0, obstaculosDe(enc), cal.malakh.alturaOjos)) continue;
            n++;
          }
          if (n) celdas.push({ x, y, n, paso });
        }
      }
      this._cachePresion = { celdas, max: arqueros.length };
    }

    const ctx = this.ctx;
    for (const c of this._cachePresion.celdas) {
      const s = this.aPantalla({ x: c.x, y: c.y });
      const lado = c.paso * this.cam.z;
      ctx.fillStyle = `rgba(196,72,63,${0.10 + 0.22 * (c.n / this._cachePresion.max)})`;
      ctx.fillRect(s.x - lado / 2, s.y - lado / 2, lado + 0.5, lado + 0.5);
    }
  }

  _lineasDeVision(enc, cal, desde) {
    const ctx = this.ctx;
    const a = this.aPantalla(desde.pos);
    for (const otro of enc.enemigos) {
      if (otro.id === desde.id) continue;
      this._raya(desde, otro.pos, otro.cota, enc, cal, a);
    }
    this._raya(desde, enc.jugador.pos, 0, enc, cal, a);
  }

  _raya(desde, hasta, cotaHasta, enc, cal, a) {
    const ve = hayVision(desde.pos, desde.cota || 0, hasta, cotaHasta || 0, obstaculosDe(enc), cal.malakh.alturaOjos);
    const b = this.aPantalla(hasta);
    const ctx = this.ctx;
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = ve ? 'rgba(124,179,66,.55)' : 'rgba(196,72,63,.35)';
    ctx.lineWidth = 1;
    if (!ve) ctx.setLineDash([3, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  _cajaFantasma() {
    const { desde, hasta } = this.arrastre;
    const a = this.aPantalla(desde), b = this.aPantalla(hasta);
    const ctx = this.ctx;
    ctx.strokeStyle = '#d4af37'; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
    ctx.strokeRect(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y));
    ctx.setLineDash([]);
  }

  _escala(w, h) {
    const ctx = this.ctx;
    const metros = 5;
    const px = metros * 100 * this.cam.z;
    ctx.strokeStyle = 'rgba(230,228,221,.5)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(w - 20 - px, h - 18); ctx.lineTo(w - 20, h - 18); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(w - 20 - px, h - 22); ctx.lineTo(w - 20 - px, h - 14);
    ctx.moveTo(w - 20, h - 22); ctx.lineTo(w - 20, h - 14); ctx.stroke();
    ctx.fillStyle = 'rgba(230,228,221,.6)'; ctx.font = '10px "Segoe UI", sans-serif'; ctx.textAlign = 'center';
    ctx.fillText(`${metros} m`, w - 20 - px / 2, h - 24);
    ctx.textAlign = 'left';
  }
}

function cajeaArena(enc) { const b = enc.arena.bounds; return { minX: b.min.x, maxX: b.max.x, minY: b.min.y, maxY: b.max.y }; }

export { ORDEN_ARQUETIPOS, etiquetaDe };
