// ¿La lanza paga? Composiciones elegidas para que SE RECOJA la lanza.
import { correrLote } from '../js/lote.js';
import { encuentroVacio, nuevoEnemigo } from '../js/esquema.js';
import { cal, armas } from './cargar.mjs';

function arena(arqs, drops) {
  const enc = encuentroVacio('lanza');
  enc.arena.entrada = { x: -1200, y: 0 };
  enc.enemigos = arqs.map((a, i) => {
    const e = nuevoEnemigo(a, 300, (i - (arqs.length - 1) / 2) * 340);
    e.id = `e${i}`;
    e.drop = drops ? drops[i] : 'garantizado';
    return e;
  });
  enc.ordenPrevisto = enc.enemigos.map(e => e.id);
  return enc;
}

const dl = (a,b) => (a==null||b==null||!b) ? '  —' : `${((a-b)/b*100>=0?'+':'')}${((a-b)/b*100).toFixed(0)}%`;

const casos = [
  ['2 Lanceros (cae 1 -> lanza)', ['lancero_del_alba','lancero_del_alba'], null],
  ['Lancero + Escudero (solo lanza)', ['lancero_del_alba','escudero_celestial'], ['garantizado','ninguno']],
  ['Lancero + 2 Escuderos (solo lanza)', ['lancero_del_alba','escudero_celestial','escudero_celestial'], ['garantizado','ninguno','ninguno']],
  ['Lancero + Arquero (solo lanza)', ['lancero_del_alba','arquero_del_firmamento'], ['garantizado','ninguno']],
  ['Elite + 2 Escuderos (solo espadon)', ['elite_pesado','escudero_celestial','escudero_celestial'], ['garantizado','ninguno','ninguno']],
];

console.log('caso'.padEnd(38) + 'gana espada  gana armas  Δtiempo  Δdaño  armas/part  descartes');
for (const [nombre, arqs, drops] of casos) {
  const lote = correrLote(arena(arqs, drops), cal, armas, { partidas: 80 });
  const e = lote.porPolitica['cercano'].resumen;
  const v = lote.porPolitica['ventaja'].resumen;
  console.log(nombre.padEnd(38) +
    `${(e.tasaVictoria*100).toFixed(0).padStart(10)}%` +
    `${(v.tasaVictoria*100).toFixed(0).padStart(11)}%` +
    `${dl(v.tiempoMediana,e.tiempoMediana).padStart(9)}` +
    `${dl(v.danoMediana,e.danoMediana).padStart(7)}` +
    `${String(v.armasPorPartida).padStart(12)}` +
    `${String(v.descartesPorPartida).padStart(11)}`);
  const r = Object.entries(v.recogidas).map(([k,n]) => `${k.split('_')[0]}:${(n/80).toFixed(2)}`).join(' ');
  console.log(`   recoge: ${r || 'nada'}`);
}
