// Politicas de Malakh. Aqui no juega un humano: juega una politica.
//
// Fase A: todas usan SOLO la espada base. Lo unico que cambia entre ellas es el
// ORDEN DE BAJAS. Eso ya basta para medir si el orden importa, que es la mitad
// de la pregunta del §5 del PDF. La otra mitad (¿la lanza acorta la pelea?)
// necesita la Fase B.

import { dist, resta, normaliza, escala } from './geometria.js';
import { ESTADOS } from './sim.js';
import { Azar } from './rng.js';

const RANGO_LARGO = ['arquero_del_firmamento'];

/** Comportamiento de combate comun. Solo cambia `elegirObjetivo`. */
class PoliticaBase {
  constructor(id, nombre, descripcion) {
    this.id = id;
    this.nombre = nombre;
    this.descripcion = descripcion;
  }

  iniciar(sim) {
    this.azar = new Azar(sim.semilla ^ 0x5f3759df);
    this.tUltimoAtaque = -99;
    this.ladoBaile = this.azar.probabilidad(0.5) ? 1 : -1;
  }

  elegirObjetivo(sim, M) {
    return this._masCercano(sim, M);
  }

  _masCercano(sim, M, filtro = null) {
    let mejor = null, mejorD = Infinity;
    for (const e of sim.enemigosVivos()) {
      if (filtro && !filtro(e)) continue;
      const d = dist(e.pos, M.pos);
      if (d < mejorD) { mejorD = d; mejor = e; }
    }
    return mejor;
  }

  decidir(sim, M) {
    // 1. ¿Me viene un golpe encima? Esto va antes que nada.
    const amenaza = sim.amenazaInminente(0.45);
    if (amenaza && M.stamina >= sim.cal.malakh.esquiva.costeStamina * 1.5) {
      const origen = amenaza.proyectil ? amenaza.proyectil : amenaza.de;
      const alejarse = normaliza(resta(M.pos, origen.pos));
      // esquivar de lado, no hacia atras: es lo que hace un jugador que sabe
      const lateral = { x: -alejarse.y, y: alejarse.x };
      const signo = this.azar.probabilidad(0.5) ? 1 : -1;
      const dir = normaliza({
        x: alejarse.x * 0.4 + lateral.x * signo,
        y: alejarse.y * 0.4 + lateral.y * signo
      });
      return { accion: 'esquivar', direccion: dir, objetivo: M.objetivoId };
    }

    // 2. Objetivo: se mantiene mientras siga vivo, para no bailar entre enemigos
    let obj = sim.agente(M.objetivoId);
    if (!obj || obj.estado === ESTADOS.MUERTO) obj = this.elegirObjetivo(sim, M);
    if (!obj) return { accion: 'esperar' };

    // 2b. ¿Toca beber? Solo con hueco de sobra: un frasco interrumpido es un frasco perdido.
    const pocion = sim.cal.malakh.pocion;
    if (pocion && M.pociones > 0 && M.hp < M.hpMax * pocion.umbralUso) {
      const margen = pocion.duracion * 1.15;
      if (this._huecoSeguro(sim, M, margen) && !sim.amenazaInminente(margen)) {
        return { accion: 'beber', objetivo: M.objetivoId };
      }
    }

    const ligero = sim.cal.malakh.ataqueLigero;
    const pesado = sim.cal.malakh.ataquePesado;
    const aturdido = obj.estado === ESTADOS.ATURDIDO;
    const perfil = aturdido && M.stamina >= pesado.costeStamina * 1.2 ? pesado : ligero;

    // 3. ¿Estoy a tiro? Si no, no hay decision que tomar: hay que andar.
    //    (Y sobre todo: no marcar "he atacado" cuando en realidad solo he caminado,
    //     o la valvula de abajo se reinicia sola y Malakh no ataca nunca.)
    const mismaCota = Math.abs((obj.cota || 0) - (M.cota || 0)) <= 120;
    const enRango = mismaCota && dist(obj.pos, M.pos) - obj.radio <= perfil.alcance;

    if (enRango) {
      // ¿Hay hueco para comprometerse? Un ataque son 1,5 s sin poder esquivar.
      // Un jugador competente no los gasta mientras alguien le levanta el arma encima.
      // Eso, y no el DPS, es lo que separa "ganable" de "imposible" en un souls.
      const hueco = aturdido || this._huecoSeguro(sim, M, perfil.duracion * 0.8);
      const forzar = sim.t - this.tUltimoAtaque > 3.0;   // valvula: nadie baila eternamente

      if ((hueco || forzar) && M.stamina >= perfil.costeStamina) {
        this.tUltimoAtaque = sim.t;
        return { accion: aturdido && perfil === pesado ? 'atacarPesado' : 'atacar', objetivo: obj.id };
      }
    }

    // 4. Sin hueco. Antes de rodear: ¿me va a caer algo que no puedo esquivar?
    //    Con dos o tres encima no da tiempo a rodar de todos; ahi se levanta la guardia.
    const presion = this._focoDePresion(sim, M);
    const bloqueo = sim.cal.malakh.bloqueo;
    const inminente = this._amenazaCuerpoACuerpo(sim, M, 0.8);

    if (!enRango && !inminente) return { accion: 'acercarse', objetivo: obj.id };

    if (inminente && M.stamina >= bloqueo.costeStaminaPorGolpe * 1.2) {
      const dir = presion ? normaliza(resta(M.pos, presion)) : null;
      return { accion: 'bloquear', mirarA: inminente.pos, direccion: dir, objetivo: obj.id };
    }

    if (presion) {
      const fuera = normaliza(resta(M.pos, presion));
      const lateral = { x: -fuera.y, y: fuera.x };
      const dir = normaliza({
        x: fuera.x * 0.5 + lateral.x * this.ladoBaile,
        y: fuera.y * 0.5 + lateral.y * this.ladoBaile
      });
      return { accion: 'reposicionar', direccion: dir, objetivo: obj.id };
    }

    return { accion: 'acercarse', objetivo: obj.id };
  }

  /** El enemigo cuerpo a cuerpo cuyo golpe llega antes, si llega dentro de `ventana`. */
  _amenazaCuerpoACuerpo(sim, M, ventana) {
    let mejor = null, mejorT = Infinity;
    for (const E of sim.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.alertado) continue;
      if (E.estado === ESTADOS.ATURDIDO) continue;
      if (E.arquetipo === 'arquero_del_firmamento') continue;
      const t = this._cuandoGolpea(E, M);
      if (t < mejorT) { mejorT = t; mejor = E; }
    }
    return mejorT <= ventana ? mejor : null;
  }

  /**
   * ¿Puedo comprometer `duracion` segundos sin comerme un golpe?
   * Los arqueros no cuentan: sus flechas se esquivan, no frenan un combo cuerpo a cuerpo.
   */
  _huecoSeguro(sim, M, duracion) {
    for (const E of sim.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.alertado) continue;
      if (E.estado === ESTADOS.ATURDIDO) continue;
      if (E.arquetipo === 'arquero_del_firmamento') continue;
      if (this._cuandoGolpea(E, M) < duracion) return false;
    }
    return true;
  }

  /**
   * Segundos que le faltan a `E` para meter su proximo golpe, contando lo que
   * tarda en CERRAR la distancia. Sin esa parte, un enemigo parado a cinco metros
   * bloqueaba todos los ataques de Malakh y la pelea se volvia infinita.
   */
  _cuandoGolpea(E, M) {
    const p = E.perfil;
    if (E.estado === ESTADOS.ACTIVO) return 0;
    if (E.estado === ESTADOS.ANTICIPACION && E.accion) {
      return Math.max(0, E.accion.impacto - E.tEstado);
    }
    const d = dist(E.pos, M.pos) - M.radio;
    const cierre = Math.max(0, (d - p.alcanceAtaque * 0.95) / Math.max(1, p.velocidad));
    let listo = E.recarga;
    if (E.estado === ESTADOS.RECUPERACION && E.accion) {
      listo = Math.max(0, E.accion.duracion - E.tEstado) + p.recarga;
    }
    return Math.max(listo, cierre) + p.ataque.impacto;
  }

  /** Centro de la presion cuerpo a cuerpo, para saber de que hay que salirse. */
  _focoDePresion(sim, M) {
    let sx = 0, sy = 0, n = 0;
    for (const E of sim.enemigos) {
      if (E.estado === ESTADOS.MUERTO || !E.alertado) continue;
      if (E.arquetipo === 'arquero_del_firmamento') continue;
      if (dist(E.pos, M.pos) - M.radio > E.perfil.alcanceAtaque * 1.6) continue;
      sx += E.pos.x; sy += E.pos.y; n += 1;
    }
    return n ? { x: sx / n, y: sy / n } : null;
  }
}

class Guionizada extends PoliticaBase {
  constructor() {
    super('guionizada', 'Ruta guionizada',
      'Sigue el orden de bajas que has marcado en el encuentro. Es la ruta que crees haber diseñado.');
  }
  elegirObjetivo(sim, M) {
    for (const id of sim.enc.ordenPrevisto || []) {
      const e = sim.agente(id);
      if (e && e.estado !== ESTADOS.MUERTO) return e;
    }
    return this._masCercano(sim, M);
  }
}

class Cercano extends PoliticaBase {
  constructor() {
    super('cercano', 'El mas cercano',
      'Ataca siempre a quien tenga delante. Es el jugador que no lee la arena: la linea base contra la que se mide todo.');
  }
}

class ArquerosPrimero extends PoliticaBase {
  constructor() {
    super('arqueros-primero', 'Arqueros primero',
      'Corre a por lo que castiga a distancia. Suele ser la lectura obvia; conviene saber si es la buena.');
  }
  elegirObjetivo(sim, M) {
    return this._masCercano(sim, M, e => RANGO_LARGO.includes(e.arquetipo))
        || this._masCercano(sim, M);
  }
}

class Aleatoria extends PoliticaBase {
  constructor() {
    super('aleatoria', 'Orden al azar',
      'Un orden distinto por semilla. Dibuja el abanico real de jugadores, no el ideal.');
  }
  iniciar(sim) {
    super.iniciar(sim);
    this.cola = this.azar.barajar(sim.enemigos.map(e => e.id));
  }
  elegirObjetivo(sim, M) {
    for (const id of this.cola) {
      const e = sim.agente(id);
      if (e && e.estado !== ESTADOS.MUERTO) return e;
    }
    return this._masCercano(sim, M);
  }
}

export function crearPoliticas() {
  return [new Guionizada(), new Cercano(), new ArquerosPrimero(), new Aleatoria()];
}

/** La politica que hace de linea base para la prueba anti-soft-lock del §7.3. */
export const POLITICA_BASE = 'cercano';
