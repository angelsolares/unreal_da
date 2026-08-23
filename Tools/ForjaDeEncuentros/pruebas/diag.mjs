import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { desdeJSON } from '../js/esquema.js';
import { techoDeLaEspada, danoNecesario, vidaNecesaria } from '../js/diagnostico.js';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const cal = JSON.parse(fs.readFileSync(path.join(aqui, '..', 'datos/calibracion.json'), 'utf8'));
const enc = desdeJSON(fs.readFileSync(path.join(aqui, '..', 'datos/encuentros/romper-la-linea.json'), 'utf8'));

const t0 = Date.now();
const techo = techoDeLaEspada(enc, cal);
console.log(`techo de la espada: ${techo.techo} de ${techo.pedidos} enemigos`);
for (const e of techo.escalones) console.log(`   ${e.n} enemigos -> ${(e.tasa*100).toFixed(0)}%`);

const dano = danoNecesario(enc, cal);
console.log('\ndano necesario:', JSON.stringify(dano));

const vida = vidaNecesaria(enc, cal);
console.log('vida necesaria:', JSON.stringify(vida));
console.log(`\n(${Date.now()-t0} ms)`);
