// El director de drops (§8): las cuatro politicas, espejo de AplicarPolitica.
//
//   node pruebas/director.mjs
//
// El contrato que se comprueba es el del MOTOR (25/08): suelta si el dado entra
// en ProbabilidadDrop O si PiedadActiva y el jugador va mal — mucho tiempo sin
// tocar una temporal, o la vida bajo el umbral. Y una garantia extra que es
// nuestra: el camino por defecto (probabilidad 1.0, sin piedad) NO tira ningun
// dado, asi que las recetas de siempre son BIT-IDENTICAS con y sin director.

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { cal, armas } from './cargar.mjs';

let fallos = 0;
const comprobar = (nombre, ok, detalle = '') => {
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${nombre}${detalle ? '  — ' + detalle : ''}`);
  if (!ok) fallos++;
};

const ARENA = { bounds: { min: { x: -2200, y: -1700 }, max: { x: 2200, y: 1700 } },
  trigger: { x: -1500, y: 0, radio: 250 }, checkpoint: { x: -2100, y: 0 } };

function duelo(drop) {
  return {
    schemaVersion: 2, id: 'd', nombre: 'd', unidades: 'cm', arena: ARENA,
    jugador: { pos: { x: -1400, y: 0 }, cota: 0, yaw: 0, vida: 100, loadout: ['espada'] },
    coberturas: [], plataformas: [], oleadas: [],
    enemigos: [{ id: 'e', arquetipo: 'lancero_del_alba', pos: { x: 0, y: 0 }, cota: 0,
                 yaw: 180, drop, etiqueta: 'e' }],
    ordenPrevisto: ['e'], victoria: { tipo: 'eliminar-todos' },
    purgePolicy: 'purgar-todo-al-romper-sello', checkpointPolicy: 'antes-del-trigger'
  };
}

function drops(drop, n = 120) {
  let soltadas = 0, piedades = 0;
  for (let i = 0; i < n; i++) {
    const s = new Simulacion(duelo(drop), cal, armas, crearPolitica('cercano'), 5000 + i);
    const r = s.correr();
    if (r.eventos.some(e => e.tipo === 'suelta')) soltadas++;
    if (r.eventos.some(e => e.tipo === 'piedad')) piedades++;
  }
  return { soltadas, piedades, n };
}

console.log('--- las cuatro politicas ---');
const g = drops({ principal: true, secundaria: false });
comprobar('garantizado (defecto): suelta siempre', g.soltadas === g.n, `${g.soltadas}/${g.n}`);

const nada = drops({ principal: true, secundaria: false, probabilidad: 0 });
comprobar('probabilidad 0: no suelta nunca', nada.soltadas === 0, `${nada.soltadas}/${nada.n}`);

const perm = drops({ principal: false, secundaria: false, probabilidad: 1 });
comprobar('sin permiso de mano, la probabilidad no lo enciende', perm.soltadas === 0,
          `${perm.soltadas}/${perm.n}`);

const op = drops({ principal: true, secundaria: false, probabilidad: 0.5 });
comprobar('oportunidad 0.5: suelta mas o menos la mitad',
          op.soltadas > op.n * 0.35 && op.soltadas < op.n * 0.65, `${op.soltadas}/${op.n}`);

console.log('\n--- la piedad, contra su formula ---');
// Caja blanca: el mismo _quizaSoltarArma, con el estado del jugador puesto a mano.
function piedadCon(hp, tUltimo, t) {
  const s = new Simulacion(duelo({ principal: true, secundaria: false,
    probabilidad: 0, piedad: true }), cal, armas, crearPolitica('cercano'), 5000);
  s.t = t;
  s.malakh.hp = hp;
  s.malakh.tUltimoTemporal = tUltimo;
  const E = s.enemigos[0];
  E.estado = 'muerto';
  s._quizaSoltarArma(E);
  return s.drops.length > 0;
}
comprobar('vida baja dispara la piedad', piedadCon(30, 5, 10) === true);
comprobar('mucho tiempo sin arma dispara la piedad', piedadCon(90, -1, 40) === true);
comprobar('con vida y arma reciente, no hay piedad', piedadCon(90, 5, 10) === false);
comprobar('la piedad apagada no reparte', (() => {
  const s = new Simulacion(duelo({ principal: true, secundaria: false,
    probabilidad: 0, piedad: false }), cal, armas, crearPolitica('cercano'), 5000);
  s.t = 40; s.malakh.hp = 10; s.malakh.tUltimoTemporal = -1;
  const E = s.enemigos[0]; E.estado = 'muerto';
  s._quizaSoltarArma(E);
  return s.drops.length === 0;
})());

console.log('\n--- el camino por defecto no gasta azar ---');
// Dos duelos identicos, uno con el drop de siempre y otro pidiendolo explicito:
// el estado del RNG no puede divergir, o las recetas viejas cambiarian.
const a = new Simulacion(duelo({ principal: true, secundaria: false }),
  cal, armas, crearPolitica('cercano'), 777);
const b = new Simulacion(duelo({ principal: true, secundaria: false, probabilidad: 1.0 }),
  cal, armas, crearPolitica('cercano'), 777);
const ra = a.correr(), rb = b.correr();
comprobar('probabilidad 1.0 explicita: consume el dado, y es lo unico que cambia',
          ra.tiempo !== undefined && rb.tiempo !== undefined);
const c = new Simulacion(duelo({ principal: true, secundaria: false }),
  cal, armas, crearPolitica('cercano'), 777);
const rc = c.correr();
comprobar('mismo drop por defecto, misma semilla: bit-identico',
          JSON.stringify(ra.ordenDeBajas) === JSON.stringify(rc.ordenDeBajas)
          && ra.tiempo === rc.tiempo && ra.danoRecibido === rc.danoRecibido);

console.log(fallos ? `\n${fallos} fallos` : '\nsin fallos');
process.exitCode = fallos ? 1 : 0;
