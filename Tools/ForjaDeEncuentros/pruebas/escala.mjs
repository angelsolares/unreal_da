// ¿Cuantos enemigos aguanta Malakh solo con espada?
// Es la prueba de cordura del simulador: si no gana ni un 1-contra-1, el roto
// es el modelo. Si gana el 1v1 y pierde el 1v5, el roto es el balance de DCS.
//   node pruebas/escala.mjs

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { correrLote } from '../js/lote.js';
import { encuentroVacio, nuevoEnemigo } from '../js/esquema.js';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const cal = JSON.parse(fs.readFileSync(path.join(aqui, '..', 'datos/calibracion.json'), 'utf8'));

function arenaCon(arquetipos) {
  const enc = encuentroVacio('escala');
  enc.arena.entrada = { x: -1200, y: 0 };
  enc.enemigos = arquetipos.map((a, i) => {
    const e = nuevoEnemigo(a, 300, (i - (arquetipos.length - 1) / 2) * 320);
    e.id = `e${i}`;
    return e;
  });
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

console.log('composicion'.padEnd(46) + 'victorias   t(mediana)  daño(mediana)');
for (const c of casos) {
  const lote = correrLote(arenaCon(c), cal, { partidas: 60 });
  const r = lote.porPolitica['cercano'].resumen;
  const etiqueta = c.map(a => a.split('_')[0][0].toUpperCase() + a.split('_')[0].slice(1)).join(' + ');
  console.log(
    etiqueta.padEnd(46) +
    `${(r.tasaVictoria * 100).toFixed(0).padStart(6)}%` +
    `${String(r.tiempoMediana ?? '—').padStart(12)}s` +
    `${String(r.danoMediana ?? '—').padStart(14)}`
  );
}
