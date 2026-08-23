// Prueba de humo: corre el lote sin navegador.
//   node pruebas/humo.mjs
// Sirve para dos cosas: que el simulador no reviente, y que el determinismo
// se cumpla (misma semilla -> mismo resultado).

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { correrLote } from '../js/lote.js';
import { validar } from '../js/esquema.js';
import { cal, armas, encuentro } from './cargar.mjs';

const enc = encuentro(process.argv[2]);
console.log(`Encuentro: ${enc.nombre} — ${enc.enemigos.length} enemigos\n`);

// 1. validacion estatica
const problemas = validar(enc);
console.log('--- validacion estatica ---');
if (!problemas.length) console.log('   sin problemas');
for (const p of problemas) console.log(`   [${p.nivel}] ${p.codigo}: ${p.texto}`);

// 2. determinismo
const a = new Simulacion(enc, cal, armas, crearPolitica('ventaja'), 99).correr();
const b = new Simulacion(enc, cal, armas, crearPolitica('ventaja'), 99).correr();
const mismo = a.tiempo === b.tiempo && a.danoRecibido === b.danoRecibido &&
              JSON.stringify(a.ordenDeBajas) === JSON.stringify(b.ordenDeBajas);
console.log(`\n--- determinismo --- ${mismo ? 'OK' : 'ROTO'}  (t=${a.tiempo}s, daño=${a.danoRecibido})`);
if (!mismo) process.exitCode = 1;

// 3. lote completo
const t0 = Date.now();
const lote = correrLote(enc, cal, armas, { partidas: 200 });
console.log(`\n--- lote: 5 politicas x ${lote.partidas} partidas en ${Date.now() - t0} ms ---`);
console.log('   ' + 'politica'.padEnd(24) + 'gana  tiempo   daño  armas  descartes  muertes  atascos');
for (const p of Object.values(lote.porPolitica)) {
  const r = p.resumen;
  console.log('   ' + p.nombre.padEnd(24) +
    `${(r.tasaVictoria * 100).toFixed(0).padStart(3)}%` +
    `${String(r.tiempoMediana ?? '—').padStart(8)}` +
    `${String(r.danoMediana ?? '—').padStart(7)}` +
    `${String(r.armasPorPartida).padStart(7)}` +
    `${String(r.descartesPorPartida).padStart(11)}` +
    `${String(r.porMuerte).padStart(9)}` +
    `${String(r.porTiempo).padStart(9)}`);
}

console.log(`\n--- veredicto: ${lote.veredicto.titular} ---`);
for (const g of lote.veredicto.puertas) {
  const marca = { ok: '[OK]   ', aviso: '[AVISO]', fallo: '[FALLO]', na: '[--]   ' }[g.estado];
  console.log(`   ${marca} ${g.titulo}  (${g.referencia})`);
  console.log(`           ${g.texto}`);
}

const vent = lote.porPolitica['ventaja'].resumen;
console.log('\n--- que armas se recogen (ruta de ventaja) ---');
const entradas = Object.entries(vent.recogidas);
if (!entradas.length) console.log('   ninguna');
for (const [fam, veces] of entradas.sort((a, b) => b[1] - a[1])) {
  console.log(`   ${fam.padEnd(26)} ${(veces / lote.partidas).toFixed(2)} por partida`);
}

console.log('\n--- daño repartido por arma (ruta de ventaja) ---');
for (const d of vent.danoPorArma) {
  console.log(`   ${String(d.clave).padEnd(26)} ${(d.fraccion * 100).toFixed(0).padStart(3)}%  (${d.total})`);
}

console.log(`\n--- testigo: ${lote.testigo ? lote.testigo.fotogramas.length + ' fotogramas' : 'ninguno'} ---`);
if (lote.testigo) {
  for (const ev of lote.testigo.eventos) {
    if (['baja', 'suelta', 'equipa', 'descarte', 'agotada', 'sealBreak', 'desmaterializa'].includes(ev.tipo)) {
      console.log(`   ${String(ev.t).padStart(7)}s  ${ev.tipo.padEnd(15)} ${ev.arma || ev.agente || ''} ${ev.motivo || ''}`);
    }
  }
}
