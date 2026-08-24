// El aura del Portador: que se aplique, que tenga radio y que muera con el.
//   node pruebas/aura.mjs

import { cal, armas } from './cargar.mjs';
import { Simulacion } from '../js/sim.js';
import { encuentroVacio, nuevoEnemigo } from '../js/esquema.js';
import { crearPolitica, POLITICA_BASE } from '../js/politicas.js';

let fallos = 0;
const comprobar = (t, ok, extra = '') => {
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${t}${extra ? '  — ' + extra : ''}`);
  if (!ok) fallos++;
};

/** Daño que declara un vigilante al arrancar su ataque, con el portador a `d` cm. */
function danoConPortadorA(d, portadorVivo = true) {
  const enc = encuentroVacio();
  enc.enemigos = [
    { ...nuevoEnemigo('escudero_celestial', 0, 0), id: 'vigi' },
    { ...nuevoEnemigo('portador_del_estandarte', d, 0), id: 'porta' }
  ];
  const sim = new Simulacion(enc, cal, armas, crearPolitica(POLITICA_BASE), 1);
  if (!portadorVivo) {
    const p = sim.enemigos.find(e => e.id === 'porta');
    p.estado = 'muerto';
  }
  return sim._danoDe(sim.enemigos.find(e => e.id === 'vigi'));
}

console.log('--- aura del Portador (contrato §1.2) ---');
const base = cal.arquetipos.escudero_celestial.dano;
const bono = cal.aura.bonificacion;

comprobar('dentro del radio, el aliado pega mas',
  danoConPortadorA(506) === base + bono, `${danoConPortadorA(506)} vs ${base}`);

comprobar('fuera del radio, no',
  danoConPortadorA(3000) === base, `${danoConPortadorA(3000)}`);

comprobar('portador muerto, no',
  danoConPortadorA(506, false) === base, `${danoConPortadorA(506, false)}`);

comprobar('el borde del radio es el que dice la calibracion',
  danoConPortadorA(cal.aura.radio - 1) === base + bono &&
  danoConPortadorA(cal.aura.radio + 1) === base);

// El portador no se buffea a si mismo: el componente recorre ALIADOS.
{
  const enc = encuentroVacio();
  enc.enemigos = [{ ...nuevoEnemigo('portador_del_estandarte', 0, 0), id: 'porta' }];
  const sim = new Simulacion(enc, cal, armas, crearPolitica(POLITICA_BASE), 1);
  const p = sim.enemigos[0];
  comprobar('el portador no se buffea a si mismo',
    sim._danoDe(p) === cal.arquetipos.portador_del_estandarte.dano);
}

// El +75% que midio la sesion de Unreal: 20 -> 35.
comprobar('reproduce el +75% medido en juego (20 -> 35)',
  danoConPortadorA(506) === 35, `${danoConPortadorA(506)}`);

console.log(fallos ? `\n${fallos} fallos` : '\nsin fallos');
process.exit(fallos ? 1 : 0);
