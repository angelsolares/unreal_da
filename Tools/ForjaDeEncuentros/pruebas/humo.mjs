// Prueba de humo: corre el lote sin navegador.
//   node pruebas/humo.mjs
// Sirve para dos cosas: que el simulador no reviente, y que el determinismo
// se cumpla (misma semilla -> mismo resultado, byte a byte).

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Simulacion } from '../js/sim.js';
import { crearPoliticas } from '../js/politicas.js';
import { correrLote } from '../js/lote.js';
import { desdeJSON, validar } from '../js/esquema.js';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const leer = (p) => JSON.parse(fs.readFileSync(path.join(aqui, '..', p), 'utf8'));

const cal = leer('datos/calibracion.json');
const enc = desdeJSON(fs.readFileSync(path.join(aqui, '..', 'datos/encuentros/romper-la-linea.json'), 'utf8'));

console.log(`Encuentro: ${enc.nombre} — ${enc.enemigos.length} enemigos\n`);

// 1. validacion estatica
const problemas = validar(enc);
console.log('--- validacion estatica ---');
if (!problemas.length) console.log('   sin problemas');
for (const p of problemas) console.log(`   [${p.nivel}] ${p.codigo}: ${p.texto}`);

// 2. determinismo
const pol = crearPoliticas()[0];
const a = new Simulacion(enc, cal, pol, 99).correr();
const b = new Simulacion(enc, cal, crearPoliticas()[0], 99).correr();
const mismo = a.tiempo === b.tiempo && a.danoRecibido === b.danoRecibido &&
              JSON.stringify(a.ordenDeBajas) === JSON.stringify(b.ordenDeBajas);
console.log(`\n--- determinismo --- ${mismo ? 'OK' : 'ROTO'}  (t=${a.tiempo}s, daño=${a.danoRecibido})`);
if (!mismo) process.exitCode = 1;

// 3. lote completo
const t0 = Date.now();
const lote = correrLote(enc, cal, { partidas: 200 });
const ms = Date.now() - t0;
console.log(`\n--- lote: 4 politicas x ${lote.partidas} partidas en ${ms} ms ---`);
for (const p of Object.values(lote.porPolitica)) {
  const r = p.resumen;
  console.log(
    `   ${p.nombre.padEnd(20)} victorias ${(r.tasaVictoria * 100).toFixed(0).padStart(3)}%  ` +
    `t=${String(r.tiempoMediana ?? '—').padStart(5)}s  daño=${String(r.danoMediana ?? '—').padStart(5)}  ` +
    `muertes=${r.porMuerte}  atascos=${r.porTiempo}`
  );
}

console.log(`\n--- veredicto: ${lote.veredicto.titular} ---`);
for (const g of lote.veredicto.puertas) {
  const marca = { ok: '[OK]  ', aviso: '[AVI] ', fallo: '[FALLO]', na: '[--]  ' }[g.estado];
  console.log(`   ${marca} ${g.titulo}  (${g.referencia})`);
  console.log(`            ${g.texto}`);
}

console.log(`\n--- fuentes de daño (politica base) ---`);
for (const f of lote.porPolitica['cercano'].resumen.danoPorFuente) {
  console.log(`   ${f.arquetipo.padEnd(26)} ${(f.fraccion * 100).toFixed(0).padStart(3)}%  (${f.total})`);
}

console.log(`\n--- testigo grabado: ${lote.testigo ? lote.testigo.fotogramas.length + ' fotogramas' : 'ninguno'} ---`);
if (lote.testigo) {
  for (const b of lote.testigo.ordenDeBajas) console.log(`   ${b.t}s  cae ${b.id} (${b.arquetipo})`);
}
