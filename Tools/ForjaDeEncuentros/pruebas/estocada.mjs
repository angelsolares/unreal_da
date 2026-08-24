// La estocada: que solo salga de lejos, que cierre la distancia y que respete
// su enfriamiento.  node pruebas/estocada.mjs

import { cal, armas } from './cargar.mjs';
import { Simulacion, ESTADOS } from '../js/sim.js';
import { encuentroVacio, nuevoEnemigo } from '../js/esquema.js';
import { crearPolitica, POLITICA_BASE } from '../js/politicas.js';

let fallos = 0;
const comprobar = (t, ok, extra = '') => {
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${t}${extra ? '  — ' + extra : ''}`);
  if (!ok) fallos++;
};

/** Un enemigo a `d` cm de Malakh, sin que Malakh haga nada. */
function banco(d, semilla) {
  const enc = encuentroVacio();
  enc.jugador.pos = { x: 0, y: 0 };
  enc.enemigos = [{ ...nuevoEnemigo('escudero_celestial', d, 0), id: 'e0' }];
  enc.ordenPrevisto = ['e0'];
  const sim = new Simulacion(enc, cal, armas, crearPolitica(POLITICA_BASE), semilla);
  return sim;
}

console.log('--- la estocada (BT_WarriorAI: Chance 40, Distance > 250, Cooldown 4s) ---');

const est = cal.arquetipos.escudero_celestial.estocada;
comprobar('los cuatro de mele la tienen, el arquero no',
  ['escudero_celestial','portador_del_estandarte','elite_pesado','lancero_del_alba']
    .every(k => cal.arquetipos[k].estocada) && !cal.arquetipos.arquero_del_firmamento.estocada);

// La regla de verdad: NUNCA arranca por debajo de la puerta de distancia.
// (Que no se vea empezando a 150 no vale como prueba: el retroceso de los golpes
// y las esquivas de Malakh separan a los dos, y ahi la estocada es legitima.)
{
  const puerta = cal.arquetipos.escudero_celestial.distanciaDecision;
  let arranques = 0, ilegales = 0;
  for (let s = 1; s <= 40; s++) {
    const sim = banco(150, s);
    let dentro = false;
    for (let i = 0; i < 600 && !sim.terminada; i++) {
      sim.paso();
      const E = sim.enemigos[0];
      const e = !!E.accion?.esEstocada;
      if (e && !dentro) {
        arranques++;
        const d = Math.hypot(E.pos.x - sim.malakh.pos.x, E.pos.y - sim.malakh.pos.y) - sim.malakh.radio;
        if (d <= puerta) ilegales++;
      }
      dentro = e;
    }
  }
  comprobar(`nunca arranca por debajo de ${puerta} cm`, ilegales === 0,
    `${arranques} arranques, ${ilegales} ilegales`);
}

// De lejos SI, y cierra la distancia.
{
  let usos = 0, cerro = 0;
  for (let s = 1; s <= 40; s++) {
    const sim = banco(400, s);
    let d0 = null;
    for (let i = 0; i < 400 && !sim.terminada; i++) {
      sim.paso();
      const E = sim.enemigos[0];
      if (E.accion?.esEstocada && d0 === null) {
        d0 = Math.hypot(E.pos.x - sim.malakh.pos.x, E.pos.y - sim.malakh.pos.y);
        usos++;
      } else if (d0 !== null && !E.accion?.esEstocada) {
        const d1 = Math.hypot(E.pos.x - sim.malakh.pos.x, E.pos.y - sim.malakh.pos.y);
        if (d1 < d0 - 100) cerro++;
        d0 = null;
      }
    }
  }
  comprobar('de lejos (400 cm) si la usa', usos > 0, `${usos} veces en 40 partidas`);
  comprobar('y cierra la distancia de verdad', cerro > 0, `${cerro} de ${usos} acercaron mas de 100 cm`);
}

// El enfriamiento: no puede encadenarlas.
{
  const sim = banco(400, 3);
  const momentos = [];
  let dentro = false;
  for (let i = 0; i < 1200 && !sim.terminada; i++) {
    sim.paso();
    const e = !!sim.enemigos[0].accion?.esEstocada;
    if (e && !dentro) momentos.push(sim.t);
    dentro = e;
  }
  const huecos = momentos.slice(1).map((t, i) => t - momentos[i]);
  comprobar('respeta el enfriamiento de 4 s',
    huecos.every(h => h >= est.enfriamiento - 0.05),
    huecos.length ? `huecos: ${huecos.map(h => h.toFixed(1)).join(', ')}` : 'solo una estocada');
}

// Determinismo: la tirada del 40% sale del Azar sembrado.
{
  const a = banco(400, 11), b = banco(400, 11);
  for (let i = 0; i < 400; i++) { a.paso(); b.paso(); }
  comprobar('misma semilla, misma partida',
    Math.abs(a.enemigos[0].pos.x - b.enemigos[0].pos.x) < 1e-9 && a.malakh.hp === b.malakh.hp);
}

console.log(fallos ? `\n${fallos} fallos` : '\nsin fallos');
process.exit(fallos ? 1 : 0);
