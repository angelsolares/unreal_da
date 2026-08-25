// Cuando una puerta se pone roja, un "no pasa" no sirve de nada. Lo que sirve es
// un numero: cuantos enemigos aguanta la espada hoy, y cuanto daño le falta para
// aguantar los que tu encuentro pide.
//
// El simulador cuesta ~3 ms por partida, asi que buscar la respuesta a fuerza
// bruta es mas barato que discutirla.

import { correrLote } from './lote.js';
import { encuentroVacio, nuevoEnemigo, podarOleadas } from './esquema.js';
import { POLITICA_BASE } from './politicas.js';

/**
 * 40 sondas eran pocas para un umbral del 90%: un encuentro que se gana el 94%
 * de verdad se cae por debajo del 90 en una muestra de 40 mas veces de las que
 * parece, y entonces la biseccion se pone a buscar el daño que haria falta para
 * arreglar algo que no esta roto. Es la misma leccion que la del veredicto.
 */
const PARTIDAS_SONDA = 150;
const UMBRAL = 0.90;

function clonar(o) { return JSON.parse(JSON.stringify(o)); }

function tasa(enc, cal, armas, partidas = PARTIDAS_SONDA) {
  const lote = correrLote(enc, cal, armas, { partidas });
  return lote.porPolitica[POLITICA_BASE].resumen.tasaVictoria;
}

/**
 * ¿Cuantos enemigos de esta composicion aguanta Malakh solo con espada?
 * Va añadiendo enemigos del encuentro, en el orden previsto, hasta que baja del 90%.
 */
export function techoDeLaEspada(encuentro, calibracion, armas) {
  const orden = ordenar(encuentro);
  const escalones = [];
  let techo = 0;

  for (let n = 1; n <= orden.length; n++) {
    const enc = clonar(encuentro);
    enc.enemigos = orden.slice(0, n).map(id => clonar(encuentro.enemigos.find(e => e.id === id)));
    enc.ordenPrevisto = (encuentro.ordenPrevisto || []).filter(id => enc.enemigos.some(e => e.id === id));
    // Sin esto, las oleadas que se quedan vacias se dan por limpias al instante
    // y los que quedan entran todos de golpe: se mediria otro encuentro.
    podarOleadas(enc);
    const t = tasa(enc, calibracion, armas);
    escalones.push({ n, tasa: t, ids: enc.enemigos.map(e => e.id) });
    if (t >= UMBRAL) techo = n;
  }

  return { techo, pedidos: encuentro.enemigos.length, escalones };
}

/**
 * Busca el daño por golpe que hace falta para que este encuentro pase la puerta.
 * Busqueda binaria sobre el daño total de Malakh (base + arma).
 */
export function danoNecesario(encuentro, calibracion, armas, maximo = 120) {
  const actual = calibracion.malakh.danoBase + calibracion.malakh.armaBase.dano;

  const conDano = (d) => {
    const cal = clonar(calibracion);
    cal.malakh.armaBase.dano = d - cal.malakh.danoBase;
    return cal;
  };

  if (tasa(encuentro, conDano(actual), armas) >= UMBRAL) {
    return { actual, necesario: actual, yaPasa: true };
  }
  if (tasa(encuentro, conDano(maximo), armas) < UMBRAL) {
    return { actual, necesario: null, yaPasa: false, techoBusqueda: maximo };
  }

  let lo = actual, hi = maximo;
  while (hi - lo > 2) {
    const medio = Math.round((lo + hi) / 2);
    if (tasa(encuentro, conDano(medio), armas) >= UMBRAL) hi = medio; else lo = medio;
  }
  return { actual, necesario: hi, yaPasa: false, factor: +(hi / actual).toFixed(2) };
}

/**
 * La otra palanca: bajar la vida de los enemigos en vez de subir el daño.
 * Devuelve el multiplicador de HP que hace pasar la puerta.
 */
export function vidaNecesaria(encuentro, calibracion, armas, minimo = 0.3) {
  const conFactor = (f) => {
    const cal = clonar(calibracion);
    for (const a of Object.values(cal.arquetipos)) a.hp = Math.round(a.hp * f);
    return cal;
  };
  if (tasa(encuentro, conFactor(1), armas) >= UMBRAL) return { factor: 1, yaPasa: true };
  if (tasa(encuentro, conFactor(minimo), armas) < UMBRAL) return { factor: null, yaPasa: false, sueloBusqueda: minimo };

  let lo = minimo, hi = 1;
  while (hi - lo > 0.04) {
    const medio = (lo + hi) / 2;
    if (tasa(encuentro, conFactor(medio), armas) >= UMBRAL) lo = medio; else hi = medio;
  }
  return { factor: +lo.toFixed(2), yaPasa: false };
}

/** Escalado generico con arquetipos sueltos, para saber donde esta el techo del sistema. */
export function techoDelSistema(calibracion, armas, arquetipo = 'escudero_celestial', maximo = 6) {
  const filas = [];
  for (let n = 1; n <= maximo; n++) {
    const enc = encuentroVacio('sonda');
    enc.jugador.pos = { x: -1200, y: 0 };
    enc.enemigos = Array.from({ length: n }, (_, i) => {
      const e = nuevoEnemigo(arquetipo, 300, (i - (n - 1) / 2) * 320);
      e.id = `s${i}`;
      return e;
    });
    filas.push({ n, tasa: tasa(enc, calibracion, armas) });
  }
  return filas;
}

function ordenar(encuentro) {
  const previsto = (encuentro.ordenPrevisto || []).filter(id => encuentro.enemigos.some(e => e.id === id));
  const resto = encuentro.enemigos.map(e => e.id).filter(id => !previsto.includes(id));
  return [...previsto, ...resto];
}
