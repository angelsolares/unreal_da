// Activacion escalonada (§6): que las oleadas hagan lo que dicen que hacen.
//
//   node pruebas/oleadas.mjs
//
// Son las comprobaciones que un lote no enseña: que un encuentro SIN oleadas se
// comporta exactamente como antes de que esto existiera, que un enemigo dormido
// no pelea pero cuenta para la victoria, que la alerta no cruza oleadas, y que
// una oleada imposible se caza en seco en vez de gastar 200 partidas en
// descubrir que la arena no se cierra nunca.

import { Simulacion, ESTADOS } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { validar, oleadasDe, enemigosPresentesAlEntrar } from '../js/esquema.js';
import { cal, armas, encuentro } from './cargar.mjs';

let fallos = 0;
const comprobar = (nombre, condicion, detalle = '') => {
  console.log(`   ${condicion ? '[OK]   ' : '[FALLO]'} ${nombre}${detalle ? '  — ' + detalle : ''}`);
  if (!condicion) fallos += 1;
};

const arena = {
  bounds: { min: { x: -2000, y: -2000 }, max: { x: 2000, y: 2000 } },
  trigger: { x: -1500, y: 0, radio: 200 },
  checkpoint: { x: -1900, y: 0 }
};
const enemigo = (id, x, y, oleada) => ({
  id, arquetipo: 'escudero_celestial', pos: { x, y }, cota: 0, yaw: 180,
  drop: { principal: false, secundaria: false }, oleada, etiqueta: id
});

function base(enemigos, oleadas) {
  return {
    schemaVersion: 2, id: 'prueba', nombre: 'prueba', unidades: 'cm', arena,
    jugador: { pos: { x: -1200, y: 0 }, cota: 0, yaw: 0, vida: 100, loadout: ['espada'] },
    coberturas: [], plataformas: [], enemigos, oleadas, ordenPrevisto: [],
    victoria: { tipo: 'eliminar-todos' }, purgePolicy: 'purgar-todo-al-romper-sello',
    checkpointPolicy: 'antes-del-trigger'
  };
}
const correr = (enc, semilla = 7) =>
  new Simulacion(enc, cal, armas, crearPolitica('cercano'), semilla).correr();

// ------------------------------------------------------- 1. sin oleadas, nada cambia
console.log('\n--- sin oleadas declaradas, todo sigue como antes ---');
{
  const enc = base([enemigo('a', -400, -200), enemigo('b', -400, 200)], []);
  const olas = oleadasDe(enc);
  comprobar('una sola oleada implicita con todo el mundo dentro',
    olas.length === 1 && olas[0].implicita && olas[0].enemigos.length === 2);
  const sim = new Simulacion(enc, cal, armas, crearPolitica('cercano'), 7);
  comprobar('los dos arrancan activos', sim.enemigos.every(e => e.activo));
  comprobar('pero NINGUNO arranca alertado: siguen despertando por su rangoAggro',
    sim.enemigos.every(e => !e.alertado));
  comprobar('el resultado no menciona oleadas', correr(enc).oleadas.length === 0);
}

// ------------------------------------------- 2. el que espera ni pelea ni sobra
console.log('\n--- un enemigo que espera su oleada ---');
{
  const enc = base(
    [enemigo('a', -400, 0, 'ola_1'), enemigo('b', 400, 0, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'oleadaLimpia', oleada: 'ola_1' }, retardo: 2, presencia: 'en-escena' }]);

  const sim = new Simulacion(enc, cal, armas, crearPolitica('cercano'), 7);
  comprobar('el de la ola 2 arranca inactivo', !sim.enemigos.find(e => e.id === 'b').activo);
  comprobar('pero PRESENTE: esta plantado en la arena y se lee desde la puerta',
    sim.enemigos.find(e => e.id === 'b').presente && enemigosPresentesAlEntrar(enc).length === 2);

  const partida = new Simulacion(enc, cal, armas, crearPolitica('cercano'), 7);
  const sitio = { ...partida.enemigos.find(e => e.id === 'b').pos };
  while (!partida.terminada && partida.enemigos.find(e => e.id === 'a').estado !== ESTADOS.MUERTO) {
    partida.paso();
  }
  const b = partida.enemigos.find(e => e.id === 'b');
  comprobar('mientras espera no se ha movido ni un centimetro',
    b.pos.x === sitio.x && b.pos.y === sitio.y);
  comprobar('la alerta del compañero no le ha despertado', !b.alertado);

  const r = correr(enc);
  comprobar('la partida no acaba hasta que caen los dos', r.victoria && r.ordenDeBajas.length === 2);
  comprobar('la ola 2 consta como activada, con su instante',
    r.oleadas.length === 2 && r.oleadas[1].activada && r.oleadas[1].t > 0);
  comprobar('y deja evento para el log de combate',
    r.eventos.some(e => e.tipo === 'oleada' && e.oleada === 'ola_2'));
}

// ------------------------------------------- 3. al que le pegas, despierta el
console.log('\n--- pegarle a uno que duerme le despierta a el, no a su oleada ---');
{
  const enc = base(
    [enemigo('a', -400, 0, 'ola_1'), enemigo('b', 600, -100, 'ola_2'), enemigo('c', 600, 100, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'tiempo', segundos: 900 }, retardo: 0, presencia: 'en-escena' }]);
  const sim = new Simulacion(enc, cal, armas, crearPolitica('cercano'), 7);
  const b = sim.enemigos.find(e => e.id === 'b');
  const c = sim.enemigos.find(e => e.id === 'c');
  sim._aplicarDano(b, 5, sim.malakh, {});
  comprobar('el golpeado se activa', b.activo && b.alertado);
  comprobar('su compañero de oleada sigue durmiendo', !c.activo);
  comprobar('y queda dicho en el log',
    sim.eventos.some(e => e.tipo === 'despierta' && e.agente === 'b'));
}

// ---------------------------------------------------- 4. las formas de activarse
console.log('\n--- las condiciones de activacion ---');
{
  const porTiempo = base(
    [enemigo('a', -400, 0, 'ola_1'), enemigo('b', 900, 0, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'tiempo', segundos: 5 }, retardo: 0, presencia: 'en-escena' }]);
  const s1 = new Simulacion(porTiempo, cal, armas, crearPolitica('cercano'), 7);
  while (s1.t < 4.9) s1.paso();
  const antes = s1.oleadas[1].activada;
  while (s1.t < 5.2 && !s1.terminada) s1.paso();
  comprobar('`tiempo` entra en su segundo', !antes && s1.oleadas[1].activada, `t=${s1.t.toFixed(2)}`);

  const porBajas = base(
    [enemigo('a', -400, -100, 'ola_1'), enemigo('b', -400, 100, 'ola_1'), enemigo('c', 900, 0, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'bajas', cuantas: 1 }, retardo: 0, presencia: 'en-escena' }]);
  const r2 = correr(porBajas);
  const tBaja = r2.ordenDeBajas[0].t;
  const tOla = r2.oleadas.find(o => o.id === 'ola_2').t;
  comprobar('`bajas` entra con la baja que le toca', Math.abs(tOla - tBaja) < 0.1,
    `baja ${tBaja}s, oleada ${tOla}s`);

  const conRetardo = base(
    [enemigo('a', -400, 0, 'ola_1'), enemigo('b', 900, 0, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'oleadaLimpia', oleada: 'ola_1' }, retardo: 6, presencia: 'en-escena' }]);
  const r3 = correr(conRetardo);
  const margen = r3.oleadas[1].t - r3.ordenDeBajas[0].t;
  comprobar('`retardo` se respeta', Math.abs(margen - 6) < 0.15, `${margen.toFixed(2)}s de margen`);
}

// ------------------------------------------------ 5. `entra` es una emboscada
console.log('\n--- una oleada que ENTRA no se lee desde la puerta, y se dice ---');
{
  const enc = base(
    [enemigo('a', -400, 0, 'ola_1'), enemigo('b', 900, 0, 'ola_2')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena' },
     { id: 'ola_2', activacion: { tipo: 'oleadaLimpia', oleada: 'ola_1' }, retardo: 0, presencia: 'entra' }]);
  comprobar('no cuenta entre los presentes al entrar', enemigosPresentesAlEntrar(enc).length === 1);
  const sim = new Simulacion(enc, cal, armas, crearPolitica('cercano'), 7);
  comprobar('no esta en la arena: no ocupa sitio ni recibe golpes',
    !sim.enemigos.find(e => e.id === 'b').presente && sim.enemigosEnEscena().length === 1);
  comprobar('pero cuenta como vivo, o la arena se abriria sola', sim.enemigosVivos().length === 2);
  comprobar('y la partida se cierra igual', correr(enc).victoria);
}

// ------------------------------------------- 6. los soft-locks, cazados en seco
console.log('\n--- validacion estatica ---');
{
  const codigos = (enc) => validar(enc).map(p => p.codigo);

  comprobar('una oleada que se espera a si misma',
    codigos(base([enemigo('a', -400, 0, 'ola_1')],
      [{ id: 'ola_1', activacion: { tipo: 'oleadaLimpia', oleada: 'ola_1' } }])).includes('oleada-referencia'));

  comprobar('ninguna oleada `inicio`: la arena se cierra y no pasa nada',
    codigos(base([enemigo('a', -400, 0, 'ola_1')],
      [{ id: 'ola_1', activacion: { tipo: 'tiempo', segundos: 5 } },
       { id: 'ola_2', activacion: { tipo: 'oleadaLimpia', oleada: 'ola_1' } }])).includes('oleada-inalcanzable'));

  comprobar('`bajas` por encima del censo: no llega nunca',
    codigos(base([enemigo('a', -400, 0, 'ola_1'), enemigo('b', 400, 0, 'ola_2')],
      [{ id: 'ola_1', activacion: { tipo: 'inicio' } },
       { id: 'ola_2', activacion: { tipo: 'bajas', cuantas: 2 } }])).includes('oleada-inalcanzable'));

  const huerfano = base([enemigo('a', -400, 0, 'ola_fantasma')],
    [{ id: 'ola_1', activacion: { tipo: 'inicio' } }]);
  comprobar('un enemigo asignado a una oleada que no existe',
    codigos(huerfano).includes('oleada-referencia'));
  comprobar('...y aun asi PELEA, en la primera: desaparecer en silencio es peor',
    oleadasDe(huerfano)[0].enemigos.length === 1);

  comprobar('una activacion que no esta en el vocabulario',
    codigos(base([enemigo('a', -400, 0, 'ola_1')],
      [{ id: 'ola_1', activacion: { tipo: 'cuando_me_apetezca' } }])).includes('enum-invalido'));
}

// ------------------------------------------------------- 7. la receta de verdad
console.log('\n--- "Romper la linea", el encuentro real ---');
{
  const enc = encuentro('romper-la-linea');
  const olas = oleadasDe(enc);
  const problemas = validar(enc);
  // Cinco desde el 25/08: con la esquiva medida en 532, dos cuerpos a la vez no se
  // ganan con espada sola, asi que la receta va de uno en uno.
  comprobar('cinco oleadas y cinco enemigos', olas.length === 5 && enc.enemigos.length === 5);
  comprobar('ninguna oleada trae mas de dos cuerpos', olas.every(o => o.enemigos.length <= 2),
    olas.map(o => o.enemigos.length).join('+'));
  comprobar('la validacion estatica esta limpia', problemas.length === 0,
    problemas.map(p => p.codigo).join(', '));
  const r = correr(enc, 1234);
  comprobar('y nunca hay mas de dos encima a la vez', r.maxEnemigosALaVez <= 2,
    `maximo ${r.maxEnemigosALaVez}`);
}

console.log(`\n${fallos ? `${fallos} comprobaciones ROTAS` : 'todo en orden'}\n`);
process.exitCode = fallos ? 1 : 0;
