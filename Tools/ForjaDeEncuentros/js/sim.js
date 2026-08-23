// Simulador determinista del encuentro.
//
// Reglas de la casa:
//  - Nada de Math.random: todo sale del Azar sembrado, o el lote de 200 partidas
//    no compara politicas, compara ruido.
//  - Nada de render aqui dentro: esto tiene que poder correr 1000 veces sin pintar.
//  - Todo numero de balance viene de calibracion.json o armas.json, nunca a pelo.

import { Azar } from './rng.js';
import { obstaculosDe, dentroDeRect, centroDeRect, poliDeRect } from './esquema.js';
import {
  dist, resta, suma, escala, normaliza, largo, yawDe, giraHacia, deltaAngulo,
  dentroDePoligono, hayVision, empujaFuera, segmentoCortaPoligono, centroide
} from './geometria.js';
import {
  perfilAtaque, perfilBloqueo, descarteDe, equipar, gastarRecurso,
  consumirPorDescarte, consumirOffHandPorDescarte, purgarPorSeal, decideDrop
} from './armas.js';

export const ESTADOS = {
  LIBRE: 'libre',
  ANTICIPACION: 'anticipacion',
  ACTIVO: 'activo',
  RECUPERACION: 'recuperacion',
  ESQUIVA: 'esquiva',
  CURANDO: 'curando',
  RECOGIENDO: 'recogiendo',
  ATURDIDO: 'aturdido',
  MUERTO: 'muerto'
};

const AGUANTE_POR_DEFECTO = { arquero_del_firmamento: 20, elite_pesado: 120 };
const REGEN_AGUANTE = 20;
const RADIO_ALERTA_ALIADOS = 900;

export class Simulacion {
  constructor(encuentro, calibracion, armas, politica, semilla, opciones = {}) {
    this.enc = encuentro;
    this.cal = calibracion;
    this.armas = armas;
    this.politica = politica;
    this.azar = new Azar(semilla);
    this.semilla = semilla;
    this.dt = calibracion.reglas.dt;
    this.tiempoLimite = opciones.tiempoLimite ?? calibracion.reglas.tiempoLimite;
    this.grabar = opciones.grabar || false;
    this.cadaCuantosFotogramas = opciones.cadaCuantosFotogramas || 2;

    this.t = 0;
    this.tick = 0;
    this.proyectiles = [];
    this.drops = [];
    this.zonas = [];
    this.eventos = [];
    this.fotogramas = [];
    this.terminada = false;
    this.razonFin = null;
    this._contadorDrops = 0;
    this.maxDropsSimultaneos = 0;

    this._montar();
    if (this.politica.iniciar) this.politica.iniciar(this);
  }

  // ------------------------------------------------------------------ montaje

  _montar() {
    const cal = this.cal;
    const m = cal.malakh;
    this.malakh = {
      id: 'malakh',
      bando: 'malakh',
      nombre: 'Malakh',
      pos: { ...this.enc.jugador.pos },
      cota: 0,
      yaw: 0,
      radio: m.radio,
      hp: m.hp, hpMax: m.hp,
      stamina: m.stamina, staminaMax: m.stamina,
      aguante: 100, aguanteMax: 100,
      estado: ESTADOS.LIBRE,
      tEstado: 0,
      accion: null,
      objetivoId: null,
      perfil: m,
      bloqueando: false,
      // --- armas temporales (Fase B) ---
      temporal: null,
      offHand: null,
      armasRecogidas: [],
      descartesUsados: 0,
      tUltimaArma: null,
      // --- consumibles y estadistica ---
      pociones: m.pocion ? m.pocion.cantidad : 0,
      pocionesBebidas: 0,
      curacionTotal: 0,
      danoRecibido: 0,
      golpesAsestados: 0,
      golpesFallados: 0,
      esquivasLogradas: 0
    };
    this.malakh.cota = this.enc.jugador.cota || 0;
    this.malakh.yaw = yawDe(resta(centroDeRect(this.enc.arena.bounds), this.malakh.pos));

    this.enemigos = this.enc.enemigos.map(e => {
      const p = cal.arquetipos[e.arquetipo];
      if (!p) throw new Error(`Arquetipo desconocido en calibracion: ${e.arquetipo}`);
      const aguante = AGUANTE_POR_DEFECTO[e.arquetipo] ?? 40;
      return {
        id: e.id,
        bando: 'enemigo',
        arquetipo: e.arquetipo,
        nombre: p.nombre,
        etiqueta: e.etiqueta || '',
        drop: e.drop,
        pos: { ...e.pos },
        cota: e.cota || 0,
        yaw: e.yaw ?? 180,
        radio: p.radio,
        hp: p.hp, hpMax: p.hp,
        aguante, aguanteMax: aguante,
        estado: ESTADOS.LIBRE,
        tEstado: 0,
        accion: null,
        recarga: this.azar.rango(0, p.recarga * 0.5),
        alertado: false,
        perfil: p,
        danoInfligido: 0,
        tMuerte: null
      };
    });

    this.agentes = [this.malakh, ...this.enemigos];
    // Muros Y plataformas: desde abajo una plataforma es un bloque, no aire.
    this.coberturas = obstaculosDe(this.enc);
    this.plataformas = this.enc.plataformas || [];
  }

  // -------------------------------------------------------------------- bucle

  correr() {
    while (!this.terminada) this.paso();
    return this.resultado();
  }

  paso() {
    if (this.terminada) return;
    const dt = this.dt;

    this._pasoProyectiles(dt);
    this._pasoDrops(dt);
    this._pasoZonas(dt);
    this._pasoMalakh(dt);
    for (const e of this.enemigos) this._pasoEnemigo(e, dt);
    this._separarAgentes();

    for (const a of this.agentes) {
      if (a.estado === ESTADOS.MUERTO) continue;
      a.aguante = Math.min(a.aguanteMax, a.aguante + REGEN_AGUANTE * dt);
    }
    this.malakh.stamina = Math.min(
      this.malakh.staminaMax,
      this.malakh.stamina + this.cal.malakh.regenStamina * dt
    );

    this.t += dt;
    this.tick += 1;
    this.maxDropsSimultaneos = Math.max(this.maxDropsSimultaneos, this.drops.length);
    if (this.grabar && this.tick % this.cadaCuantosFotogramas === 0) this._grabarFotograma();
    this._comprobarFin();
  }

  _comprobarFin() {
    const vivos = this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO);
    if (this.malakh.hp <= 0) {
      this.terminada = true; this.razonFin = 'muerte';
      this._evento('derrota', { motivo: 'Malakh cae' });
    } else if (vivos.length === 0) {
      this.terminada = true; this.razonFin = 'victoria';
      this._evento('victoria', { tiempo: this.t });
      // REGLA DE SEAL BREAK: todo lo temporal se desmaterializa (§ prompt maestro).
      const purgado = purgarPorSeal(this.malakh);
      this.drops = [];
      if (purgado.length) this._evento('sealBreak', { purgado });
    } else if (this.t >= this.tiempoLimite) {
      this.terminada = true; this.razonFin = 'tiempo';
      this._evento('derrota', { motivo: `Se agoto el limite de ${this.tiempoLimite}s`, vivos: vivos.length });
    }
  }

  // ------------------------------------------------------------------- Malakh

  _pasoMalakh(dt) {
    const M = this.malakh;
    if (M.estado === ESTADOS.MUERTO) return;

    M.bloqueando = false;
    M.tEstado += dt;

    if (M.estado === ESTADOS.ATURDIDO) {
      if (M.tEstado >= M.accion.duracion) this._aLibre(M);
      return;
    }

    if (M.estado === ESTADOS.CURANDO) {
      if (M.tEstado >= M.accion.duracion) {
        const cura = Math.min(M.accion.curacion, M.hpMax - M.hp);
        M.hp += cura;
        M.curacionTotal += cura;
        this._evento('curado', { agente: M.id, cura: +cura.toFixed(1), restantes: M.pociones });
        this._aLibre(M);
      }
      return;
    }

    if (M.estado === ESTADOS.RECOGIENDO) {
      if (M.tEstado >= M.accion.duracion) {
        this._completarRecogida(M.accion.dropId);
        this._aLibre(M);
      }
      return;
    }

    if (M.estado === ESTADOS.ESQUIVA) {
      const a = M.accion;
      this._mover(M, escala(a.dir, (a.distancia / a.duracion) * dt));
      if (M.tEstado >= a.duracion) this._aLibre(M);
      return;
    }

    if (M.estado !== ESTADOS.LIBRE) {
      this._avanzarAtaque(M, dt);
      return;
    }

    // --- libre: decide la politica ---
    const intencion = this.politica.decidir(this, M);
    M.objetivoId = intencion.objetivo || M.objetivoId;
    const obj = this.agente(M.objetivoId);

    if (intencion.accion === 'esquivar' && M.stamina >= this.cal.malakh.esquiva.costeStamina) {
      this._iniciarEsquiva(M, intencion.direccion);
      return;
    }

    if (intencion.accion === 'beber' && M.pociones > 0) {
      const p = this.cal.malakh.pocion;
      M.pociones -= 1;
      M.pocionesBebidas += 1;
      M.estado = ESTADOS.CURANDO;
      M.tEstado = 0;
      M.accion = { duracion: p.duracion, curacion: p.curacion };
      this._evento('bebe', { agente: M.id, restantes: M.pociones });
      return;
    }

    // --- recoger un arma del suelo (§4.1) ---
    if (intencion.accion === 'recoger') {
      const drop = this.drops.find(d => d.id === intencion.dropId);
      if (drop) {
        if (dist(M.pos, drop.pos) <= this.armas.reglas.radioRecogida &&
            Math.abs((drop.cota || 0) - M.cota) <= 120) {
          M.estado = ESTADOS.RECOGIENDO;
          M.tEstado = 0;
          M.accion = { duracion: this.armas.reglas.duracionRecogida, dropId: drop.id };
          return;
        }
        this._avanzarHacia(M, { pos: drop.pos, cota: drop.cota, radio: 0 }, 0, dt);
        return;
      }
    }

    // --- ataque de descarte (§3.2): sacrificar el arma por un remate ---
    if (intencion.accion === 'descartar') {
      const d = descarteDe(M, this.armas);
      if (d) { this._iniciarDescarte(M, d); return; }
    }

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      M.yaw = giraHacia(M.yaw, yawDe(resta(obj.pos, M.pos)), M.perfil.velocidadGiro * dt);
    }

    if (intencion.accion === 'bloquear') {
      M.bloqueando = true;
      if (intencion.mirarA) {
        M.yaw = giraHacia(M.yaw, yawDe(resta(intencion.mirarA, M.pos)), M.perfil.velocidadGiro * dt);
      }
      if (intencion.direccion) {
        const f = perfilBloqueo(M, this.cal, this.armas).factorVelocidad;
        this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * f * dt));
      }
      return;
    }

    if (intencion.accion === 'reposicionar' && intencion.direccion) {
      this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * dt));
      return;
    }

    if (intencion.accion === 'atacar' || intencion.accion === 'atacarPesado') {
      const perfil = perfilAtaque(M, this.cal, this.armas, intencion.accion === 'atacarPesado');
      if (obj && this._enAlcance(M, obj, perfil.alcance) && M.stamina >= (perfil.costeStamina || 0)) {
        if (!perfil.necesitaVision ||
            hayVision(M.pos, M.cota, obj.pos, obj.cota, this.coberturas, this.cal.malakh.alturaOjos)) {
          this._iniciarAtaque(M, perfil);
          return;
        }
      }
    }

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      const perfil = perfilAtaque(M, this.cal, this.armas, false);
      this._avanzarHacia(M, obj, perfil.alcance * 0.7, dt);
    }
  }

  _iniciarEsquiva(M, direccion) {
    const e = this.cal.malakh.esquiva;
    M.stamina -= e.costeStamina;
    M.estado = ESTADOS.ESQUIVA;
    M.tEstado = 0;
    M.accion = { ...e, dir: normaliza(direccion || { x: -1, y: 0 }) };
    this._evento('esquiva', { agente: M.id });
  }

  _completarRecogida(dropId) {
    const i = this.drops.findIndex(d => d.id === dropId);
    if (i < 0) return;
    const drop = this.drops[i];
    this.drops.splice(i, 1);
    const M = this.malakh;
    for (const ev of equipar(M, drop.familia, this.armas, drop.origenId)) {
      this._evento(ev.tipo, { agente: M.id, ...ev });
    }
    M.armasRecogidas.push({ familia: drop.familia, t: +this.t.toFixed(2), origen: drop.origenId });
    M.tUltimaArma = this.t;
  }

  _iniciarDescarte(M, d) {
    M.estado = ESTADOS.ANTICIPACION;
    M.tEstado = 0;
    M.accion = {
      ...d,
      esDescarte: true,
      ventana: d.ventana ?? 0.12,
      arco: d.arco ?? 360,
      yaGolpeo: false,
      dano: d.dano + (d.danoPorFlechaRestante ? d.danoPorFlechaRestante * (M.temporal?.municion || 0) : 0)
    };
    M.descartesUsados += 1;
    const ev = M.temporal ? consumirPorDescarte(M) : consumirOffHandPorDescarte(M);
    this._evento('descarte', { agente: M.id, nombre: d.nombre, arma: ev?.arma, objetivo: M.objetivoId });
  }

  // -------------------------------------------------------------------- enemigos

  _pasoEnemigo(E, dt) {
    if (E.estado === ESTADOS.MUERTO) return;
    const M = this.malakh;
    E.tEstado += dt;
    E.recarga = Math.max(0, E.recarga - dt);

    if (E.estado === ESTADOS.ATURDIDO) {
      if (E.tEstado >= E.accion.duracion) this._aLibre(E);
      return;
    }
    if (E.estado !== ESTADOS.LIBRE) {
      this._avanzarAtaque(E, dt);
      return;
    }

    if (!E.alertado) {
      const d = dist(E.pos, M.pos);
      const ve = hayVision(E.pos, E.cota, M.pos, M.cota, this.coberturas, this.cal.malakh.alturaOjos);
      if (d <= E.perfil.rangoAggro && ve) this._alertar(E);
      else return;
    }

    E.yaw = giraHacia(E.yaw, yawDe(resta(M.pos, E.pos)), E.perfil.velocidadGiro * dt);

    if (E.arquetipo === 'arquero_del_firmamento') this._pasoArquero(E, dt);
    else this._pasoCuerpoACuerpo(E, dt);
  }

  _alertar(E) {
    if (E.alertado) return;
    E.alertado = true;
    this._evento('alerta', { agente: E.id });
    for (const otro of this.enemigos) {
      if (otro.alertado || otro.estado === ESTADOS.MUERTO) continue;
      if (dist(otro.pos, E.pos) <= RADIO_ALERTA_ALIADOS) otro.alertado = true;
    }
  }

  _pasoCuerpoACuerpo(E, dt) {
    const M = this.malakh;
    const p = E.perfil;
    const d = dist(E.pos, M.pos) - M.radio;
    if (d > p.alcanceAtaque * 0.95) {
      this._avanzarHacia(E, M, p.distanciaPreferida, dt);
      return;
    }
    if (E.recarga <= 0 && Math.abs(deltaAngulo(E.yaw, yawDe(resta(M.pos, E.pos)))) < 35) {
      this._iniciarAtaque(E, { ...p.ataque, alcance: p.alcanceAtaque, dano: p.dano });
    }
  }

  _pasoArquero(E, dt) {
    const M = this.malakh;
    const p = E.perfil;
    const d = dist(E.pos, M.pos);
    const ve = hayVision(E.pos, E.cota, M.pos, M.cota, this.coberturas, this.cal.malakh.alturaOjos);

    // Retirada con presupuesto. Un arquero que retrocede sin limite contra un
    // Malakh que tiene que esquivar flechas produce tablas eternas: los dos
    // movimientos se cancelan y la arena no se cierra nunca. Agotado el
    // presupuesto se planta y dispara a bocajarro.
    if (d < p.distanciaMinima && (E.tRetirada || 0) < (p.segundosDeRetirada ?? Infinity)) {
      E.tRetirada = (E.tRetirada || 0) + dt;
      this._mover(E, escala(normaliza(resta(E.pos, M.pos)), this._velocidadDe(E) * dt));
      return;
    }
    if (d > p.distanciaMinima * 1.4) E.tRetirada = 0;   // recupera el presupuesto al abrir hueco
    if (!ve) {
      const hacia = normaliza(resta(M.pos, E.pos));
      this._mover(E, escala({ x: -hacia.y, y: hacia.x }, this._velocidadDe(E) * 0.6 * dt));
      return;
    }
    if (d > p.alcanceAtaque) { this._avanzarHacia(E, M, p.distanciaPreferida, dt); return; }
    if (E.recarga <= 0) {
      this._iniciarAtaque(E, { ...p.ataque, alcance: p.alcanceAtaque, dano: p.dano, proyectil: true, velocidad: p.velocidadProyectil });
    }
  }

  // ---------------------------------------------------------------- ataques

  _iniciarAtaque(A, perfil) {
    A.estado = ESTADOS.ANTICIPACION;
    A.tEstado = 0;
    A.accion = { ...perfil, yaGolpeo: false };
    if (A.bando === 'malakh') A.stamina -= perfil.costeStamina || 0;
    this._evento('ataque', {
      agente: A.id,
      pesado: !!perfil.esPesado,
      arma: perfil.familia || null,
      objetivo: A.bando === 'malakh' ? A.objetivoId : 'malakh'
    });
  }

  _avanzarAtaque(A, dt) {
    const a = A.accion;
    const t = A.tEstado;
    const ini = a.impacto, fin = a.impacto + (a.ventana ?? 0.12);

    if (t < ini) A.estado = ESTADOS.ANTICIPACION;
    else if (t <= fin) A.estado = ESTADOS.ACTIVO;
    else A.estado = ESTADOS.RECUPERACION;

    if (A.estado === ESTADOS.ACTIVO && !a.yaGolpeo) {
      a.yaGolpeo = true;
      if (a.tipo === 'zona') this._plantarZona(A, a);
      else if (a.tipo === 'aoe') this._golpeEnArea(A, a);
      else if (a.proyectil || a.tipo === 'proyectil') this._lanzarProyectil(A, a);
      else this._resolverGolpeCuerpoACuerpo(A, a);

      if (A.bando === 'malakh' && a.gastaMunicion) {
        const ev = gastarRecurso(A, a.gastaMunicion);
        if (ev) this._evento(ev.tipo, { agente: A.id, arma: ev.arma });
      }
    }

    if (t >= a.duracion) {
      if (A.bando === 'enemigo') A.recarga = A.perfil.recarga;
      this._aLibre(A);
    }
  }

  _resolverGolpeCuerpoACuerpo(A, a) {
    const candidatos = A.bando === 'malakh'
      ? this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO)
      : [this.malakh];

    let alcanzado = false;
    for (const O of candidatos) {
      if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) continue;
      if (dist(A.pos, O.pos) - O.radio > a.alcance) continue;
      if (Math.abs(deltaAngulo(A.yaw, yawDe(resta(O.pos, A.pos)))) > (a.arco || 90) / 2) continue;
      this._aplicarDano(O, a.dano, A, a);
      alcanzado = true;
      if (A.bando === 'malakh' && !a.multiObjetivo) break;
    }
    if (A.bando === 'malakh') {
      if (alcanzado) A.golpesAsestados += 1; else A.golpesFallados += 1;
    }
  }

  _golpeEnArea(A, a) {
    const candidatos = A.bando === 'malakh'
      ? this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO)
      : [this.malakh];
    let alcanzado = false;
    for (const O of candidatos) {
      if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) continue;
      if (dist(A.pos, O.pos) - O.radio > a.radio) continue;
      this._aplicarDano(O, a.dano, A, a);
      alcanzado = true;
    }
    if (A.bando === 'malakh') { if (alcanzado) A.golpesAsestados += 1; else A.golpesFallados += 1; }
  }

  _plantarZona(A, a) {
    this.zonas.push({
      pos: { ...A.pos },
      radio: a.radio,
      ttl: a.duracionZona,
      factorDano: a.factorDanoEnemigo ?? 1,
      factorVelocidad: a.factorVelocidadEnemigo ?? 1
    });
    this._evento('zona', { agente: A.id, radio: a.radio, duracion: a.duracionZona });
  }

  _pasoZonas(dt) {
    this.zonas = this.zonas.filter(z => (z.ttl -= dt) > 0);
  }

  _modificadorZona(agente, campo) {
    let f = 1;
    for (const z of this.zonas) {
      if (dist(agente.pos, z.pos) <= z.radio) f *= z[campo];
    }
    return f;
  }

  _velocidadDe(A) {
    const base = A.perfil.velocidad;
    return A.bando === 'enemigo' ? base * this._modificadorZona(A, 'factorVelocidad') : base;
  }

  _lanzarProyectil(A, a) {
    const objetivo = A.bando === 'malakh' ? this.agente(A.objetivoId) : this.malakh;
    if (!objetivo || objetivo.estado === ESTADOS.MUERTO) return;
    this.proyectiles.push({
      pos: { ...A.pos },
      cota: A.cota,
      dir: normaliza(resta(objetivo.pos, A.pos)),
      velocidad: a.velocidad || 3500,
      dano: a.dano,
      aturde: !!a.aturde,
      rompeGuardia: !!a.rompeGuardia,
      origenId: A.id,
      bando: A.bando,
      vida: (a.alcance || 2600) / (a.velocidad || 3500) + 0.2
    });
    this._evento('disparo', { agente: A.id, arma: a.familia || null, descarte: !!a.esDescarte });
    if (A.bando === 'malakh') A.golpesAsestados += 0;   // el impacto lo cuenta el proyectil
  }

  _pasoProyectiles(dt) {
    const vivos = [];
    for (const p of this.proyectiles) {
      const antes = { ...p.pos };
      p.pos = suma(p.pos, escala(p.dir, p.velocidad * dt));
      p.vida -= dt;

      let parado = false;
      for (const c of this.coberturas) {
        if (!c.bloqueaVision) continue;
        const cima = (c.cota || 0) + (c.altura || 0);
        if (cima <= p.cota + this.cal.malakh.alturaOjos - 10) continue;
        if (segmentoCortaPoligono(antes, p.pos, c.poli)) { parado = true; break; }
      }
      if (parado) { this._evento('proyectilParado', { origen: p.origenId }); continue; }

      const objetivos = p.bando === 'malakh'
        ? this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO)
        : [this.malakh];
      let impacto = false;
      for (const O of objetivos) {
        if (O.estado === ESTADOS.MUERTO) continue;
        if (dist(p.pos, O.pos) > O.radio + 15) continue;
        this._aplicarDano(O, p.dano, this.agente(p.origenId),
                          { aturde: p.aturde, rompeGuardia: p.rompeGuardia, proyectil: true });
        impacto = true;
        break;
      }
      if (impacto) continue;
      if (p.vida > 0) vivos.push(p);
    }
    this.proyectiles = vivos;
  }

  _aplicarDano(O, cantidad, origen, a = {}) {
    if (O.estado === ESTADOS.MUERTO) return;

    // i-frames de la esquiva
    if (O.bando === 'malakh' && O.estado === ESTADOS.ESQUIVA) {
      const e = this.cal.malakh.esquiva;
      if (O.tEstado >= e.iframeInicio && O.tEstado <= e.iframeFin) {
        O.esquivasLogradas += 1;
        this._evento('esquivado', { agente: O.id, de: origen?.id });
        return;
      }
    }

    let dano = cantidad;
    let bloqueado = false;

    // Guardia de Malakh. El Escudo Celestial la mejora mucho y ademas para flechas.
    if (O.bando === 'malakh' && O.bloqueando && origen) {
      const b = perfilBloqueo(O, this.cal, this.armas);
      const puedeParar = !a.proyectil || b.paraProyectiles;
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < b.arco / 2;
      if (frontal && puedeParar) {
        if (O.stamina >= b.costeStaminaPorGolpe) {
          O.stamina -= b.costeStaminaPorGolpe;
          dano *= 1 - b.reduccion;
          bloqueado = true;
        } else {
          O.stamina = 0; O.aguante = 0;
          this._evento('guardiaRota', { agente: O.id, de: origen.id });
        }
      }
    }

    // Guardia del enemigo. El espadon y el bash la ignoran (guard break).
    const guardia = O.perfil?.guardia || 0;
    if (!a.rompeGuardia && guardia > 0 && origen) {
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < 70;
      if (frontal && this.azar.probabilidad(guardia)) {
        dano *= 1 - (O.perfil.reduccionGuardia ?? 0.75);
        bloqueado = true;
      }
    }

    if (O.bando === 'enemigo') dano *= this._modificadorZona(O, 'factorDano');

    const factor = this.cal.reglas.factorArmadura || 0;
    if (factor > 0) dano = Math.max(1, dano - factor);

    O.hp -= dano;
    // Cuando le entro el ultimo golpe. Un golpe que no aturde no deja estado, y
    // sin esto ni la planta ni la 3D pueden enseñar que a alguien le estan dando.
    O.tUltimoGolpe = this.t;
    O.ultimoGolpeBloqueado = bloqueado;
    if (O.bando === 'malakh') O.danoRecibido += dano;
    if (origen && origen.bando === 'enemigo') origen.danoInfligido += dano;

    this._evento('golpe', {
      de: origen?.id, a: O.id, dano: +dano.toFixed(1), bloqueado,
      arma: a.familia || null, descarte: !!a.esDescarte,
      hpRestante: Math.max(0, +O.hp.toFixed(1))
    });

    if (!bloqueado) {
      O.aguante -= dano * (a.esPesado || a.aturde ? 2 : 1);
      if (a.aturde) O.aguante = Math.min(O.aguante, 0);
      if (O.aguante <= 0 && O.estado !== ESTADOS.MUERTO) {
        O.aguante = O.aguanteMax;
        O.estado = ESTADOS.ATURDIDO;
        O.tEstado = 0;
        O.accion = { duracion: this.cal.malakh.reaccionGolpe };
        if (O.bando === 'enemigo') O.recarga = Math.max(O.recarga, O.perfil.recarga * 0.5);
        this._evento('aturdido', { agente: O.id });
      }
    }

    if (O.hp <= 0) {
      O.hp = 0;
      O.estado = ESTADOS.MUERTO;
      O.accion = null;
      if (O.bando === 'enemigo') {
        O.tMuerte = this.t;
        this._evento('baja', { agente: O.id, arquetipo: O.arquetipo, t: +this.t.toFixed(2), drop: O.drop });
        this._quizaSoltarArma(O);
      }
    }
  }

  // ------------------------------------------------------------------- drops

  _quizaSoltarArma(E) {
    const familia = E.perfil.arma;
    if (!familia || !this.armas.familias[familia]) return;
    if (!decideDrop(E, familia, this.armas)) {
      this._evento('sinDrop', { agente: E.id, ranura: E.drop });
      return;
    }
    const drop = {
      id: `drop_${++this._contadorDrops}`,
      familia,
      pos: { ...E.pos },
      cota: E.cota,
      ttl: this.armas.reglas.ttlEnSuelo,
      origenId: E.id
    };
    this.drops.push(drop);
    this._evento('suelta', { agente: E.id, arma: familia, drop: drop.id, ranura: E.drop });
  }

  _pasoDrops(dt) {
    const vivos = [];
    for (const d of this.drops) {
      d.ttl -= dt;
      if (d.ttl > 0) vivos.push(d);
      else this._evento('dropExpirado', { drop: d.id, arma: d.familia });
    }
    this.drops = vivos;
  }

  // -------------------------------------------------------------- movimiento

  _avanzarHacia(A, objetivo, distanciaParada, dt) {
    const ruta = this._rutaHacia(A, objetivo);
    const destino = ruta.punto;
    const parada = ruta.intermedio ? 0 : distanciaParada;
    const radio = ruta.intermedio ? 0 : (objetivo.radio || 0);
    const d = dist(A.pos, destino) - radio;
    if (d <= parada) return;

    let dir = normaliza(resta(destino, A.pos));
    const bloqueo = this._coberturaEnMedio(A.pos, destino);
    if (bloqueo) {
      const vertice = this._verticeDeRodeo(A.pos, destino, bloqueo);
      if (vertice) dir = normaliza(resta(vertice, A.pos));
    }
    A.yaw = giraHacia(A.yaw, yawDe(dir), (A.perfil.velocidadGiro || 360) * dt);
    this._mover(A, escala(dir, this._velocidadDe(A) * dt));
  }

  _rutaHacia(A, objetivo) {
    const dCota = (objetivo.cota || 0) - (A.cota || 0);
    if (Math.abs(dCota) <= 50) return { punto: objetivo.pos, intermedio: false };

    const plat = dCota > 0
      ? this.plataformas.find(p => dentroDeRect(objetivo.pos, p))
      : this.plataformas.find(p => dentroDeRect(A.pos, p));
    if (!plat || !plat.accesos || !plat.accesos.length) {
      return { punto: objetivo.pos, intermedio: false };
    }

    // Una rampa tiene dos extremos: `desde` al pie y `hasta` arriba. Para subir
    // se va al pie; para bajar, al remate de arriba. Antes era un punto suelto y
    // no se sabia por donde se entraba.
    const subiendo = dCota > 0;
    let mejor = null, mejorD = Infinity;
    for (const r of plat.accesos) {
      const boca = subiendo ? r.desde : r.hasta;
      if (!boca) continue;
      const d = dist(A.pos, boca);
      if (d < mejorD) { mejorD = d; mejor = { boca, rampa: r }; }
    }
    if (!mejor) return { punto: objetivo.pos, intermedio: false };

    // Al pisar la boca, se recorre la rampa. No se simula la subida paso a paso:
    // lo que importa del encuentro es cuanto se tarda en llegar, y eso ya lo
    // cobra el rodeo hasta la boca.
    if (mejorD < 120) {
      A.cota = subiendo ? plat.cota : 0;
      A.pos = { ...(subiendo ? mejor.rampa.hasta : mejor.rampa.desde) };
      return { punto: objetivo.pos, intermedio: false };
    }
    return { punto: mejor.boca, intermedio: true };
  }

  _coberturaEnMedio(a, b) {
    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if (segmentoCortaPoligono(a, b, c.poli)) return c;
    }
    return null;
  }

  _verticeDeRodeo(desde, hasta, cobertura) {
    let mejor = null, mejorCoste = Infinity;
    for (const p of cobertura.poli) {
      const fuera = empujaFuera(p, cobertura.poli, 90);
      const coste = dist(desde, fuera) + dist(fuera, hasta);
      if (coste < mejorCoste) { mejorCoste = coste; mejor = fuera; }
    }
    return mejor;
  }

  _mover(A, delta) {
    let p = suma(A.pos, delta);

    // Quien esta en alto se queda en alto: un balcon tiene barandilla.
    if ((A.cota || 0) > 50) {
      const plat = this.plataformas.find(pl =>
        Math.abs((pl.cota || 0) - A.cota) <= 50 && dentroDeRect(A.pos, pl));
      if (plat && !dentroDeRect(p, plat)) {
        const soloX = { x: p.x, y: A.pos.y }, soloY = { x: A.pos.x, y: p.y };
        if (dentroDeRect(soloX, plat)) p = soloX;
        else if (dentroDeRect(soloY, plat)) p = soloY;
        else p = A.pos;
      }
    }

    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if ((c.cota || 0) + (c.altura || 0) <= (A.cota || 0) + 20) continue;
      if (dentroDePoligono(p, c.poli)) p = empujaFuera(p, c.poli, A.radio + 5);
    }

    if (!dentroDeRect(p, this.enc.arena.bounds)) {
      const soloX = { x: p.x, y: A.pos.y }, soloY = { x: A.pos.x, y: p.y };
      if (dentroDeRect(soloX, this.enc.arena.bounds)) p = soloX;
      else if (dentroDeRect(soloY, this.enc.arena.bounds)) p = soloY;
      else p = A.pos;
    }
    A.pos = p;
  }

  _separarAgentes() {
    const vivos = this.agentes.filter(a => a.estado !== ESTADOS.MUERTO);
    for (let i = 0; i < vivos.length; i++) {
      for (let j = i + 1; j < vivos.length; j++) {
        const a = vivos[i], b = vivos[j];
        if (Math.abs((a.cota || 0) - (b.cota || 0)) > 100) continue;
        const min = a.radio + b.radio;
        const d = dist(a.pos, b.pos);
        if (d >= min || d < 1e-3) continue;
        const empuje = escala(normaliza(resta(b.pos, a.pos)), (min - d) / 2);
        a.pos = resta(a.pos, empuje);
        b.pos = suma(b.pos, empuje);
      }
    }
    // Separar puede meter a alguien DENTRO de un muro: el empujon de arriba no
    // sabe nada de geometria. Sin este repaso, dos agentes apretandose contra un
    // pilar acababan dentro de el, y en la vista 3D se veia al personaje metido
    // en la caja. El solido gana siempre.
    for (const a of vivos) this._sacarDeSolidos(a);
  }

  _sacarDeSolidos(A) {
    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if ((c.cota || 0) + (c.altura || 0) <= (A.cota || 0) + 20) continue;
      if (dentroDePoligono(A.pos, c.poli)) A.pos = empujaFuera(A.pos, c.poli, A.radio + 5);
    }
  }

  // ------------------------------------------------------------------ apoyo

  _aLibre(A) { A.estado = ESTADOS.LIBRE; A.tEstado = 0; A.accion = null; }

  agente(id) { return this.agentes.find(a => a.id === id) || null; }

  enemigosVivos() { return this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO); }

  _enAlcance(A, O, alcance) {
    if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) return false;
    return dist(A.pos, O.pos) - O.radio <= alcance;
  }

  amenazaInminente(anticipacion = 0.25) {
    const M = this.malakh;
    for (const E of this.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.accion) continue;
      if (E.estado !== ESTADOS.ANTICIPACION) continue;
      const falta = E.accion.impacto - E.tEstado;
      if (falta < 0 || falta > anticipacion) continue;
      if (E.accion.proyectil) return { de: E, falta };
      if (dist(E.pos, M.pos) - M.radio <= E.accion.alcance * 1.15) return { de: E, falta };
    }
    for (const p of this.proyectiles) {
      if (p.bando === 'malakh') continue;
      const d = dist(p.pos, M.pos);
      if (d / p.velocidad <= anticipacion) return { de: this.agente(p.origenId), falta: d / p.velocidad, proyectil: p };
    }
    return null;
  }

  _evento(tipo, datos) {
    this.eventos.push({ t: +this.t.toFixed(3), tipo, ...datos });
  }

  _grabarFotograma() {
    const M = this.malakh;
    this.fotogramas.push({
      t: +this.t.toFixed(3),
      arma: M.temporal?.familia || null,
      offHand: M.offHand?.familia || null,
      municion: M.temporal?.municion ?? null,
      agentes: this.agentes.map(a => ({
        id: a.id, x: Math.round(a.pos.x), y: Math.round(a.pos.y),
        cota: a.cota, yaw: Math.round(a.yaw), hp: Math.round(a.hp),
        hpMax: a.hpMax,
        estado: a.bloqueando ? 'bloqueando' : a.estado,
        // Destello de impacto: dura un cuarto de segundo, lo justo para verse.
        golpeado: (this.t - (a.tUltimoGolpe ?? -99)) < 0.25,
        golpeBloqueado: !!a.ultimoGolpeBloqueado
      })),
      proyectiles: this.proyectiles.map(p => ({ x: Math.round(p.pos.x), y: Math.round(p.pos.y), bando: p.bando })),
      drops: this.drops.map(d => ({ x: Math.round(d.pos.x), y: Math.round(d.pos.y), familia: d.familia })),
      zonas: this.zonas.map(z => ({ x: Math.round(z.pos.x), y: Math.round(z.pos.y), radio: z.radio }))
    });
  }

  resultado() {
    const M = this.malakh;
    const bajas = this.eventos.filter(e => e.tipo === 'baja');
    const danoPorFuente = {};
    const danoPorArma = {};
    for (const ev of this.eventos) {
      if (ev.tipo !== 'golpe') continue;
      if (ev.a === 'malakh') {
        const f = this.agente(ev.de);
        const clave = f ? f.arquetipo : 'desconocido';
        danoPorFuente[clave] = (danoPorFuente[clave] || 0) + ev.dano;
      } else if (ev.de === 'malakh') {
        const clave = ev.arma || 'espada_base';
        danoPorArma[clave] = (danoPorArma[clave] || 0) + ev.dano;
      }
    }
    return {
      semilla: this.semilla,
      victoria: this.razonFin === 'victoria',
      razonFin: this.razonFin,
      tiempo: +this.t.toFixed(2),
      danoRecibido: +M.danoRecibido.toFixed(1),
      hpFinal: Math.max(0, +M.hp.toFixed(1)),
      pocionesBebidas: M.pocionesBebidas,
      golpesAsestados: M.golpesAsestados,
      golpesFallados: M.golpesFallados,
      esquivasLogradas: M.esquivasLogradas,
      enemigosVivos: this.enemigosVivos().length,
      ordenDeBajas: bajas.map(b => ({ id: b.agente, arquetipo: b.arquetipo, t: b.t })),
      armasRecogidas: M.armasRecogidas,
      descartesUsados: M.descartesUsados,
      maxDropsSimultaneos: this.maxDropsSimultaneos,
      danoPorFuente,
      danoPorArma,
      eventos: this.eventos,
      fotogramas: this.fotogramas
    };
  }
}
