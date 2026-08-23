import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
import { desdeJSON } from '../js/esquema.js';
import { Simulacion } from '../js/sim.js';
import { crearPoliticas } from '../js/politicas.js';
const aqui = path.dirname(fileURLToPath(import.meta.url));
const cal = JSON.parse(fs.readFileSync(path.join(aqui,'..','datos/calibracion.json'),'utf8'));
const enc = desdeJSON(fs.readFileSync(path.join(aqui,'..','datos/encuentros/romper-la-linea.json'),'utf8'));
for (let s=1234; s<1234+200; s++) {
  const sim = new Simulacion(enc, cal, crearPoliticas().find(p=>p.id==='cercano'), s);
  const r = sim.correr();
  if (r.razonFin !== 'tiempo') continue;
  console.log(`semilla ${s}: atasco. bajas=${r.ordenDeBajas.length} golpes=${r.golpesAsestados}`);
  for (const e of sim.enemigos) console.log(`   ${e.id.padEnd(15)} hp=${Math.round(e.hp)} cota=${e.cota} pos=(${Math.round(e.pos.x)},${Math.round(e.pos.y)}) alertado=${e.alertado} ${e.estado}`);
  console.log(`   malakh hp=${Math.round(sim.malakh.hp)} cota=${sim.malakh.cota} pos=(${Math.round(sim.malakh.pos.x)},${Math.round(sim.malakh.pos.y)}) obj=${sim.malakh.objetivoId} pociones=${sim.malakh.pociones}`);
  const ult = r.eventos.slice(-6).map(e=>`${e.t} ${e.tipo}`).join(' | ');
  console.log(`   ultimos: ${ult}`);
  break;
}
