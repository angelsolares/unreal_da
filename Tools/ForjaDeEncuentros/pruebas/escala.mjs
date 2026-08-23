// ¿Cuantos enemigos aguanta Malakh solo con espada, y cuanto cambia con armas?
// Es la prueba de cordura del simulador: si no gana ni un 1-contra-1, el roto
// es el modelo. Si gana el 1v1 y pierde el 1v5, el roto es el balance.
//   node pruebas/escala.mjs

import { correrLote } from '../js/lote.js';
import { encuentroVacio, nuevoEnemigo } from '../js/esquema.js';
import { cal, armas } from './cargar.mjs';

function arenaCon(arquetipos) {
  const enc = encuentroVacio('escala');
  enc.arena.entrada = { x: -1200, y: 0 };
  enc.enemigos = arquetipos.map((a, i) => {
    const e = nuevoEnemigo(a, 300, (i - (arquetipos.length - 1) / 2) * 320);
    e.id = `e${i}`;
    e.drop = 'garantizado';
    return e;
  });
  enc.ordenPrevisto = enc.enemigos.map(e => e.id);
  return enc;
}

const casos = [
  ['escudero_celestial'],
  ['lancero_del_alba'],
  ['arquero_del_firmamento'],
  ['escudero_celestial', 'escudero_celestial'],
  ['escudero_celestial', 'lancero_del_alba'],
  ['escudero_celestial', 'escudero_celestial', 'lancero_del_alba'],
  ['escudero_celestial', 'escudero_celestial', 'lancero_del_alba', 'arquero_del_firmamento'],
  ['escudero_celestial', 'escudero_celestial', 'lancero_del_alba', 'arquero_del_firmamento', 'arquero_del_firmamento']
];

// Donde la espada ya gana el 100%, la tasa de victoria no distingue nada:
// ahi la ventaja se mide en TIEMPO y DAÑO, que es lo que dice el §5.2.
const dl = (a, b) => (a == null || b == null || !b) ? '   —' :
  `${(((a - b) / b) * 100 >= 0 ? '+' : '')}${(((a - b) / b) * 100).toFixed(0)}%`.padStart(5);

console.log('composicion'.padEnd(40) + 'gana espada  gana armas   Δtiempo  Δdaño  armas/part');
for (const c of casos) {
  const lote = correrLote(arenaCon(c), cal, armas, { partidas: 60 });
  const e = lote.porPolitica['cercano'].resumen;
  const v = lote.porPolitica['ventaja'].resumen;
  const etiqueta = c.map(a => a.split('_')[0][0].toUpperCase() + a.split('_')[0].slice(1)).join(' + ');
  console.log(
    etiqueta.padEnd(40) +
    `${(e.tasaVictoria * 100).toFixed(0).padStart(10)}%` +
    `${(v.tasaVictoria * 100).toFixed(0).padStart(11)}%` +
    `${dl(v.tiempoMediana, e.tiempoMediana).padStart(10)}` +
    `${dl(v.danoMediana, e.danoMediana).padStart(7)}` +
    `${String(v.armasPorPartida).padStart(12)}`
  );
}
