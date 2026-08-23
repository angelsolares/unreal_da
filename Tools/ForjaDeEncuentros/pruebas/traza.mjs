// Traza una sola partida, para depurar el simulador cuando el lote dice algo raro.
//   node pruebas/traza.mjs [semilla] [politica]

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { cal, armas, encuentro } from './cargar.mjs';

const enc = encuentro();
const semilla = Number(process.argv[2] || 1234);
const pol = crearPolitica(process.argv[3] || 'ventaja');
if (!pol) { console.error('politica desconocida'); process.exit(1); }

const sim = new Simulacion(enc, cal, armas, pol, semilla);
const r = sim.correr();

console.log(`politica=${pol.nombre}  semilla=${semilla}`);
console.log(`fin=${r.razonFin}  t=${r.tiempo}s  hp=${r.hpFinal}  daño=${r.danoRecibido}  pociones=${r.pocionesBebidas}`);
console.log(`golpes: ${r.golpesAsestados} dados / ${r.golpesFallados} fallados / ${r.esquivasLogradas} esquivas`);
console.log(`armas recogidas: ${r.armasRecogidas.map(a => `${a.familia}@${a.t}s`).join(', ') || 'ninguna'}`);
console.log(`descartes: ${r.descartesUsados}   max armas en el suelo a la vez: ${r.maxDropsSimultaneos}`);

console.log('\nHP de cada enemigo al final:');
for (const e of sim.enemigos) {
  console.log(`   ${e.id.padEnd(16)} ${String(Math.round(e.hp)).padStart(4)}/${e.hpMax}  ${e.estado}  alertado=${e.alertado}`);
}

const cuenta = {};
for (const ev of r.eventos) cuenta[ev.tipo] = (cuenta[ev.tipo] || 0) + 1;
console.log('\neventos:', cuenta);

console.log('\nhitos:');
for (const ev of r.eventos) {
  if (['baja', 'suelta', 'equipa', 'desmaterializa', 'descarte', 'agotada', 'sealBreak', 'dropExpirado', 'sinDrop', 'victoria', 'derrota'].includes(ev.tipo)) {
    console.log('   ' + JSON.stringify(ev));
  }
}
