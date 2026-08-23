// Techo de la espada y palancas de balance para este encuentro.
//   node pruebas/diag.mjs

import { techoDeLaEspada, danoNecesario, vidaNecesaria } from '../js/diagnostico.js';
import { cal, armas, encuentro } from './cargar.mjs';

const enc = encuentro(process.argv[2]);
const t0 = Date.now();

const techo = techoDeLaEspada(enc, cal, armas);
console.log(`techo de la espada: ${techo.techo} de ${techo.pedidos} enemigos`);
for (const e of techo.escalones) console.log(`   ${e.n} enemigos -> ${(e.tasa * 100).toFixed(0)}%`);

console.log('\ndano necesario:', JSON.stringify(danoNecesario(enc, cal, armas)));
console.log('vida necesaria:', JSON.stringify(vidaNecesaria(enc, cal, armas)));
console.log(`\n(${Date.now() - t0} ms)`);
