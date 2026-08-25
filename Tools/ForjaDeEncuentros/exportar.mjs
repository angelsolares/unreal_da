// Llevar una receta al editor desde la linea de ordenes.
//
//   node exportar.mjs [encuentro] [--offset x,y,z] [--confirmar]
//
// El exportador es un modulo (exportador.mjs) y hasta hoy solo se le llamaba
// desde el servidor web. Esto es la misma llamada sin navegador de por medio.
//
// NO CAMBIA DE NIVEL: coloca en el que tengas abierto, que es la regla 1 del
// exportador y viene de haber dejado al editor sin mundo una vez. Abre tu el
// nivel destino antes de llamar.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { desdeJSON } from './js/esquema.js';
import { exportar } from './exportador.mjs';

const raiz = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const nombre = args.find(a => !a.startsWith('--')) || 'romper-la-linea';
const crudo = args.find(a => a.startsWith('--offset='));
const offset = crudo
  ? (([x, y, z]) => ({ x: +x || 0, y: +y || 0, z: +z || 0 }))(crudo.split('=')[1].split(','))
  : { x: 0, y: 0, z: 0 };

const enc = desdeJSON(fs.readFileSync(path.join(raiz, `datos/encuentros/${nombre}.json`), 'utf8'));
console.log(`\nExportando "${enc.nombre}" — ${enc.enemigos.length} enemigos, ${enc.oleadas.length} oleadas`);
console.log(`offset ${offset.x}, ${offset.y}, ${offset.z}\n`);

const r = await exportar({ encuentro: enc, offset, confirmarNivel: args.includes('--confirmar') });
console.log(JSON.stringify(r, null, 2));
