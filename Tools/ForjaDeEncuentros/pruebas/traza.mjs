// Traza una sola partida, para depurar el simulador cuando el lote dice algo raro.
//   node pruebas/traza.mjs [semilla] [politica]

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Simulacion } from '../js/sim.js';
import { crearPoliticas } from '../js/politicas.js';
import { desdeJSON } from '../js/esquema.js';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const cal = JSON.parse(fs.readFileSync(path.join(aqui, '..', 'datos/calibracion.json'), 'utf8'));
const enc = desdeJSON(fs.readFileSync(path.join(aqui, '..', 'datos/encuentros/romper-la-linea.json'), 'utf8'));

const semilla = Number(process.argv[2] || 1234);
const idPol = process.argv[3] || 'cercano';
const pol = crearPoliticas().find(p => p.id === idPol);

const sim = new Simulacion(enc, cal, pol, semilla);
const r = sim.correr();

console.log(`politica=${pol.nombre}  semilla=${semilla}`);
console.log(`fin=${r.razonFin}  t=${r.tiempo}s  hp=${r.hpFinal}  daño=${r.danoRecibido}`);
console.log(`golpes: ${r.golpesAsestados} dados / ${r.golpesFallados} fallados / ${r.esquivasLogradas} esquivas`);
console.log(`enemigos vivos al final: ${r.enemigosVivos}`);
console.log('\nHP de cada enemigo al final:');
for (const e of sim.enemigos) {
  console.log(`   ${e.id.padEnd(16)} ${String(Math.round(e.hp)).padStart(4)}/${e.hpMax}  ${e.estado}  alertado=${e.alertado}`);
}

const cuenta = {};
for (const ev of r.eventos) cuenta[ev.tipo] = (cuenta[ev.tipo] || 0) + 1;
console.log('\neventos:', cuenta);

console.log('\nprimeros 45 eventos:');
for (const ev of r.eventos.slice(0, 45)) {
  console.log('   ' + JSON.stringify(ev));
}
