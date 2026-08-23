// Simulador determinista del encuentro.
//
// Reglas de la casa:
//  - Nada de Math.random: todo sale del Azar sembrado, o el lote de 200 partidas
//    no compara politicas, compara ruido.
//  - Nada de render aqui dentro: esto tiene que poder correr 200 veces sin pintar.
//  - Todo numero de balance viene de calibracion.json, nunca escrito a pelo.

import { Azar } from './rng.js';
import {
  dist, resta, suma, escala, normaliza, largo, yawDe, giraHacia, deltaAngulo,
  dentroDePoligono, hayVision, empujaFuera, segmentoCortaPoligono, centroide
} from './geometria.js';

export const ESTADOS = {
  LIBRE: 'libre',
  ANTICIPACION: 'anticipacion',
  ACTIVO: 'activo',
  RECUPERACION: 'recuperacion',
  ESQUIVA: 'esquiva',
  CURANDO: 'curando',
  ATURDIDO: 'aturdido',
  MUERTO: 'muerto'
};

const AGUANTE_POR_DEFECTO = { arquero_del_firmamento: 20, elite_pesado: 120 };
const REGEN_AGUANTE = 20;
const RADIO_ALERTA_ALIADOS = 900;

export class Simulacion {
  constructor(encuentro, calibracion, politica, semilla, opciones = {}) {
    this.enc = encuentro;
    this.cal = calibracion;
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
    this.eventos = [];
    this.fotogramas = [];
    this.terminada = false;
    this.razonFin = null;

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
      pos: { ...this.enc.arena.entrada },
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
      pociones: m.pocion ? m.pocion.cantidad : 0,
      pocionesBebidas: 0,
      curacionTotal: 0,
      danoRecibido: 0,
      golpesAsestados: 0,
      golpesFallados: 0,
      esquivasLogradas: 0
    };
    // mirar hacia el centro de la arena
    this.malakh.yaw = yawDe(resta(centroide(this.enc.arena.bounds), this.malakh.pos));

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
        recarga: this.azar.rango(0, p.recarga * 0.5), // desincronizar el primer ataque
        alertado: false,
        perfil: p,
        danoInfligido: 0,
        tMuerte: null
      };
    });

    this.agentes = [this.malakh, ...this.enemigos];
    this.coberturas = this.enc.coberturas || [];
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
    } else if (this.t >= this.tiempoLimite) {
      this.terminada = true; this.razonFin = 'tiempo';
      this._evento('derrota', { motivo: `Se agoto el limite de ${this.tiempoLimite}s`, vivos: vivos.length });
    }
  }

  // ------------------------------------------------------------------- Malakh

  _pasoMalakh(dt) {
    const M = this.malakh;
    if (M.estado === ESTADOS.MUERTO) return;

    M.bloqueando = false;   // se sostiene tick a tick; si la politica no lo pide, baja la guardia
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

    if (M.estado === ESTADOS.ESQUIVA) {
      const a = M.accion;
      const avance = (a.distancia / a.duracion) * dt;
      this._mover(M, escala(a.dir, avance));
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

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      M.yaw = giraHacia(M.yaw, yawDe(resta(obj.pos, M.pos)), M.perfil.velocidadGiro * dt);
    }

    if (intencion.accion === 'beber' && M.pociones > 0) {
      const p = this.cal.malakh.pocion;
      M.pociones -= 1;
      M.pocionesBebidas += 1;
      M.estado = ESTADOS.CURANDO;
      M.tEstado = 0;
      // El frasco se gasta al empezar: si te interrumpen, lo has perdido.
      M.accion = { duracion: p.duracion, curacion: p.curacion };
      this._evento('bebe', { agente: M.id, restantes: M.pociones });
      return;
    }

    if (intencion.accion === 'bloquear') {
      M.bloqueando = true;
      // De cara a la amenaza, no al objetivo: bloquear de espaldas no sirve de nada.
      if (intencion.mirarA) {
        M.yaw = giraHacia(M.yaw, yawDe(resta(intencion.mirarA, M.pos)), M.perfil.velocidadGiro * dt);
      }
      if (intencion.direccion) {
        const f = this.cal.malakh.bloqueo.factorVelocidad;
        this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * f * dt));
      }
      return;
    }

    if (intencion.accion === 'reposicionar' && intencion.direccion) {
      // Rodear sin perder de vista al objetivo: el yaw ya se giro arriba.
      this._mover(M, escala(normaliza(intencion.direccion), M.perfil.velocidad * dt));
      return;
    }

    if (intencion.accion === 'atacar' || intencion.accion === 'atacarPesado') {
      const perfil = intencion.accion === 'atacarPesado'
        ? this.cal.malakh.ataquePesado : this.cal.malakh.ataqueLigero;
      if (obj && this._enAlcance(M, obj, perfil.alcance) && M.stamina >= perfil.costeStamina) {
        this._iniciarAtaque(M, perfil, intencion.accion === 'atacarPesado');
        return;
      }
    }

    if (obj && obj.estado !== ESTADOS.MUERTO) {
      this._avanzarHacia(M, obj, this.cal.malakh.ataqueLigero.alcance * 0.7, dt);
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

    // aggro
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
      if (dist(otro.pos, E.pos) <= RADIO_ALERTA_ALIADOS) { otro.alertado = true; }
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

    if (d < p.distanciaMinima) {           // demasiado cerca: retroceder
      const huida = normaliza(resta(E.pos, M.pos));
      this._mover(E, escala(huida, p.velocidad * dt));
      return;
    }
    if (!ve) {                              // sin linea: reposicionar lateralmente
      const hacia = normaliza(resta(M.pos, E.pos));
      const lateral = { x: -hacia.y, y: hacia.x };
      this._mover(E, escala(lateral, p.velocidad * 0.6 * dt));
      return;
    }
    if (d > p.alcanceAtaque) {
      this._avanzarHacia(E, M, p.distanciaPreferida, dt);
      return;
    }
    if (E.recarga <= 0) {
      this._iniciarAtaque(E, { ...p.ataque, alcance: p.alcanceAtaque, dano: p.dano, proyectil: true });
    }
  }

  // ---------------------------------------------------------------- ataques

  _iniciarAtaque(A, perfil, esPesado = false) {
    A.estado = ESTADOS.ANTICIPACION;
    A.tEstado = 0;
    A.accion = {
      ...perfil,
      esPesado,
      yaGolpeo: false,
      dano: perfil.dano ?? (this.cal.malakh.danoBase + this.cal.malakh.armaBase.dano) *
            (esPesado ? (this.cal.malakh.ataquePesado.multiplicadorDano || 1) : 1)
    };
    if (A.bando === 'malakh') A.stamina -= perfil.costeStamina || 0;
    this._evento('ataque', { agente: A.id, pesado: esPesado, objetivo: A.objetivoId || 'malakh' });
  }

  _avanzarAtaque(A, dt) {
    const a = A.accion;
    const t = A.tEstado;
    const iniVentana = a.impacto;
    const finVentana = a.impacto + a.ventana;

    if (t < iniVentana) A.estado = ESTADOS.ANTICIPACION;
    else if (t <= finVentana) A.estado = ESTADOS.ACTIVO;
    else A.estado = ESTADOS.RECUPERACION;

    if (A.estado === ESTADOS.ACTIVO && !a.yaGolpeo) {
      a.yaGolpeo = true;
      if (a.proyectil) this._lanzarProyectil(A, a);
      else this._resolverGolpeCuerpoACuerpo(A, a);
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
      if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) continue;   // no se llega a otra cota
      const d = dist(A.pos, O.pos) - O.radio;
      if (d > a.alcance) continue;
      const ang = Math.abs(deltaAngulo(A.yaw, yawDe(resta(O.pos, A.pos))));
      if (ang > (a.arco || 90) / 2) continue;
      this._aplicarDano(O, a.dano, A, a.esPesado);
      alcanzado = true;
      if (A.bando === 'malakh') break;   // un objetivo por golpe: nada de barridos gratis
    }
    if (A.bando === 'malakh') {
      if (alcanzado) A.golpesAsestados += 1; else A.golpesFallados += 1;
    }
  }

  _lanzarProyectil(A, a) {
    const M = this.malakh;
    const dir = normaliza(resta(M.pos, A.pos));
    this.proyectiles.push({
      pos: { ...A.pos },
      cota: A.cota,
      dir,
      velocidad: A.perfil.velocidadProyectil,
      dano: a.dano,
      origenId: A.id,
      vida: 3.0
    });
    this._evento('disparo', { agente: A.id });
  }

  _pasoProyectiles(dt) {
    const M = this.malakh;
    const vivos = [];
    for (const p of this.proyectiles) {
      const antes = { ...p.pos };
      p.pos = suma(p.pos, escala(p.dir, p.velocidad * dt));
      p.vida -= dt;

      // ¿lo para una cobertura?
      let parado = false;
      for (const c of this.coberturas) {
        if (!c.bloqueaVision) continue;
        const cima = (c.cota || 0) + (c.altura || 0);
        if (cima <= Math.max(p.cota, M.cota) + this.cal.malakh.alturaOjos - 10) continue;
        if (segmentoCortaPoligono(antes, p.pos, c.poli)) { parado = true; break; }
      }
      if (parado) { this._evento('proyectilParado', { origen: p.origenId }); continue; }

      if (M.estado !== ESTADOS.MUERTO && dist(p.pos, M.pos) <= M.radio + 15) {
        this._aplicarDano(M, p.dano, this.agente(p.origenId), false);
        continue;
      }
      if (p.vida > 0) vivos.push(p);
    }
    this.proyectiles = vivos;
  }

  _aplicarDano(O, cantidad, origen, esPesado) {
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

    // Guardia de Malakh: frontal, cuesta stamina, y si no queda se rompe.
    if (O.bando === 'malakh' && O.bloqueando && origen) {
      const b = this.cal.malakh.bloqueo;
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < b.arco / 2;
      if (frontal) {
        if (O.stamina >= b.costeStaminaPorGolpe) {
          O.stamina -= b.costeStaminaPorGolpe;
          dano *= 1 - b.reduccion;
          bloqueado = true;
        } else {
          // guard break: pasa el golpe entero y ademas te tumba
          O.stamina = 0;
          O.aguante = 0;
          this._evento('guardiaRota', { agente: O.id, de: origen.id });
        }
      }
    }

    const guardia = O.perfil?.guardia || 0;
    if (guardia > 0 && origen) {
      const frontal = Math.abs(deltaAngulo(O.yaw, yawDe(resta(origen.pos, O.pos)))) < 70;
      if (frontal && this.azar.probabilidad(guardia)) {
        dano *= 1 - (O.perfil.reduccionGuardia ?? 0.75);
        bloqueado = true;
      }
    }

    const factor = this.cal.reglas.factorArmadura || 0;
    if (factor > 0) dano = Math.max(1, dano - factor);

    O.hp -= dano;
    if (O.bando === 'malakh') O.danoRecibido += dano;
    if (origen && origen.bando === 'enemigo') origen.danoInfligido += dano;

    this._evento('golpe', {
      de: origen?.id, a: O.id, dano: +dano.toFixed(1), bloqueado, pesado: !!esPesado, hpRestante: Math.max(0, +O.hp.toFixed(1))
    });

    // aguante -> stagger
    if (!bloqueado) {
      O.aguante -= dano * (esPesado ? 2 : 1);
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
      }
    }
  }

  // -------------------------------------------------------------- movimiento

  /**
   * Camina hacia `objetivo` parandose a `distanciaParada`.
   * Si hay cobertura de por medio, rodea por el vertice mas barato en vez de
   * empotrarse: no es pathfinding de verdad, pero no miente sobre la geometria.
   */
  _avanzarHacia(A, objetivo, distanciaParada, dt) {
    const ruta = this._rutaHacia(A, objetivo);
    const destino = ruta.punto;
    // A un punto de paso se llega del todo. La distancia de parada es solo para
    // el objetivo final: aplicarla al waypoint dejaba a Malakh clavado a 1,7 m
    // de la rampa, mirando al arquero del balcon sin poder subir jamas.
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
    const paso = (A.perfil.velocidad || 400) * dt;
    A.yaw = giraHacia(A.yaw, yawDe(dir), (A.perfil.velocidadGiro || 360) * dt);
    this._mover(A, escala(dir, paso));
  }

  /**
   * Ruta hasta el objetivo. Si esta en otra cota, el primer tramo es el acceso
   * de su plataforma; al pisarlo, el agente cambia de cota.
   * Devuelve {punto, intermedio}.
   */
  _rutaHacia(A, objetivo) {
    const dCota = (objetivo.cota || 0) - (A.cota || 0);
    if (Math.abs(dCota) <= 50) return { punto: objetivo.pos, intermedio: false };

    // Sube: acceso de la plataforma del objetivo. Baja: acceso de la propia.
    const plat = dCota > 0
      ? this.plataformas.find(p => dentroDePoligono(objetivo.pos, p.poli))
      : this.plataformas.find(p => dentroDePoligono(A.pos, p.poli));
    if (!plat || !plat.accesos || !plat.accesos.length) {
      return { punto: objetivo.pos, intermedio: false };   // sin acceso: inalcanzable, ya lo canta validar()
    }

    let mejor = plat.accesos[0], mejorD = Infinity;
    for (const ac of plat.accesos) {
      const d = dist(A.pos, ac);
      if (d < mejorD) { mejorD = d; mejor = ac; }
    }
    if (mejorD < 120) {
      A.cota = dCota > 0 ? plat.cota : 0;
      return { punto: objetivo.pos, intermedio: false };
    }
    return { punto: mejor, intermedio: true };
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

    // Quien esta en alto se queda en alto: un balcon tiene barandilla. Sin esto,
    // el arquero huia hacia atras, se salia de la plataforma conservando su cota
    // y quedaba flotando fuera del alcance de nadie — la arena no se cerraba jamas.
    if ((A.cota || 0) > 50) {
      const plat = this.plataformas.find(pl =>
        Math.abs((pl.cota || 0) - A.cota) <= 50 && dentroDePoligono(A.pos, pl.poli));
      if (plat && !dentroDePoligono(p, plat.poli)) {
        const soloX = { x: p.x, y: A.pos.y };
        const soloY = { x: A.pos.x, y: p.y };
        if (dentroDePoligono(soloX, plat.poli)) p = soloX;
        else if (dentroDePoligono(soloY, plat.poli)) p = soloY;
        else p = A.pos;
      }
    }

    for (const c of this.coberturas) {
      if (!c.bloqueaPaso) continue;
      if ((c.cota || 0) + (c.altura || 0) <= (A.cota || 0) + 20) continue;  // se camina por encima
      if (dentroDePoligono(p, c.poli)) p = empujaFuera(p, c.poli, A.radio + 5);
    }
    if (this.enc.arena.bounds.length >= 3 && !dentroDePoligono(p, this.enc.arena.bounds)) {
      // El sello: nadie sale de la arena. Deslizar contra el borde en vez de frenar en seco,
      // que es lo que hace un Blocking Volume de verdad.
      const soloX = { x: p.x, y: A.pos.y };
      const soloY = { x: A.pos.x, y: p.y };
      if (dentroDePoligono(soloX, this.enc.arena.bounds)) p = soloX;
      else if (dentroDePoligono(soloY, this.enc.arena.bounds)) p = soloY;
      else p = A.pos;
    }
    A.pos = p;
  }

  /** Separacion barata para que no se solapen las capsulas. */
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
  }

  // ------------------------------------------------------------------ apoyo

  _aLibre(A) { A.estado = ESTADOS.LIBRE; A.tEstado = 0; A.accion = null; }

  agente(id) { return this.agentes.find(a => a.id === id) || null; }

  enemigosVivos() { return this.enemigos.filter(e => e.estado !== ESTADOS.MUERTO); }

  _enAlcance(A, O, alcance) {
    if (Math.abs((O.cota || 0) - (A.cota || 0)) > 120) return false;
    return dist(A.pos, O.pos) - O.radio <= alcance;
  }

  /** ¿Hay un ataque enemigo a punto de aterrizar sobre Malakh? Lo usa la politica. */
  amenazaInminente(anticipacion = 0.25) {
    const M = this.malakh;
    for (const E of this.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.accion) continue;
      if (E.estado !== ESTADOS.ANTICIPACION) continue;
      const falta = E.accion.impacto - E.tEstado;
      if (falta < 0 || falta > anticipacion) continue;
      if (E.accion.proyectil) return { de: E, falta };
      const d = dist(E.pos, M.pos) - M.radio;
      if (d <= E.accion.alcance * 1.15) return { de: E, falta };
    }
    for (const p of this.proyectiles) {
      const d = dist(p.pos, M.pos);
      if (d / p.velocidad <= anticipacion) return { de: this.agente(p.origenId), falta: d / p.velocidad, proyectil: p };
    }
    return null;
  }

  _evento(tipo, datos) {
    this.eventos.push({ t: +this.t.toFixed(3), tipo, ...datos });
  }

  _grabarFotograma() {
    this.fotogramas.push({
      t: +this.t.toFixed(3),
      agentes: this.agentes.map(a => ({
        id: a.id, x: Math.round(a.pos.x), y: Math.round(a.pos.y),
        cota: a.cota, yaw: Math.round(a.yaw), hp: Math.round(a.hp),
        estado: a.estado
      })),
      proyectiles: this.proyectiles.map(p => ({ x: Math.round(p.pos.x), y: Math.round(p.pos.y) }))
    });
  }

  resultado() {
    const bajas = this.eventos.filter(e => e.tipo === 'baja');
    const danoPorFuente = {};
    for (const ev of this.eventos) {
      if (ev.tipo !== 'golpe' || ev.a !== 'malakh') continue;
      const f = this.agente(ev.de);
      const clave = f ? f.arquetipo : 'desconocido';
      danoPorFuente[clave] = (danoPorFuente[clave] || 0) + ev.dano;
    }
    return {
      semilla: this.semilla,
      victoria: this.razonFin === 'victoria',
      razonFin: this.razonFin,
      tiempo: +this.t.toFixed(2),
      danoRecibido: +this.malakh.danoRecibido.toFixed(1),
      hpFinal: Math.max(0, +this.malakh.hp.toFixed(1)),
      golpesAsestados: this.malakh.golpesAsestados,
      golpesFallados: this.malakh.golpesFallados,
      esquivasLogradas: this.malakh.esquivasLogradas,
      enemigosVivos: this.enemigosVivos().length,
      ordenDeBajas: bajas.map(b => ({ id: b.agente, arquetipo: b.arquetipo, t: b.t })),
      danoPorFuente,
      eventos: this.eventos,
      fotogramas: this.fotogramas
    };
  }
}
