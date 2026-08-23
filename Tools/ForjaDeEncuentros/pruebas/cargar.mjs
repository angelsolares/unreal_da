// Carga de datos compartida por los scripts de prueba.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { desdeJSON } from '../js/esquema.js';

const raiz = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const leer = (rel) => fs.readFileSync(path.join(raiz, rel), 'utf8');

export const cal = JSON.parse(leer('datos/calibracion.json'));
export const armas = JSON.parse(leer('datos/armas.json'));

export function encuentro(nombre = 'romper-la-linea') {
  return desdeJSON(leer(`datos/encuentros/${nombre}.json`));
}
