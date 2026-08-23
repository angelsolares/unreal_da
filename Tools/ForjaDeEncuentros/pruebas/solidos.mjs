// Nadie atraviesa lo que se dibuja macizo.
//
// La vista 3D pinta las plataformas como bloques, y con razon: desde abajo un
// balcon de 3,5 m es un muro. Pero el simulador las trataba como aire y los
// agentes cruzaban por dentro — se veia en la 3D, con los personajes metidos en
// la caja. Esta prueba recorre partidas enteras comprobando, tick a tick, que
// nadie esta donde no cabe.
//
//   node pruebas/solidos.mjs

import { Simulacion } from '../js/sim.js';
import { crearPoliticas } from '../js/politicas.js';
import { obstaculosDe } from '../js/esquema.js';
import { dentroDePoligono } from '../js/geometria.js';
import { cal, armas, encuentro } from './cargar.mjs';

let fallos = 0;

for (const nombre of ['romper-la-linea', 'cadena-perfecta']) {
  const enc = encuentro(nombre);
  const solidos = obstaculosDe(enc).filter(o => o.bloqueaPaso);
  console.log(`\n--- ${enc.nombre}: ${solidos.length} solidos ---`);
  if (!solidos.length) { console.log('   (sin obstaculos que comprobar)'); continue; }

  const dentro = new Map();   // etiqueta del solido -> ticks con alguien dentro
  let ticks = 0;

  for (const pol of crearPoliticas()) {
    for (let s = 0; s < 12; s++) {
      const sim = new Simulacion(enc, cal, armas, pol, 3000 + s);
      while (!sim.terminada) {
        sim.paso();
        ticks++;
        for (const a of sim.agentes) {
          if (a.estado === 'muerto') continue;
          for (const o of solidos) {
            // Solo cuenta si el agente esta POR DEBAJO de la cima: por encima
            // se camina encima, que es lo correcto.
            const cima = (o.cota || 0) + (o.altura || 0);
            if (cima <= (a.cota || 0) + 20) continue;
            if (!dentroDePoligono(a.pos, o.poli)) continue;
            const clave = `${o.id || 'sin-id'}${o.esPlataforma ? ' (plataforma)' : ''}`;
            dentro.set(clave, (dentro.get(clave) || 0) + 1);
          }
        }
      }
    }
  }

  console.log(`   ${ticks} ticks recorridos`);
  if (!dentro.size) {
    console.log('   OK   nadie se mete dentro de nada');
  } else {
    for (const [clave, n] of dentro) {
      console.log(`   MAL  ${n} ticks con alguien dentro de "${clave}"`);
      fallos++;
    }
  }
}

console.log(fallos ? `\n${fallos} solidos atravesados` : '\ntodo solido es solido');
process.exitCode = fallos ? 1 : 0;
