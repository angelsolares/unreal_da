// Vista 3D con primitivos. Misma simulacion, otro renderer.
//
// No esta para que quede bonito. Esta para las dos cosas que la planta NO puede
// contestar:
//
//   1. La linea de vision de verdad — el balcon, la cobertura parcial, el muro
//      que tapa a media altura. En 2D todo eso es una aproximacion.
//   2. La camara a la altura de los ojos de Malakh en la puerta. El §5.1 dice
//      "Lanza larga y brillante visible desde entrada". Aqui se mira si es cierto.
//
// Unidades: la herramienta trabaja en cm y Three en metros, asi que todo pasa
// por aTres(). Ejes: Unreal X (norte) -> -Z, Unreal Y (este) -> X, cota -> Y.

import * as THREE from '../vendor/three/three.module.min.js';
import { ARQUETIPOS, FAMILIAS } from './catalogo.js';
import { cajaDe, centroide } from './geometria.js';
import { lecturaDesdeLaEntrada } from './lectura.js';

const M = 0.01;                       // cm -> m
const COLOR_MALAKH = 0xf2e6c8;

/**
 * cm de la herramienta -> metros de Three, con los ejes de Unreal:
 * X (norte) -> -Z, Y (este) -> X, cota -> Y.
 * Se exporta para poder comprobarlo sin navegador; un eje cambiado de signo
 * pasa desapercibido mirando una maqueta y arruina todo lo que se juzgue en ella.
 */
export const aTres = (p, cota = 0) => new THREE.Vector3(p.y * M, (cota || 0) * M, -p.x * M);

export class Vista3D {
  constructor(contenedor, obtenerEstado) {
    this.cont = contenedor;
    this.estado = obtenerEstado;
    this.activa = false;
    this.camaraActual = 'orbita';
    this.grupos = new Map();          // id de agente -> THREE.Group
    this.dropsVivos = [];

    this._montarEscena();
    this._montarCamaras();
    this._montarOrbita();

    this._ro = new ResizeObserver(() => this._ajustar());
    this._ro.observe(contenedor);
  }

  // ------------------------------------------------------------------ escena

  _montarEscena() {
    this.escena = new THREE.Scene();
    this.escena.background = new THREE.Color(0x08080c);
    this.escena.fog = new THREE.Fog(0x08080c, 40, 140);

    this.render3d = new THREE.WebGLRenderer({ antialias: true });
    this.render3d.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    this.render3d.shadowMap.enabled = true;
    this.render3d.shadowMap.type = THREE.PCFSoftShadowMap;
    this.cont.appendChild(this.render3d.domElement);

    this.escena.add(new THREE.HemisphereLight(0x8899bb, 0x151018, 1.1));
    const sol = new THREE.DirectionalLight(0xfff2d0, 2.2);
    sol.position.set(18, 30, 12);
    sol.castShadow = true;
    sol.shadow.mapSize.set(2048, 2048);
    const s = 40;
    sol.shadow.camera.left = -s; sol.shadow.camera.right = s;
    sol.shadow.camera.top = s; sol.shadow.camera.bottom = -s;
    sol.shadow.camera.far = 120;
    this.escena.add(sol);

    this.mundo = new THREE.Group();      // arena, coberturas, plataformas
    this.actores = new THREE.Group();    // agentes, drops, ayudas
    this.escena.add(this.mundo, this.actores);
  }

  _montarCamaras() {
    this.cam = new THREE.PerspectiveCamera(55, 1, 0.1, 400);
    this.orbita = { radio: 45, theta: Math.PI * 0.75, phi: 0.95, centro: new THREE.Vector3() };
  }

  _montarOrbita() {
    const el = this.render3d.domElement;
    let arrastrando = false, ax = 0, ay = 0;

    el.addEventListener('mousedown', (e) => {
      if (this.camaraActual !== 'orbita') return;
      arrastrando = true; ax = e.clientX; ay = e.clientY;
    });
    window.addEventListener('mouseup', () => { arrastrando = false; });
    window.addEventListener('mousemove', (e) => {
      if (!arrastrando) return;
      this.orbita.theta -= (e.clientX - ax) * 0.006;
      this.orbita.phi = Math.max(0.08, Math.min(1.5, this.orbita.phi - (e.clientY - ay) * 0.005));
      ax = e.clientX; ay = e.clientY;
    });
    el.addEventListener('wheel', (e) => {
      if (this.camaraActual !== 'orbita') return;
      e.preventDefault();
      this.orbita.radio = Math.max(6, Math.min(160, this.orbita.radio * (e.deltaY > 0 ? 1.12 : 1 / 1.12)));
    }, { passive: false });
  }

  // ------------------------------------------------------- construir el mundo

  reconstruir() {
    const { enc, cal } = this.estado();
    this._vaciar(this.mundo);
    this._vaciar(this.actores);
    this.grupos.clear();

    const caja = cajaDe(enc.arena.bounds);
    const centro = centroide(enc.arena.bounds);
    this.orbita.centro = aTres(centro, 0);
    this.orbita.radio = Math.max(24, Math.hypot(caja.maxX - caja.minX, caja.maxY - caja.minY) * M * 0.95);

    this._suelo(enc);
    this._sello(enc);
    for (const c of enc.coberturas || []) this._cobertura(c);
    for (const p of enc.plataformas || []) this._plataforma(p);
    this._marcadores(enc);

    // Un grupo por agente, reutilizado en cada fotograma.
    this.grupos.set('malakh', this._agenteMalakh(cal));
    for (const e of enc.enemigos) this.grupos.set(e.id, this._agenteEnemigo(e, cal));
    for (const g of this.grupos.values()) this.actores.add(g);

    this._plantarEnPosicionInicial(enc, cal);
    this.pintar();
  }

  _vaciar(grupo) {
    while (grupo.children.length) {
      const h = grupo.children.pop();
      h.traverse(o => { o.geometry?.dispose?.(); o.material?.dispose?.(); });
    }
  }

  _formaDe(poli) {
    const s = new THREE.Shape();
    poli.forEach((p, i) => {
      const v = aTres(p, 0);
      i ? s.lineTo(v.x, -v.z) : s.moveTo(v.x, -v.z);
    });
    s.closePath();
    return s;
  }

  _suelo(enc) {
    const g = new THREE.ShapeGeometry(this._formaDe(enc.arena.bounds));
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: 0x22201c, roughness: 0.95, metalness: 0
    }));
    m.rotation.x = -Math.PI / 2;
    m.receiveShadow = true;
    this.mundo.add(m);

    const rejilla = new THREE.GridHelper(200, 200, 0x2a2a38, 0x16161f);
    rejilla.position.y = 0.01;
    this.mundo.add(rejilla);
  }

  /** El sello del §7: barrera invisible, pero con lectura diegetica. */
  _sello(enc) {
    const puntos = enc.arena.bounds.map(p => aTres(p, 0));
    puntos.push(puntos[0].clone());
    const alto = 5;

    const geo = new THREE.BufferGeometry();
    const verts = [];
    for (let i = 0; i < puntos.length - 1; i++) {
      const a = puntos[i], b = puntos[i + 1];
      verts.push(
        a.x, 0, a.z, b.x, 0, b.z, b.x, alto, b.z,
        a.x, 0, a.z, b.x, alto, b.z, a.x, alto, a.z
      );
    }
    geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    geo.computeVertexNormals();
    this.mundo.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      color: 0xd4af37, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false
    })));
    this.mundo.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(puntos),
      new THREE.LineBasicMaterial({ color: 0xd4af37, transparent: true, opacity: 0.6 })
    ));
  }

  _cobertura(c) {
    const caja = cajaDe(c.poli);
    const ancho = (caja.maxY - caja.minY) * M;
    const fondo = (caja.maxX - caja.minX) * M;
    const alto = (c.altura || 200) * M;
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(ancho, alto, fondo),
      new THREE.MeshStandardMaterial({ color: 0x50505e, roughness: 0.9 })
    );
    const centro = { x: (caja.minX + caja.maxX) / 2, y: (caja.minY + caja.maxY) / 2 };
    m.position.copy(aTres(centro, (c.cota || 0)));
    m.position.y += alto / 2;
    m.castShadow = true; m.receiveShadow = true;
    this.mundo.add(m);
  }

  _plataforma(p) {
    const caja = cajaDe(p.poli);
    const ancho = (caja.maxY - caja.minY) * M;
    const fondo = (caja.maxX - caja.minX) * M;
    const alto = (p.cota || 0) * M;
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(ancho, alto, fondo),
      new THREE.MeshStandardMaterial({ color: 0x3a4252, roughness: 0.9 })
    );
    const centro = { x: (caja.minX + caja.maxX) / 2, y: (caja.minY + caja.maxY) / 2 };
    m.position.copy(aTres(centro, 0));
    m.position.y = alto / 2;
    m.castShadow = true; m.receiveShadow = true;
    this.mundo.add(m);

    for (const a of (p.accesos || [])) {
      const r = new THREE.Mesh(
        new THREE.CylinderGeometry(0.9, 0.9, alto, 12),
        new THREE.MeshStandardMaterial({ color: 0x7cb342, roughness: 0.8 })
      );
      r.position.copy(aTres(a, 0));
      r.position.y = alto / 2;
      this.mundo.add(r);
    }
  }

  _marcadores(enc) {
    const e = new THREE.Mesh(
      new THREE.CircleGeometry(1.2, 24),
      new THREE.MeshBasicMaterial({ color: COLOR_MALAKH, transparent: true, opacity: 0.35 })
    );
    e.rotation.x = -Math.PI / 2;
    e.position.copy(aTres(enc.arena.entrada, 0));
    e.position.y = 0.02;
    this.mundo.add(e);

    const t = enc.arena.trigger;
    if (t) {
      const anillo = new THREE.Mesh(
        new THREE.RingGeometry(t.radio * M * 0.92, t.radio * M, 32),
        new THREE.MeshBasicMaterial({ color: 0xb58ad8, transparent: true, opacity: 0.55, side: THREE.DoubleSide })
      );
      anillo.rotation.x = -Math.PI / 2;
      anillo.position.copy(aTres(t, 0));
      anillo.position.y = 0.03;
      this.mundo.add(anillo);
    }
  }

  // ------------------------------------------------------------------ agentes

  _capsula(radioCm, alturaCm, color) {
    const r = radioCm * M;
    const h = Math.max(0.1, alturaCm * M - 2 * r);
    const m = new THREE.Mesh(
      new THREE.CapsuleGeometry(r, h, 6, 14),
      new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.1 })
    );
    m.position.y = r + h / 2;
    m.castShadow = true;
    return m;
  }

  // ------------------------------------------------- chapas de estado y vida

  /**
   * La planta 2D enseña vida y estado de un vistazo; la 3D era ciega al lado.
   * Cada agente lleva una "chapa": un sprite con la barra de vida y el glifo del
   * estado, dibujado en un canvas. Un solo sprite por agente, y solo se redibuja
   * cuando cambia algo — mover la camara no cuesta nada.
   */
  _chapa() {
    const lienzo = document.createElement('canvas');
    lienzo.width = 128; lienzo.height = 48;
    const tex = new THREE.CanvasTexture(lienzo);
    tex.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
      map: tex, transparent: true, depthTest: false, depthWrite: false
    }));
    sprite.scale.set(1.6, 0.6, 1);
    sprite.renderOrder = 999;      // por encima de todo: es informacion, no escenario
    sprite.userData = { lienzo, tex, firma: null };
    return sprite;
  }

  /** Glifos y colores, los mismos que la planta para no tener que traducir. */
  static get ESTADOS_CHAPA() {
    return {
      anticipacion: { glifo: '!', color: '#d9a441' },   // levanta el arma
      activo:       { glifo: '✳', color: '#ff5c48' },   // el golpe esta saliendo
      recuperacion: { glifo: '·', color: '#8a8a96' },
      esquiva:      { glifo: '~', color: '#9fd0e8' },
      bloqueando:   { glifo: '▮', color: '#7fa8e8' },
      curando:      { glifo: '+', color: '#7cb342' },
      recogiendo:   { glifo: '⌾', color: '#d4af37' },
      aturdido:     { glifo: '×', color: '#ffffff' }
    };
  }

  _pintarChapa(sprite, a, hpMax) {
    const est = Vista3D.ESTADOS_CHAPA[a.estado];
    const frac = Math.max(0, Math.min(1, a.hp / (hpMax || 100)));
    const firma = `${Math.round(frac * 100)}|${a.estado}|${a.golpeado ? (a.golpeBloqueado ? 'b' : 'g') : ''}`;
    if (sprite.userData.firma === firma) return;     // nada que redibujar
    sprite.userData.firma = firma;

    const { lienzo, tex } = sprite.userData;
    const c = lienzo.getContext('2d');
    c.clearRect(0, 0, 128, 48);

    // Destello de impacto: rojo si entro, azul si lo paro la guardia.
    if (a.golpeado) {
      c.fillStyle = a.golpeBloqueado ? 'rgba(127,168,232,.55)' : 'rgba(255,92,72,.55)';
      c.beginPath();
      c.arc(64, 30, 26, 0, Math.PI * 2);
      c.fill();
    }

    // Barra de vida
    c.fillStyle = 'rgba(0,0,0,.75)';
    c.fillRect(20, 24, 88, 10);
    c.fillStyle = frac > 0.5 ? '#7cb342' : frac > 0.22 ? '#d9a441' : '#c4483f';
    c.fillRect(21, 25, 86 * frac, 8);
    c.strokeStyle = 'rgba(255,255,255,.35)';
    c.lineWidth = 1;
    c.strokeRect(20.5, 24.5, 87, 9);

    // Glifo del estado, encima
    if (est) {
      c.font = 'bold 22px "Segoe UI Symbol", "Segoe UI", sans-serif';
      c.textAlign = 'center';
      c.textBaseline = 'middle';
      c.lineWidth = 4;
      c.strokeStyle = 'rgba(0,0,0,.9)';
      c.strokeText(est.glifo, 64, 11);
      c.fillStyle = est.color;
      c.fillText(est.glifo, 64, 11);
    }
    tex.needsUpdate = true;
  }

  _agenteMalakh(cal) {
    const g = new THREE.Group();
    g.add(this._capsula(cal.malakh.radio, 190, COLOR_MALAKH));
    // Espada base: siempre presente, porque nunca desaparece (§ regla central).
    const espada = new THREE.Mesh(
      new THREE.BoxGeometry(0.08, 1.1, 0.02),
      new THREE.MeshStandardMaterial({ color: 0xd8d8e0, metalness: 0.7, roughness: 0.3 })
    );
    espada.position.set(0.45, 1.0, 0.1);
    espada.rotation.z = -0.5;
    espada.name = 'espada';
    g.add(espada);

    const arma = new THREE.Group();       // arma temporal, se rellena en cada fotograma
    arma.name = 'temporal';
    g.add(arma);

    const chapa = this._chapa();
    chapa.name = 'chapa';
    chapa.position.y = 2.5;
    g.add(chapa);
    return g;
  }

  /**
   * La silueta ES la señal del §5.1. Cada arquetipo lleva su arma en la mano
   * con su tamaño real: la lanza mide 3,2 m y se ve desde la puerta; el escudo
   * esta pegado al cuerpo y casi no cambia el contorno. Eso es lo que hay que
   * poder juzgar mirando, no leyendo la ficha.
   */
  _agenteEnemigo(e, cal) {
    const meta = ARQUETIPOS[e.arquetipo] || {};
    const perfil = cal.arquetipos[e.arquetipo] || {};
    const color = new THREE.Color(meta.color || '#888888');
    const g = new THREE.Group();
    const altura = e.arquetipo === 'elite_pesado' ? 230 : 190;
    g.add(this._capsula(perfil.radio || 45, altura, color));
    const prop = this._siluetaDeArma(perfil.arma, color);
    if (prop) g.add(prop);

    // Un aro en el suelo marca al portador de la llave tactica (solo debug).
    if (e.drop === 'garantizado') {
      const aro = new THREE.Mesh(
        new THREE.RingGeometry(0.75, 0.9, 24),
        new THREE.MeshBasicMaterial({ color: 0xd4af37, side: THREE.DoubleSide, transparent: true, opacity: 0.8 })
      );
      aro.rotation.x = -Math.PI / 2;
      aro.position.y = 0.04;
      g.add(aro);
    }

    const chapa = this._chapa();
    chapa.name = 'chapa';
    chapa.position.y = (altura / 100) + 0.6;
    g.add(chapa);
    return g;
  }

  _siluetaDeArma(familia, color) {
    const mat = new THREE.MeshStandardMaterial({
      color: 0xe8dcc0, emissive: color.clone().multiplyScalar(0.35), roughness: 0.4, metalness: 0.5
    });
    switch (familia) {
      case 'lanza_del_alba': {
        const l = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 3.2, 8), mat);
        l.position.set(0.4, 1.6, 0);
        l.rotation.z = 0.22;
        l.castShadow = true;
        return l;
      }
      case 'arco_del_firmamento': {
        const b = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.04, 6, 20, Math.PI * 1.25), mat);
        b.position.set(0.4, 1.2, 0);
        b.rotation.y = Math.PI / 2;
        b.castShadow = true;
        return b;
      }
      case 'escudo_celestial': {
        const s = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.9, 0.7), mat);
        s.position.set(-0.35, 1.15, 0);
        s.castShadow = true;
        return s;
      }
      case 'espadon_alabarda': {
        const a = new THREE.Group();
        const asta = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2.4, 8), mat);
        const hoja = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.6, 0.05), mat);
        hoja.position.y = 1.1;
        a.add(asta, hoja);
        a.position.set(0.5, 1.4, 0);
        a.rotation.z = 0.3;
        return a;
      }
      case 'estandarte_ritual': {
        const a = new THREE.Group();
        const poste = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3.4, 8), mat);
        const tela = new THREE.Mesh(
          new THREE.PlaneGeometry(0.7, 1.2),
          new THREE.MeshStandardMaterial({ color: 0xb58ad8, side: THREE.DoubleSide, roughness: 0.9 })
        );
        tela.position.set(0.36, 1.1, 0);
        a.add(poste, tela);
        a.position.set(0.4, 1.7, 0);
        return a;
      }
      default: return null;
    }
  }

  _plantarEnPosicionInicial(enc, cal) {
    const sano = (g, id, hpMax) => {
      const chapa = g.getObjectByName('chapa');
      if (chapa) {
        chapa.visible = true;
        this._pintarChapa(chapa, { id, hp: hpMax, estado: 'libre', golpeado: false }, hpMax);
      }
    };

    const m = this.grupos.get('malakh');
    if (m) {
      m.position.copy(aTres(enc.arena.entrada, 0));
      m.rotation.set(0, 0, 0);
      m.visible = true;
      sano(m, 'malakh', cal.malakh.hp);
    }
    for (const e of enc.enemigos) {
      const g = this.grupos.get(e.id);
      if (!g) continue;
      g.position.copy(aTres(e.pos, e.cota));
      g.rotation.set(0, -(e.yaw ?? 180) * Math.PI / 180, 0);
      g.visible = true;
      g.traverse(h => { if (h.material) { h.material.transparent = false; h.material.opacity = 1; } });
      sano(g, e.id, cal.arquetipos[e.arquetipo]?.hp || 100);
    }
    this._pintarDrops([]);
  }

  // --------------------------------------------------------------- fotograma

  mostrar(fotograma) {
    const { enc, cal } = this.estado();
    if (!fotograma) { this._plantarEnPosicionInicial(enc, cal); return; }

    for (const a of fotograma.agentes) {
      const g = this.grupos.get(a.id);
      if (!g) continue;
      g.position.copy(aTres({ x: a.x, y: a.y }, a.cota));
      g.rotation.y = -a.yaw * Math.PI / 180;
      const muerto = a.estado === 'muerto';
      g.visible = true;
      // Los caidos se tumban: se sigue viendo donde cayo cada uno.
      g.rotation.x = muerto ? -Math.PI / 2.2 : 0;

      const chapa = g.getObjectByName('chapa');
      for (const o of g.children) {
        if (o === chapa) continue;
        o.traverse(h => {
          if (!h.material) return;
          h.material.transparent = muerto;
          h.material.opacity = muerto ? 0.35 : 1;
        });
      }

      if (chapa) {
        // A un muerto no se le pone barra de vida: solo estorba.
        chapa.visible = !muerto;
        if (!muerto) {
          const hpMax = a.hpMax || (a.id === 'malakh'
            ? cal.malakh.hp
            : cal.arquetipos[enc.enemigos.find(e => e.id === a.id)?.arquetipo]?.hp) || 100;
          this._pintarChapa(chapa, a, hpMax);
        }
      }
    }

    // El arma temporal que lleva Malakh ahora mismo.
    const gm = this.grupos.get('malakh');
    if (gm) {
      const ranura = gm.getObjectByName('temporal');
      const actual = ranura.userData.familia || null;
      if (actual !== (fotograma.arma || null)) {
        this._vaciar(ranura);
        ranura.userData.familia = fotograma.arma || null;
        const prop = fotograma.arma
          ? this._siluetaDeArma(fotograma.arma, new THREE.Color(FAMILIAS[fotograma.arma]?.color || '#d4af37'))
          : null;
        if (prop) ranura.add(prop);
      }
      const espada = gm.getObjectByName('espada');
      if (espada) espada.visible = !fotograma.arma;   // a dos manos, la espada se guarda
    }

    this._pintarDrops(fotograma.drops || []);
    this.pintar();
  }

  _pintarDrops(drops) {
    for (const d of this.dropsVivos) {
      this.actores.remove(d);
      d.geometry?.dispose(); d.material?.dispose();
    }
    this.dropsVivos = [];
    for (const d of drops) {
      const color = new THREE.Color(FAMILIAS[d.familia]?.color || '#d4af37');
      const m = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.35),
        new THREE.MeshStandardMaterial({ color, emissive: color.clone().multiplyScalar(0.6), roughness: 0.3 })
      );
      m.position.copy(aTres(d, 0));
      m.position.y = 0.5;
      this.actores.add(m);
      this.dropsVivos.push(m);
    }
  }

  // ---------------------------------------------------- lectura desde entrada

  /**
   * Dibuja lo que se ve desde la puerta: una linea por enemigo, verde si su
   * silueta llega y roja si esta tapado. Es el §5.1 hecho imagen.
   */
  alternarLineasDeEntrada(encender) {
    if (this.lineas) {
      this.mundo.remove(this.lineas);
      this.lineas.traverse(o => { o.geometry?.dispose?.(); o.material?.dispose?.(); });
      this.lineas = null;
    }
    if (!encender) { this.pintar(); return; }

    const { enc, cal } = this.estado();
    const grupo = new THREE.Group();
    const ojos = aTres(enc.arena.entrada, 0);
    ojos.y = cal.malakh.alturaOjos * M;

    for (const f of lecturaDesdeLaEntrada(enc, cal)) {
      const e = enc.enemigos.find(x => x.id === f.id);
      if (!e) continue;
      const hasta = aTres(e.pos, e.cota);
      hasta.y += 1.0;
      const color = f.estado === 'legible' ? 0x7cb342 : f.estado === 'lejos' ? 0xd9a441 : 0xc4483f;
      const mat = new THREE.MeshBasicMaterial({
        color, transparent: true, opacity: f.visible ? 0.75 : 0.35, depthWrite: false
      });

      // Tubo en vez de linea: una linea de 1 px es invisible en una escena 3D,
      // y un overlay de depuracion que no se ve no sirve para depurar nada.
      const largo = ojos.distanceTo(hasta);
      const tubo = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, largo, 6), mat);
      tubo.position.copy(ojos).lerp(hasta, 0.5);
      tubo.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        hasta.clone().sub(ojos).normalize()
      );
      grupo.add(tubo);

      // Y una marca en el destino, para contar de un vistazo cuantos se leen.
      const marca = new THREE.Mesh(new THREE.SphereGeometry(0.35, 10, 8), mat);
      marca.position.copy(hasta);
      grupo.add(marca);
    }
    this.lineas = grupo;
    this.mundo.add(grupo);
    this.pintar();
  }

  // ------------------------------------------------------------------ camaras

  ponerCamara(cual) {
    this.camaraActual = cual;
    // La camara de entrada usa el FOV de un juego, no el de una maqueta:
    // si la miras con 55 grados la lanza "se lee" mejor de lo que se leera.
    this.cam.fov = cual === 'entrada' ? 70 : 55;
    this.cam.updateProjectionMatrix();
    this.pintar();
  }

  _colocarCamara() {
    const { enc, cal } = this.estado();
    const centro = centroide(enc.arena.bounds);

    if (this.camaraActual === 'entrada') {
      const p = aTres(enc.arena.entrada, 0);
      p.y = cal.malakh.alturaOjos * M;
      this.cam.position.copy(p);
      const mira = aTres(centro, 0);
      mira.y = cal.malakh.alturaOjos * M;
      this.cam.lookAt(mira);
      return;
    }

    if (this.camaraActual === 'malakh') {
      const g = this.grupos.get('malakh');
      if (g) {
        const atras = new THREE.Vector3(Math.sin(g.rotation.y), 0, Math.cos(g.rotation.y)).multiplyScalar(-5.5);
        this.cam.position.copy(g.position).add(atras).add(new THREE.Vector3(0, 3.2, 0));
        this.cam.lookAt(g.position.clone().add(new THREE.Vector3(0, 1.2, 0)));
        return;
      }
    }

    if (this.camaraActual === 'cenital') {
      const c = aTres(centro, 0);
      this.cam.position.set(c.x, this.orbita.radio * 1.25, c.z + 0.01);
      this.cam.lookAt(c);
      return;
    }

    const { radio, theta, phi, centro: c } = this.orbita;
    this.cam.position.set(
      c.x + radio * Math.cos(phi) * Math.cos(theta),
      c.y + radio * Math.sin(phi),
      c.z + radio * Math.cos(phi) * Math.sin(theta)
    );
    this.cam.lookAt(c);
  }

  // -------------------------------------------------------------------- bucle

  _ajustar() {
    const r = this.cont.getBoundingClientRect();
    if (!r.width || !r.height) return;
    this.render3d.setSize(r.width, r.height, false);
    this.cam.aspect = r.width / r.height;
    this.cam.updateProjectionMatrix();
  }

  /**
   * Un fotograma, ya. El bucle de rAF se para cuando la pestaña esta oculta,
   * asi que cada cambio de estado repinta por su cuenta en vez de esperarlo.
   */
  pintar() {
    if (!this.cont.clientWidth) return;
    this._colocarCamara();
    this.render3d.render(this.escena, this.cam);
  }

  arrancar() {
    this.activa = true;
    this._ajustar();
    const bucle = () => {
      if (!this.activa) return;
      this.pintar();
      this._raf = requestAnimationFrame(bucle);
    };
    bucle();
  }

  parar() {
    this.activa = false;
    cancelAnimationFrame(this._raf);
  }
}
