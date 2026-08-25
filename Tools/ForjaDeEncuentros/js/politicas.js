// Politicas de Malakh. Aqui no juega un humano: juega una politica.
//
// La comparacion que importa (§5.2 del PDF) es entre dos de ellas:
//   "El mas cercano"  — espada sola, sin tocar el suelo. Es la puerta anti-soft-lock.
//   "Ruta de ventaja" — tu orden + recoge armas + las sacrifica cuando toca.
// Si la segunda no es mejor, la mecanica de armas temporales no esta pagando.
// Si la primera no gana, la arena incumple el §12.

import { dist, resta, normaliza } from './geometria.js';
import { ESTADOS } from './sim.js';
import { perfilAtaque, descarteDe } from './armas.js';
import { Azar } from './rng.js';

const RANGO_LARGO = ['arquero_del_firmamento'];
const RADIO_INTERES_DROP = 1100;   // cm que Malakh acepta desviarse por un arma

class PoliticaBase {
  constructor(id, nombre, descripcion, opciones = {}) {
    this.id = id;
    this.nombre = nombre;
    this.descripcion = descripcion;
    this.usaArmas = !!opciones.usaArmas;
    this.codicioso = !!opciones.codicioso;
  }

  iniciar(sim) {
    this.azar = new Azar(sim.semilla ^ 0x5f3759df);
    this.tUltimoAtaque = -99;
    this.ladoBaile = this.azar.probabilidad(0.5) ? 1 : -1;
  }

  elegirObjetivo(sim, M) { return this._masCercano(sim, M); }

  /**
   * El orden de bajas es una PREFERENCIA, no una obsesion.
   *
   * Un jugador que ha decidido "primero el lancero" no cruza la arena de espaldas
   * mientras dos escuderos le pegan: se quita de encima al que tiene delante y
   * luego sigue con el plan. Sin esta regla, las politicas con orden fijo se
   * suicidaban caminando y la comparacion del §5.2 no medía nada.
   */
  _objetivoEfectivo(sim, M, preferido) {
    if (!preferido) return preferido;
    const lejos = dist(preferido.pos, M.pos) > 500;
    const otraCota = Math.abs((preferido.cota || 0) - (M.cota || 0)) > 120;
    if (!lejos && !otraCota) return preferido;

    const encima = this._masCercano(sim, M, e =>
      e.arquetipo !== 'arquero_del_firmamento' &&
      Math.abs((e.cota || 0) - (M.cota || 0)) <= 120 &&
      dist(e.pos, M.pos) - M.radio <= e.perfil.alcanceAtaque * 1.4);
    return encima || preferido;
  }

  /**
   * El mas cercano de los que estan PELEANDO.
   *
   * Con oleadas (§6) quien no ha entrado todavia NO es un objetivo, y esto
   * importa mas de lo que parece: la primera version se caia a la lista entera
   * cuando no habia nadie activo, y en el hueco entre dos oleadas Malakh cruzaba
   * la arena a despertar al arquero de la torre de enfrente. Medido: moria el
   * 100% de las veces peleando contra los dos arqueros a la vez, que es
   * exactamente lo que escalonar existia para evitar.
   *
   * Un jugador en ese hueco bebe y espera. La red de seguridad —caer a la lista
   * entera— solo se tiende cuando ya han entrado TODAS las oleadas, que es el
   * unico caso en que esperar seria esperar para siempre.
   */
  _masCercano(sim, M, filtro = null) {
    const buscar = (lista) => {
      let mejor = null, mejorD = Infinity;
      for (const e of lista) {
        if (filtro && !filtro(e)) continue;
        const d = dist(e.pos, M.pos);
        if (d < mejorD) { mejorD = d; mejor = e; }
      }
      return mejor;
    };
    const activo = buscar(sim.enemigosActivos());
    if (activo) return activo;
    return sim.oleadasPendientes().length ? null : buscar(sim.enemigosVivos());
  }

  /** El primero del orden previsto que este peleando. */
  _delOrdenPrevisto(sim) {
    for (const id of sim.enc.ordenPrevisto || []) {
      const e = sim.agente(id);
      if (e && e.estado !== ESTADOS.MUERTO && e.activo) return e;
    }
    return null;
  }

  // ------------------------------------------------------------------ decidir

  /** El bloqueo que tengo ahora mismo: el del escudo si lo llevo, o el de la espada. */
  _bloqueoActual(sim, M) {
    return M.offHand
      ? sim.armas.familias[M.offHand.familia]?.bloqueo || sim.cal.malakh.bloqueo
      : sim.cal.malakh.bloqueo;
  }

  decidir(sim, M) {
    // 1. ¿Me viene un golpe encima? Esto va antes que nada.
    // A UNA FLECHA SE LE RUEDA, LLEVES ESCUDO O NO.
    //
    // Hubo una version que dejaba de rodar cuando llevabas escudo, y salia
    // mucho peor: los i-frames duran 0,35 s y cubren el trayecto entero, asi
    // que cambiar la esquiva por la guardia era regalar el 63% mas de daño. El
    // Escudo Celestial no sustituye a rodar — cubre lo que rodar no puede, que
    // son las flechas que entran mientras estas clavado en tu propia animacion,
    // y eso lo hace solo (`mitigacionEnCompromiso`), sin cambiar como se juega.
    const amenaza = sim.amenazaInminente(0.45);
    if (amenaza && M.stamina >= sim.cal.malakh.esquiva.costeStamina * 1.5) {
      const origen = amenaza.proyectil ? amenaza.proyectil : amenaza.de;
      const alejarse = normaliza(resta(M.pos, origen.pos));
      const lateral = { x: -alejarse.y, y: alejarse.x };
      const signo = this.azar.probabilidad(0.5) ? 1 : -1;
      return {
        accion: 'esquivar',
        direccion: normaliza({
          x: alejarse.x * 0.4 + lateral.x * signo,
          y: alejarse.y * 0.4 + lateral.y * signo
        }),
        objetivo: M.objetivoId
      };
    }

    let obj = sim.agente(M.objetivoId);
    if (!obj || obj.estado === ESTADOS.MUERTO || !obj.activo) obj = this.elegirObjetivo(sim, M);
    obj = this._objetivoEfectivo(sim, M, obj);
    // OJO al orden: sin objetivo se sigue pudiendo beber y recoger. El hueco
    // entre oleadas es JUSTO el momento de hacer las dos cosas, y si aqui se
    // saliera con `esperar` el jugador se quedaria mirando la pared con la
    // pocion en la mano y el escudo del vigilante en el suelo.

    // 2. ¿Toca beber? Con hueco, en cuanto baja del umbral. Sin hueco, solo
    //    cuando ya da igual: morir con cuatro frascos encima no lo hace nadie.
    const pocion = sim.cal.malakh.pocion;
    if (pocion && M.pociones > 0) {
      const margen = pocion.duracion * 1.15;
      const conHueco = M.hp < M.hpMax * pocion.umbralUso
        && this._huecoSeguro(sim, M, margen) && !sim.amenazaInminente(margen);
      const aLaDesesperada = M.hp < M.hpMax * 0.25 && !sim.amenazaInminente(0.35);
      // Con la arena en calma —lo que la activacion escalonada del §6 crea entre
      // oleada y oleada— se bebe aunque no estes en las ultimas. Sin esto Malakh
      // se moria con frascos encima: en mitad de la pelea nunca se abre un hueco
      // de 2,2 s, asi que gastaba 2 de 4.
      const enCalma = !sim.enemigos.some(E =>
        E.estado !== ESTADOS.MUERTO && E.activo && E.alertado);
      const respiro = enCalma
        && M.hp < M.hpMax * (pocion.umbralRespiro ?? pocion.umbralUso)
        && !sim.amenazaInminente(margen);
      if (conHueco || respiro || aLaDesesperada) return { accion: 'beber', objetivo: obj?.id };
    }

    // 3. Armas temporales: recoger o sacrificar.
    if (this.usaArmas) {
      const plan = this._planDeArma(sim, M, obj);
      if (plan) return plan;
    }

    // Sin nadie a quien pegar: la oleada siguiente todavia no ha entrado.
    if (!obj) return { accion: 'esperar' };

    const perfil = perfilAtaque(M, sim.cal, sim.armas, false);
    const pesado = perfilAtaque(M, sim.cal, sim.armas, true);
    const aturdido = obj.estado === ESTADOS.ATURDIDO;
    const usar = (aturdido && pesado !== perfil && M.stamina >= (pesado.costeStamina || 0) * 1.2)
      ? pesado : perfil;

    const mismaCota = Math.abs((obj.cota || 0) - (M.cota || 0)) <= 120;
    const enRango = mismaCota && dist(obj.pos, M.pos) - obj.radio <= usar.alcance;

    if (enRango) {
      // Un ataque es compromiso de animacion. Un jugador competente no lo gasta
      // mientras alguien le levanta el arma encima.
      const hueco = aturdido || this._huecoSeguro(sim, M, usar.duracion * 0.8);
      const forzar = sim.t - this.tUltimoAtaque > 3.0;
      if ((hueco || forzar) && M.stamina >= (usar.costeStamina || 0)) {
        this.tUltimoAtaque = sim.t;
        return { accion: usar.esPesado ? 'atacarPesado' : 'atacar', objetivo: obj.id };
      }
    }

    // 4. Espaciado. Si mi arma llega mas lejos que la suya, el sitio correcto es
    //    justo fuera de SU alcance, no pegado a el. Esto es lo que hace valiosa a
    //    la lanza (§4: "Alcance / control"), y sin ello el alcance no vale nada:
    //    Malakh se pegaba igual que con la espada y perdia toda la ventaja.
    const suAlcance = obj.perfil?.alcanceAtaque ?? 0;
    if (usar.alcance > suAlcance * 1.25 && !usar.proyectil) {
      const hueco = dist(obj.pos, M.pos) - obj.radio;
      if (hueco < suAlcance * 1.15) {
        return {
          accion: 'reposicionar',
          direccion: normaliza(resta(M.pos, obj.pos)),
          objetivo: obj.id
        };
      }
    }

    // AQUI HUBO UN "AVANZAR TRAS EL ESCUDO" Y SE QUITO, porque la medida lo
    // tumbo: cruzar bloqueando al 60% de velocidad daba +35% de daño y bajaba
    // la victoria del 80% al 13%. Atacaba el sintoma equivocado — las flechas
    // del trayecto ya se esquivan. Lo que el escudo cubre es otra cosa y lo
    // hace solo, sin pedirle al jugador que camine raro.

    // 5. Sin hueco. Con dos o tres encima no da tiempo a rodar de todos: guardia.
    const presion = this._focoDePresion(sim, M);
    const inminente = this._amenazaCuerpoACuerpo(sim, M, 0.8);
    if (!enRango && !inminente) return { accion: 'acercarse', objetivo: obj.id };

    const bloqueo = M.offHand
      ? sim.armas.familias[M.offHand.familia].bloqueo
      : sim.cal.malakh.bloqueo;
    if (inminente && M.stamina >= bloqueo.costeStaminaPorGolpe * 1.2) {
      return {
        accion: 'bloquear',
        mirarA: inminente.pos,
        direccion: presion ? normaliza(resta(M.pos, presion)) : null,
        objetivo: obj.id
      };
    }

    if (presion) {
      const fuera = normaliza(resta(M.pos, presion));
      const lateral = { x: -fuera.y, y: fuera.x };
      return {
        accion: 'reposicionar',
        direccion: normaliza({
          x: fuera.x * 0.5 + lateral.x * this.ladoBaile,
          y: fuera.y * 0.5 + lateral.y * this.ladoBaile
        }),
        objetivo: obj.id
      };
    }
    return { accion: 'acercarse', objetivo: obj.id };
  }

  // ------------------------------------------------------- armas temporales

  _planDeArma(sim, M, obj) {
    // 3a. ¿Merece la pena sacrificar lo que llevo? (§3.2)
    const d = obj ? descarteDe(M, sim.armas) : null;
    if (d && this._mereceDescarte(sim, M, obj, d)) {
      return { accion: 'descartar', objetivo: obj.id };
    }

    // 3b. ¿Hay algo en el suelo que mejore lo que llevo? (§4.1)
    const drop = this._mejorDrop(sim, M);
    if (!drop) return null;

    // Recoger son 0,7 s clavado. No se hace con alguien levantando el arma.
    const cerca = dist(M.pos, drop.pos) <= sim.armas.reglas.radioRecogida;
    const margen = sim.armas.reglas.duracionRecogida * 1.2;
    if (cerca && !this._huecoSeguro(sim, M, margen)) return null;

    return { accion: 'recoger', dropId: drop.id, objetivo: obj?.id };
  }

  _mejorDrop(sim, M) {
    let mejor = null, mejorGanancia = 0;
    const actual = this._valorDeArma(sim, M, M.temporal?.familia || null);

    for (const drop of sim.drops) {
      if (dist(M.pos, drop.pos) > RADIO_INTERES_DROP) continue;
      const fam = sim.armas.familias[drop.familia];
      if (!fam) continue;

      let ganancia;
      if (fam.esOffHand) {
        if (M.offHand) continue;
        ganancia = this._valorDeArma(sim, M, drop.familia);
        // Coger el escudo con algo a dos manos en la mano PURGA la principal
        // (§4.1, y lo hace `equipar`). Compensa solo si el escudo vale mas: es
        // la misma cuenta que al reves, y antes no se hacia — el escudo se
        // descartaba de plano y luego no habia forma de volver a el.
        if (M.temporal && sim.armas.familias[M.temporal.familia]?.dosManos) {
          ganancia -= this._valorDeArma(sim, M, M.temporal.familia);
        }
      } else {
        ganancia = this._valorDeArma(sim, M, drop.familia) - actual;
        // La regla del §4.1: un arma a dos manos OBLIGA a soltar el escudo. Eso
        // tiene precio, y no tenerlo en cuenta era el motivo de que Malakh
        // cambiara el Escudo Celestial por la lanza con dos arqueros en pie.
        if (sim.armas.familias[drop.familia]?.dosManos && M.offHand) {
          ganancia -= this._valorDeArma(sim, M, M.offHand.familia);
        }
        if (this.codicioso) ganancia = Math.max(ganancia, 0.1);   // el codicioso coge todo
      }

      if (ganancia <= mejorGanancia) continue;
      mejorGanancia = ganancia;
      mejor = drop;
    }
    return mejorGanancia > 0.4 ? mejor : null;
  }

  /**
   * Cuanto vale un arma AHORA, segun lo que queda vivo. No es un ranking fijo:
   * la lanza vale mucho con arqueros en pie y poco cuando solo quedan escuderos.
   */
  _valorDeArma(sim, M, familia) {
    const vivos = sim.enemigosVivos();
    if (!vivos.length) return 0;
    const lejanos = vivos.filter(e =>
      RANGO_LARGO.includes(e.arquetipo) || Math.abs((e.cota || 0) - (M.cota || 0)) > 120).length;
    const conGuardia = vivos.filter(e => (e.perfil.guardia || 0) > 0).length;

    switch (familia) {
      case null: return 1.0;                                   // espada base
      case 'lanza_del_alba': return 2.0 + lejanos * 0.8;
      case 'arco_del_firmamento': return 1.2 + lejanos * 1.6;
      case 'espadon_alabarda': return 2.0 + conGuardia * 1.0;
      case 'estandarte_ritual': return 1.4 + (vivos.length >= 3 ? 1.2 : 0);
      // El Escudo Celestial para flechas, asi que su valor lo fijan los arqueros
      // que sigan en pie. Antes caia en el `default` y valia 1.0 pasara lo que
      // pasara, con lo que cambiarlo por cualquier cosa a dos manos salia gratis.
      case 'escudo_celestial': return 1.5 + lejanos * 0.9;
      default: return 1.0;
    }
  }

  _mereceDescarte(sim, M, obj, d) {
    const vivos = sim.enemigosVivos();
    const dObj = dist(M.pos, obj.pos);

    switch (d.tipo) {
      case 'proyectil': {
        // Arrojar la lanza: solo contra quien no puedo alcanzar de otra forma,
        // o para rematar. Tirarla al que tengo pegado es tirarla a la basura.
        const inalcanzable = Math.abs((obj.cota || 0) - (M.cota || 0)) > 120;
        const lejos = dObj > 600 && dObj < (d.alcance || 2600);
        const remate = obj.hp <= d.dano;
        if (!(inalcanzable || lejos || remate)) return false;
        return sim.armas.familias[M.temporal?.familia]?.recurso?.tipo === 'municion'
          ? (M.temporal.municion <= 3)      // el arco: solo cuando ya casi no quedan flechas
          : true;
      }
      case 'aoe':
        return vivos.filter(e => dist(M.pos, e.pos) <= d.radio).length >= 2;
      case 'zona':
        return vivos.filter(e => dist(M.pos, e.pos) <= d.radio).length >= 2 && vivos.length >= 2;
      case 'impacto':
        // Shield bash de sacrificio: contra un escudero pegado, y solo si ya
        // tengo otra cosa en la mano o el escudo ha dejado de servir.
        return dObj - obj.radio <= (d.alcance || 240) && (obj.perfil.guardia || 0) > 0
            && vivos.length <= 2;
      default:
        return false;
    }
  }

  // ------------------------------------------------------------------ apoyo

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

// ---------------------------------------------------------------- las cinco

class Cercano extends PoliticaBase {
  constructor() {
    super('cercano', 'Espada · el mas cercano',
      'Espada sola, sin tocar nada del suelo. El jugador que no lee la arena. Es la linea base y la puerta anti-soft-lock del §7.3.');
  }
}

class Guionizada extends PoliticaBase {
  constructor() {
    super('guionizada', 'Espada · tu orden',
      'Espada sola siguiendo tu orden de bajas. Aisla cuanto aporta el ORDEN, sin contar las armas.');
  }
  elegirObjetivo(sim, M) {
    return this._delOrdenPrevisto(sim) || this._masCercano(sim, M);
  }
}

class Ventaja extends PoliticaBase {
  constructor() {
    super('ventaja', 'Ruta de ventaja',
      'Tu orden, recogiendo las armas que sueltan y sacrificandolas cuando compensa. Es la ruta que el PDF quiere que el jugador descubra.',
      { usaArmas: true });
  }
  elegirObjetivo(sim, M) {
    return this._delOrdenPrevisto(sim) || this._masCercano(sim, M);
  }
}

class CodiciosoArmas extends PoliticaBase {
  constructor() {
    super('codicioso', 'Codicioso',
      'Ataca al mas cercano y recoge todo lo que ve. El jugador que confunde "hay un arma" con "esta arma me sirve".',
      { usaArmas: true, codicioso: true });
  }
}

class Aleatoria extends PoliticaBase {
  constructor() {
    super('aleatoria', 'Orden al azar',
      'Espada sola, orden distinto por semilla. Dibuja el abanico real de jugadores, no el ideal.');
  }
  iniciar(sim) {
    super.iniciar(sim);
    this.cola = this.azar.barajar(sim.enemigos.map(e => e.id));
  }
  elegirObjetivo(sim, M) {
    for (const id of this.cola) {
      const e = sim.agente(id);
      if (e && e.estado !== ESTADOS.MUERTO && e.activo) return e;
    }
    return this._masCercano(sim, M);
  }
}

export function crearPoliticas() {
  return [new Cercano(), new Guionizada(), new Ventaja(), new CodiciosoArmas(), new Aleatoria()];
}

export function crearPolitica(id) {
  return crearPoliticas().find(p => p.id === id) || null;
}

/** La que hace de linea base para la prueba anti-soft-lock del §7.3. */
export const POLITICA_BASE = 'cercano';
/** La que representa la ruta que el diseñador cree haber puesto. */
export const POLITICA_VENTAJA = 'ventaja';
