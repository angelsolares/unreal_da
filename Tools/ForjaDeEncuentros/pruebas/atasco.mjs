// Busca la primera partida que agota el tiempo y la disecciona.
//   node pruebas/atasco.mjs [politica]

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { cal, armas, encuentro } from './cargar.mjs';

const enc = encuentro();
const pol = crearPolitica(process.argv[2] || 'cercano');

for (let s = 1234; s < 1234 + 200; s++) {
  const sim = new Simulacion(enc, cal, armas, pol, s);
  const r = sim.correr();
  if (r.razonFin !== 'tiempo') continue;
  console.log(`semilla ${s} (${pol.nombre}): atasco. bajas=${r.ordenDeBajas.length} golpes=${r.golpesAsestados}`);
  for (const e of sim.enemigos) {
    console.log(`   ${e.id.padEnd(15)} hp=${Math.round(e.hp)} cota=${e.cota} pos=(${Math.round(e.pos.x)},${Math.round(e.pos.y)}) alertado=${e.alertado} ${e.estado}`);
  }
  const M = sim.malakh;
  console.log(`   malakh hp=${Math.round(M.hp)} cota=${M.cota} pos=(${Math.round(M.pos.x)},${Math.round(M.pos.y)}) obj=${M.objetivoId} arma=${M.temporal?.familia || 'espada'} pociones=${M.pociones}`);
  console.log(`   ultimos: ${r.eventos.slice(-6).map(e => `${e.t} ${e.tipo}`).join(' | ')}`);
  process.exit(0);
}
console.log(`Sin atascos en 200 semillas con "${pol.nombre}".`);
