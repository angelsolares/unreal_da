// Que el exportador SE PUEDA CARGAR. Suena a poco y es justo lo que faltaba.
//
//   node pruebas/exportador.mjs
//
// POR QUE EXISTE. El 25/08 un commit metio tres comentarios de Python con
// backticks alrededor de un identificador —markdown por costumbre— y el fichero
// dejo de parsear: el Python va dentro de un template literal de JS, y un
// backtick ahi CIERRA el template, con lo que lo de en medio se lee como codigo.
// El error es "missing ) after argument list" en una linea de Python, que no
// ayuda nada.
//
// Estuvo roto TRES DIAS sin que nadie se enterase, porque `npm test` no tocaba
// el exportador y el camino de exportar no se volvio a usar. Se descubrio el
// 26/08 al ir a exportar la segunda receta.
//
// La prueba no exporta nada ni habla con el editor: solo importa el modulo y
// mira que el Python embebido no lleve backticks. Con eso basta.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const raiz = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
let fallos = 0;
const comprobar = (nombre, ok, detalle = '') => {
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${nombre}${detalle ? '  — ' + detalle : ''}`);
  if (!ok) fallos++;
};

console.log('--- el exportador carga ---');
let mod = null;
try {
  mod = await import('../exportador.mjs');
  comprobar('exportador.mjs importa', true);
} catch (e) {
  comprobar('exportador.mjs importa', false, e.message);
}
comprobar('exporta una funcion `exportar`', typeof mod?.exportar === 'function');

// Y la causa raiz, por si vuelve: ningun backtick dentro del Python embebido.
console.log('\n--- el Python embebido no lleva backticks ---');
const BT = String.fromCharCode(96);
const lineas = fs.readFileSync(path.join(raiz, 'exportador.mjs'), 'utf8').split(/\r?\n/);
let dentro = false;
const sucias = [];
for (let i = 0; i < lineas.length; i++) {
  const l = lineas[i];
  if (!dentro && new RegExp('await python\\(' + BT).test(l)) { dentro = true; continue; }
  if (dentro && l.trim().indexOf(BT + ');') === 0) { dentro = false; continue; }
  if (dentro && l.indexOf(BT) >= 0) sucias.push(i + 1);
}
comprobar('sin backticks dentro de los bloques python', sucias.length === 0,
          sucias.length ? 'lineas ' + sucias.join(', ') : '');
comprobar('los bloques python estan cerrados', dentro === false);

console.log(fallos ? `\n${fallos} fallos` : '\nsin fallos');
process.exitCode = fallos ? 1 : 0;
