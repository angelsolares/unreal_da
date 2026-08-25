// Prueba de humo: corre el lote sin navegador.
//   node pruebas/humo.mjs
// Sirve para dos cosas: que el simulador no reviente, y que el determinismo
// se cumpla (misma semilla -> mismo resultado).

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { correrLote } from '../js/lote.js';
import { validar, oleadasDe } from '../js/esquema.js';
import { cal, armas, encuentro } from './cargar.mjs';

const enc = encuentro(process.argv[2]);
console.log(`Encuentro: ${enc.nombre} — ${enc.enemigos.length} enemigos\n`);

// Las oleadas del §6, si las hay. Sin esto el lote dice "5 enemigos" y no se ve
// que nunca hay mas de dos a la vez, que es justo lo que hace ganable la receta.
const olas = oleadasDe(enc).filter(o => !o.implicita);
if (olas.length) {
  console.log('--- oleadas ---');
  for (const o of olas) {
    const a = o.activacion;
    const cuando = a.tipo === 'inicio' ? 'al romper el sello'
      : a.tipo === 'tiempo' ? `a los ${a.segundos} s`
      : a.tipo === 'bajas' ? `con ${a.cuantas} bajas`
      : `cuando caiga "${a.oleada}"`;
    console.log(`   ${String(o.nombre).padEnd(28)} ${String(o.enemigos.length).padStart(2)} enemigos · ${cuando}`
      + (o.retardo ? ` +${o.retardo}s` : '') + (o.presencia === 'entra' ? ' · ENTRA (no se ve al entrar)' : ''));
  }
  console.log('');
}

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
const lote = correrLote(enc, cal, armas, { partidas: Number(process.env.PARTIDAS || 1000) });
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
if (olas.length) {
  const ven = lote.porPolitica['ventaja'].resumen;
  console.log(`\n   como mucho ${ven.maxEnemigosALaVez} enemigos encima a la vez (mediana ${ven.enemigosALaVezMediana}).`);
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
