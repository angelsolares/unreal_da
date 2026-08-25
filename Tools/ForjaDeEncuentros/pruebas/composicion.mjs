// Banco de composiciones: varias formas del mismo encuentro, comparadas en la
// misma tanda y ordenadas por lo que dice el veredicto.
//
//   node pruebas/composicion.mjs [encuentro]
//   PARTIDAS=1000 node pruebas/composicion.mjs
//
// Existe porque buscar a mano la composicion que pone las puertas en verde es
// abrir el editor, mover a uno, correr el lote, leer y repetir. Aqui se declaran
// juntas y se comparan con la misma semilla base, que es la unica forma de que
// la comparacion signifique algo.
//
// Las variantes de abajo son las que se midieron el 2026-08-25 para llegar a la
// receta actual, incluidas LAS QUE NO FUNCIONARON. Se quedan escritas a
// proposito: la lista de callejones sin salida vale tanto como la salida.

import { correrLote, PARTIDAS_POR_DEFECTO } from '../js/lote.js';
import { cal, armas, encuentro } from './cargar.mjs';

const base = encuentro(process.argv[2]);
const PARTIDAS = Number(process.env.PARTIDAS || PARTIDAS_POR_DEFECTO);
const copia = (e) => JSON.parse(JSON.stringify(e));

// ------------------------------------------------------------------ utilidades

const buscar = (enc, id) => {
  const e = enc.enemigos.find(n => n.id === id);
  if (!e) throw new Error(`no existe el enemigo ${id}`);
  return e;
};
const mover = (enc, id, x, y, cota) => {
  const e = buscar(enc, id);
  e.pos = { x, y };
  if (cota != null) e.cota = cota;
};
const drop = (enc, id, principal, secundaria) => {
  buscar(enc, id).drop = { principal: !!principal, secundaria: !!secundaria };
};
/** Redefine las oleadas: una lista de listas de ids, encadenadas por "la anterior limpia". */
const encadenar = (enc, grupos, retardo = 3) => {
  enc.oleadas = grupos.map((g, i) => ({
    id: `ola_${i + 1}`,
    nombre: g.nombre || `oleada ${i + 1}`,
    activacion: i === 0 ? { tipo: 'inicio' } : { tipo: 'oleadaLimpia', oleada: `ola_${i}` },
    retardo: i === 0 ? 0 : retardo,
    presencia: 'en-escena'
  }));
  grupos.forEach((g, i) => { for (const id of g.ids) buscar(enc, id).oleada = `ola_${i + 1}`; });
};
/** El balcon de un arquero, a medida. Su tamaño ES su dificultad. */
const balcon = (enc, id, { ancho, largo, centroY }) => {
  const p = enc.plataformas.find(q => q.id === id);
  if (!p) throw new Error(`no existe la plataforma ${id}`);
  p.min = { x: 1100, y: centroY - largo / 2 };
  p.max = { x: 1100 + ancho, y: centroY + largo / 2 };
  p.accesos = [{ desde: { x: 700, y: centroY }, hasta: { x: 1280, y: centroY }, ancho: 300 }];
};

// ------------------------------------------------------------------ variantes

const VARIANTES = [];
const variante = (nombre, porQue, fn) => VARIANTES.push({ nombre, porQue, fn });

variante('la receta actual', 'la que esta en el JSON', (e) => e);

variante('sin oleadas, los 5 de golpe',
  'lo que pasa si se exporta a un BP_DA_Arena que no sabe escalonar',
  (e) => { e.oleadas = []; for (const n of e.enemigos) n.oleada = null; });

variante('de uno en uno',
  'escalonar del todo: ¿hace falta que la primera sean dos?',
  (e) => encadenar(e, [
    { nombre: 'Lancero', ids: ['en_lancero'] },
    { nombre: 'Escudero', ids: ['en_escudero_a'] },
    { nombre: 'Balcon norte', ids: ['en_arquero_a'] },
    { nombre: 'Vigilante', ids: ['en_escudero_b'] },
    { nombre: 'Balcon sur', ids: ['en_arquero_b'] }]));

variante('los dos arqueros juntos',
  'la trampa que costo la tarde: DOS arqueros a la vez es una derrota segura',
  (e) => encadenar(e, [
    { nombre: 'La linea', ids: ['en_lancero', 'en_escudero_a'] },
    { nombre: 'El vigilante', ids: ['en_escudero_b'] },
    { nombre: 'Los dos balcones', ids: ['en_arquero_a', 'en_arquero_b'] }]));

variante('arquero emparejado con melé',
  'un arquero disparando mientras otro te sujeta: tampoco',
  (e) => encadenar(e, [
    { nombre: 'La linea', ids: ['en_lancero', 'en_escudero_a'] },
    { nombre: 'Balcon y vigilante', ids: ['en_arquero_a', 'en_escudero_b'] },
    { nombre: 'Balcon sur', ids: ['en_arquero_b'] }]));

variante('los dos balcones grandes',
  'si los dos arqueros son caros, la espada sola no llega',
  (e) => {
    balcon(e, 'plat_balcon_n', { ancho: 650, largo: 1000, centroY: -1000 });
    mover(e, 'en_arquero_a', 1600, -1250, 350);
  });

variante('los dos balcones pequeños',
  'y si los dos son baratos, el arsenal no pinta nada',
  (e) => {
    balcon(e, 'plat_balcon_s', { ancho: 350, largo: 450, centroY: 1000 });
    mover(e, 'en_arquero_b', 1300, 1113, 350);
  });

variante('con el escudo garantizado',
  'el drop que parece gratis y no lo es: con lanza o arco en la mano no se puede coger',
  (e) => { drop(e, 'en_escudero_a', false, true); drop(e, 'en_escudero_b', false, true); });

variante('sin la lanza',
  'cuanto de la ventaja es la lanza y cuanto el arco',
  (e) => drop(e, 'en_lancero', false, false));

variante('sin el arco',
  'idem, por el otro lado',
  (e) => drop(e, 'en_arquero_a', false, false));

// ------------------------------------------------------------------- informe

const MARCA = { ok: 'V', aviso: '~', fallo: 'X', na: '-' };
const filas = [];

for (const v of VARIANTES) {
  const enc = copia(base);
  const devuelto = v.fn(enc);
  const usado = devuelto || enc;
  const lote = correrLote(usado, cal, armas, { partidas: PARTIDAS });
  const ver = lote.veredicto;
  const cer = lote.porPolitica['cercano'].resumen;
  const gui = lote.porPolitica['guionizada'].resumen;
  const ven = lote.porPolitica['ventaja'].resumen;
  filas.push({
    nombre: v.nombre, porQue: v.porQue, veredicto: ver,
    fallos: ver.puertas.filter(p => p.estado === 'fallo').length,
    avisos: ver.puertas.filter(p => p.estado === 'aviso').length,
    puertas: ver.puertas.map(p => MARCA[p.estado]).join(''),
    espada: cer.tasaVictoria, ventaja: ven.tasaVictoria,
    hp: ven.hpFinalMedia, aLaVez: ven.maxEnemigosALaVez,
    dano: cer.danoMedio,
    ganaArmas: cer.danoMedio && ven.danoMedio ? (ven.danoMedio - cer.danoMedio) / cer.danoMedio : null,
    ganaOrden: cer.danoMedio && gui.danoMedio ? (gui.danoMedio - cer.danoMedio) / cer.danoMedio : null,
    atascos: Object.values(lote.porPolitica).reduce((a, p) => a + p.resumen.porTiempo, 0)
  });
}

const pct = (x) => (x == null ? '   —' : `${(x * 100).toFixed(0)}%`.padStart(5));

console.log(`\nEncuentro base: ${base.nombre} — ${base.enemigos.length} enemigos`);
console.log(`${PARTIDAS} partidas por politica y variante\n`);
console.log('   ' + 'variante'.padEnd(30) + 'puertas     esp%  vent%   hp  a la vez  armas  orden  atasc');
for (const f of filas.slice().sort((a, b) => a.fallos - b.fallos || a.avisos - b.avisos)) {
  console.log('   ' + f.nombre.padEnd(30) + f.puertas.padEnd(12) +
    pct(f.espada) + pct(f.ventaja) +
    `${String(f.hp ?? '—').padStart(6)}` +
    `${String(f.aLaVez).padStart(10)}` +
    pct(f.ganaArmas) + pct(f.ganaOrden) +
    `${String(f.atascos).padStart(7)}`);
}

console.log('\n   puertas: alcanzable · ganable · ventaja · cuesta · orden · drop · se-lee · saturar · watchdog');
console.log('   V verde · ~ aviso · X rojo · - sin datos');
console.log('   "armas" y "orden" son cuanto BAJA el daño recibido; cuanto mas negativo, mejor.\n');

const mejor = filas.slice().sort((a, b) => a.fallos - b.fallos || a.avisos - b.avisos)[0];
console.log(`--- detalle de "${mejor.nombre}" (${mejor.porQue}) ---`);
for (const g of mejor.veredicto.puertas) {
  console.log(`   [${MARCA[g.estado]}] ${g.titulo}`);
  console.log(`       ${g.texto}`);
}
