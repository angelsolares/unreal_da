// ¿Que se lee desde la puerta? (§5.1)
//   node pruebas/lectura.mjs [encuentro]

import { lecturaDesdeLaEntrada, LIMITE_LECTURA } from '../js/lectura.js';
import { cal, encuentro } from './cargar.mjs';

const enc = encuentro(process.argv[2]);
console.log(`${enc.nombre} — desde la entrada (${enc.arena.entrada.x}, ${enc.arena.entrada.y}), ojos a ${cal.malakh.alturaOjos} cm\n`);
console.log('enemigo'.padEnd(20) + 'llave  estado    dist    silueta  de eso, arma');
for (const f of lecturaDesdeLaEntrada(enc, cal)) {
  console.log(
    f.etiqueta.padEnd(20) +
    (f.llaveTactica ? '  SI ' : '  -- ') +
    f.estado.padEnd(10) +
    `${f.distancia}`.padStart(6) +
    `${f.grados.toFixed(2)}°`.padStart(10) +
    `${(f.fraccionArma * 100).toFixed(0)}%`.padStart(14) +
    (f.nombreArma ? `  (${f.nombreArma})` : '')
  );
}
console.log(`\nlimite de lectura asumido: ${LIMITE_LECTURA} cm`);
