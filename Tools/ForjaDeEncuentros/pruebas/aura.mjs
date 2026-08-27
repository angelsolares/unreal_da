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

// Las pruebas de radio y muerte van SIN retraso: miden la geometria del buff,
// no su timing. El timing tiene su propio bloque abajo.
const calSinRetraso = JSON.parse(JSON.stringify(cal));
calSinRetraso.aura.retraso = 0;

/** Daño que declara un vigilante al arrancar su ataque, con el portador a `d` cm. */
function danoConPortadorA(d, portadorVivo = true, calibracion = calSinRetraso) {
  const enc = encuentroVacio();
  enc.enemigos = [
    { ...nuevoEnemigo('escudero_celestial', 0, 0), id: 'vigi' },
    { ...nuevoEnemigo('portador_del_estandarte', d, 0), id: 'porta' }
  ];
  const sim = new Simulacion(enc, calibracion, armas, crearPolitica(POLITICA_BASE), 1);
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
  const sim = new Simulacion(enc, calSinRetraso, armas, crearPolitica(POLITICA_BASE), 1);
  const p = sim.enemigos[0];
  comprobar('el portador no se buffea a si mismo',
    sim._danoDe(p) === cal.arquetipos.portador_del_estandarte.dano);
}

// El +75% que midio la sesion de Unreal: 20 -> 35.
comprobar('reproduce el +75% medido en juego (20 -> 35)',
  danoConPortadorA(506) === 35, `${danoConPortadorA(506)}`);

// --- el ARRANQUE (§5.1, 26/08): el aura no nace encendida -------------------
//
// Espejo de VigilarArranque/ActivarAura: el retraso cuenta desde que el jugador
// entra en radioArranque, y hasta agotarse el buff NO suma.
{
  const enc = encuentroVacio();
  enc.enemigos = [
    { ...nuevoEnemigo('escudero_celestial', 0, 0), id: 'vigi' },
    { ...nuevoEnemigo('portador_del_estandarte', 506, 0), id: 'porta' }
  ];
  const base = cal.arquetipos.escudero_celestial.dano;
  const bono = cal.aura.bonificacion;
  const sim = new Simulacion(enc, cal, armas, crearPolitica(POLITICA_BASE), 1);
  const porta = sim.enemigos.find(e => e.id === 'porta');
  const vigi = sim.enemigos.find(e => e.id === 'vigi');

  // el jugador del encuentro vacio nace LEJOS: hay que acercarlo para que
  // el portador lo "vea" (radioArranque)
  sim.malakh.pos = { x: porta.pos.x - 300, y: 0 };
  sim._pasoAura();
  comprobar('recien visto, el buff NO suma todavia',
    sim._danoDe(vigi) === base,
    `${sim._danoDe(vigi)} vs ${base} (retraso ${cal.aura.retraso} s, tVista=${porta.tVistaAura})`);

  sim.t = cal.aura.retraso + 0.1;          // el reloj pasa; tVistaAura quedo en 0
  comprobar('agotado el retraso, suma',
    sim._danoDe(vigi) === base + bono, `${sim._danoDe(vigi)}`);

  // Y el radio de arranque manda: un portador al que el jugador nunca se ha
  // acercado no arranca aunque pase el tiempo.
  const sim2 = new Simulacion(enc, cal, armas, crearPolitica(POLITICA_BASE), 1);
  const porta2 = sim2.enemigos.find(e => e.id === 'porta');
  porta2.pos = { x: cal.aura.radioArranque + 800, y: 0 };
  sim2._pasoAura();
  sim2.t = 60;
  const vigi2 = sim2.enemigos.find(e => e.id === 'vigi');
  comprobar('sin haber visto al jugador, nunca arranca',
    porta2.tVistaAura == null && sim2._danoDe(vigi2) === base,
    `tVistaAura=${porta2.tVistaAura}`);
}

console.log(fallos ? `\n${fallos} fallos` : '\nsin fallos');
process.exit(fallos ? 1 : 0);
