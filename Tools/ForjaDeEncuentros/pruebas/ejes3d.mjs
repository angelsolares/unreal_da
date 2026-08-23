// El mapeo de ejes de la vista 3D, comprobado sin navegador.
//
// Un eje con el signo cambiado no se nota mirando una maqueta —todo parece
// plausible— pero invalida cualquier cosa que se juzgue en ella: la lanza del
// balcon sale por el lado que no es y el "se lee desde la entrada" miente.
//
//   node pruebas/ejes3d.mjs

import { aTres } from '../js/vista3d.js';
import { encuentro } from './cargar.mjs';

let fallos = 0;
const esperar = (nombre, real, esperado, tol = 1e-6) => {
  const ok = ['x', 'y', 'z'].every(k => Math.abs(real[k] - esperado[k]) <= tol);
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${nombre.padEnd(34)} (${real.x.toFixed(2)}, ${real.y.toFixed(2)}, ${real.z.toFixed(2)})`);
  if (!ok) { fallos++; console.log(`        esperado (${esperado.x}, ${esperado.y}, ${esperado.z})`); }
};

console.log('--- convenio: X(norte)->-Z, Y(este)->X, cota->Y, cm->m ---');
esperar('origen', aTres({ x: 0, y: 0 }, 0), { x: 0, y: 0, z: 0 });
esperar('100 cm al norte (X+)', aTres({ x: 100, y: 0 }, 0), { x: 0, y: 0, z: -1 });
esperar('100 cm al este (Y+)', aTres({ x: 0, y: 100 }, 0), { x: 1, y: 0, z: 0 });
esperar('cota 350', aTres({ x: 0, y: 0 }, 350), { x: 0, y: 3.5, z: 0 });
esperar('combinado', aTres({ x: -200, y: 400 }, 50), { x: 4, y: 0.5, z: 2 });

console.log('\n--- coherencia con el encuentro real ---');
const enc = encuentro();
const entrada = aTres(enc.arena.entrada, 0);
const balcon = enc.enemigos.find(e => (e.cota || 0) > 50);

// La entrada esta al oeste (X negativo) -> en Three debe quedar en +Z.
const okEntrada = entrada.z > 0;
console.log(`   ${okEntrada ? 'OK  ' : 'MAL '} la entrada queda detras del centro (z=${entrada.z.toFixed(2)} > 0)`);
if (!okEntrada) fallos++;

if (balcon) {
  const v = aTres(balcon.pos, balcon.cota);
  const okAlto = Math.abs(v.y - balcon.cota / 100) < 1e-6;
  const okLejos = v.z < entrada.z;
  console.log(`   ${okAlto ? 'OK  ' : 'MAL '} el del balcon esta a ${v.y.toFixed(2)} m de alto`);
  console.log(`   ${okLejos ? 'OK  ' : 'MAL '} y mas lejos de la puerta (z=${v.z.toFixed(2)} < ${entrada.z.toFixed(2)})`);
  if (!okAlto) fallos++;
  if (!okLejos) fallos++;
}

console.log(fallos ? `\n${fallos} comprobaciones MAL` : '\ntodo correcto');
process.exitCode = fallos ? 1 : 0;
