// Extrae el registro de ritmo [BEAT] del log del juego a un fichero de texto limpio
// y resume las ventanas sin evento ni combate.
//
//   node beats.mjs                 -> lee Saved/Logs/DynamicCombatSystem.log (PIE)
//   node beats.mjs <ruta.log>      -> otro log (p. ej. el del build)
//
// Salida: Saved/Beats/beats_<fecha>.txt con las lineas y, al final, el resumen:
// cuantas ventanas superaron los 45 s, donde, y las lineas de +N s de cada una.
//
// El registro lo escribe BP_DA_DebugHUD (DbgCronoLog) y solo existe en PIE:
// el Debug HUD no entra en el build. La regla de diseno es "no mas de 45 s de
// avance sin evento ni combate".
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const log = process.argv[2] || join(raiz, 'Saved', 'Logs', 'DynamicCombatSystem.log');
if (!existsSync(log)) { console.error('no existe', log); process.exit(1); }

const lineas = readFileSync(log, 'utf8').split(/\r?\n/);
const beats = [];
for (const l of lineas) {
  const i = l.indexOf('[BEAT] ');
  if (i < 0) continue;
  const m = l.match(/^\[([0-9.\-:]+)\]/);          // marca de tiempo del log
  const hora = m ? m[1].replace(/^\d{4}\.\d{2}\.\d{2}-/, '').replace(/:\d{3}$/, '') : '';
  beats.push({ hora, texto: l.slice(i + 7).trim() });
}
if (!beats.length) { console.error('sin lineas [BEAT] en', log); process.exit(2); }

// Ventanas: desde un EVENTO/COMBATE/arranque hasta el siguiente. Se guarda el maximo "+N s".
const ventanas = [];
let actual = { inicio: 'arranque', hora: beats[0].hora, max: 0, avisos: 0, lineas: [] };
for (const b of beats) {
  const ev = b.texto.match(/^(EVENTO .*?|COMBATE) tras (\d+) s \| (.*)$/);
  const paso = b.texto.match(/^\+(\d+) s \| (.*)$/);
  const aviso = b.texto.startsWith('!! 45 s');
  if (ev) {
    actual.dur = +ev[2];
    ventanas.push(actual);
    actual = { inicio: ev[1], hora: b.hora, max: 0, avisos: 0, lineas: [], ctx: ev[3] };
  } else if (paso) {
    actual.max = Math.max(actual.max, +paso[1]);
    actual.lineas.push(b.texto);
  } else if (aviso) {
    actual.avisos++;
    actual.lineas.push(b.texto);
  }
}
actual.dur = actual.max;
ventanas.push(actual);

const largas = ventanas.filter(v => (v.dur ?? v.max) > 45);
const zona = (v) => { const m = (v.lineas[v.lineas.length - 1] || v.ctx || '').match(/zona=([^|]*)/); return m ? m[1].trim() : '?'; };

const fecha = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '').replace(/(\d{8})(\d{4})/, '$1_$2');
const dir = join(raiz, 'Saved', 'Beats');
mkdirSync(dir, { recursive: true });
const salida = join(dir, `beats_${fecha}.txt`);

const out = [];
out.push(`REGISTRO DE RITMO  (${beats.length} lineas, ${ventanas.length} ventanas)  fuente: ${log}`);
out.push('');
for (const b of beats) out.push(`${b.hora}  ${b.texto}`);
out.push('');
out.push('='.repeat(78));
out.push(`RESUMEN: ${largas.length} ventana(s) de mas de 45 s sin evento ni combate`);
for (const v of largas) {
  out.push(`  - desde ${v.hora} tras "${v.inicio}": ${v.dur ?? v.max} s  (zona: ${zona(v)})`);
  for (const l of v.lineas) out.push(`        ${l}`);
}
out.push('');
out.push('Ventanas por orden (inicio -> duracion):');
for (const v of ventanas) out.push(`  ${String(v.dur ?? v.max).padStart(4)} s  ${v.hora}  ${v.inicio}  [${zona(v)}]`);
writeFileSync(salida, out.join('\n') + '\n');
console.log(out.slice(-ventanas.length - 3 - largas.length * 1).join('\n'));
console.log('\nescrito:', salida);
