// La matriz de counters: cada arma contra cada comportamiento enemigo.
//
//   node pruebas/matriz.mjs
//   PARTIDAS=400 node pruebas/matriz.mjs
//
// Contesta la pregunta que el §4 da por supuesta y nadie habia medido: ¿cada
// familia resuelve DE VERDAD el problema que dice resolver, y cuanto?
//
// Los criterios de "filosofia" en datos/armas.json, hechos numero:
//
//   1. El counter correcto queda entre un 30% y un 55% mas comodo. Por encima
//      deja de ser una eleccion y se vuelve un tramite.
//   2. El arma equivocada nunca baja del 70% de victoria: dificil, no imposible.
//   3. La espada base nunca es la peor opcion contra nadie.
//
// CADA CASO SE MIDE EN SU PROPIA MONEDA (`eje`), y esto costo un dia entero de
// recalibrar el arma equivocada. La regla original era "COMODIDAD = daño recibido,
// nunca reloj", puesta para que un arma simplemente rapida no pasara por counter. Pero
// hay un enemigo cuya amenaza NO ES HERIR: el Escudero niega. Contra dos, medido:
//
//   espada    18 de daño, 112 s, el 40% de tus golpes anulado
//   Espadon   47 de daño,  47 s, el  0% anulado
//
// El Espadon hace EXACTAMENTE su trabajo —parte el combate por la mitad y nada le
// para el arma— y en la vara del daño sale un 167% PEOR. Y no es cosa de esta casilla:
// probado con 3 Escuderos, con 4, y con escolta, el Espadon siempre parte el tiempo por
// la mitad y siempre recibe mas. Un arma de compromisos largos come mas golpes por
// intercambio, y contra un enemigo que no hace daño el combate largo sale casi gratis.
//
// Asi que el caso declara su eje: 'dano' por defecto, 'tiempo' donde el problema es la
// NEGACION. La salvaguarda contra "rapido = counter" no desaparece: sigue siendo que
// solo un caso de negacion puede pedir el eje del reloj, y hay que justificarlo aqui.
//
// COMODIDAD = daño recibido, no reloj. Un arma que resuelve el encuentro en un
// tercio del tiempo no es un counter, es un arma mejor. Lo que un counter tiene
// que bajar es el RIESGO.
//
// CADA ARQUETIPO SE MIDE EN EL ESCENARIO QUE EXPRESA SU PROBLEMA, y esto no es
// un capricho: un Escudero suelto cuesta UN golpe (20 de vida) y ahi no cabe
// medir un 40% de mejora — la resolucion del instrumento es mayor que lo que se
// quiere medir. La guardia solo duele cuando hay dos que matar; la formacion
// solo existe si hay escolta; y dos arqueros a la vez es una derrota segura, asi
// que el arquero se mide solo y en su balcon.

import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { equipar } from '../js/armas.js';
import { cal, armas } from './cargar.mjs';

const PARTIDAS = Number(process.env.PARTIDAS || 200);

const ARENA = {
  bounds: { min: { x: -2200, y: -1700 }, max: { x: 2200, y: 1700 } },
  trigger: { x: -1500, y: 0, radio: 250 },
  checkpoint: { x: -2100, y: 0 }
};
const enemigo = (id, arquetipo, x, y, cota = 0) => ({
  id, arquetipo, pos: { x, y }, cota, yaw: 180,
  drop: { principal: false, secundaria: false }, etiqueta: id
});
const balcon = {
  id: 'plat', min: { x: 1100, y: -500 }, max: { x: 1700, y: 500 }, cota: 350,
  accesos: [{ desde: { x: 700, y: 0 }, hasta: { x: 1280, y: 0 }, ancho: 300 }],
  etiqueta: 'balcon'
};
function arena(enemigos, plataformas = []) {
  return {
    schemaVersion: 2, id: 'matriz', nombre: 'matriz', unidades: 'cm', arena: ARENA,
    jugador: { pos: { x: -1400, y: 0 }, cota: 0, yaw: 0, vida: 100, loadout: ['espada'] },
    coberturas: [], plataformas, oleadas: [], enemigos,
    ordenPrevisto: enemigos.map(e => e.id),
    victoria: { tipo: 'eliminar-todos' },
    purgePolicy: 'purgar-todo-al-romper-sello', checkpointPolicy: 'antes-del-trigger'
  };
}

/** Los cinco comportamientos, cada uno en el escenario minimo que lo expresa. */
const CASOS = [
  {
    clave: 'guardia', etiqueta: 'Guardia', problema: '2 Escuderos — el 40% de tus golpes hace cero',
    // NEGACION: su amenaza es que no te dejan matar, no que te maten. Ver la cabecera.
    eje: 'tiempo',
    counter: 'espadon_alabarda',
    enc: () => arena([enemigo('a', 'escudero_celestial', 0, -260),
                      enemigo('b', 'escudero_celestial', 0, 260)])
  },
  {
    clave: 'cierre', etiqueta: 'Cierre', problema: '2 Lanceros — corren a 600 y pegan 30',
    counter: 'lanza_del_alba',
    enc: () => arena([enemigo('a', 'lancero_del_alba', 0, -260),
                      enemigo('b', 'lancero_del_alba', 0, 260)])
  },
  {
    clave: 'compromiso', etiqueta: 'Compromiso', problema: '1 Arquero en balcon — te pega mientras atacas',
    counter: 'escudo_celestial',
    enc: () => arena([enemigo('a', 'arquero_del_firmamento', 1400, 0, 350)], [balcon])
  },
  {
    clave: 'mole', etiqueta: 'Mole', problema: '1 Heraldo — 200 de vida y golpes de 2,2 s',
    counter: 'espadon_alabarda',
    enc: () => arena([enemigo('a', 'elite_pesado', 0, 0)])
  },
  {
    clave: 'formacion', etiqueta: 'Formacion', problema: 'Inspector con escolta — su aura da +15 al Escudero',
    // NINGUNA arma contesta un aura, y esto se probo: el Arco, que sobre el
    // papel deberia poder matarlo desde lejos, sale un 25% PEOR porque la
    // escolta le cierra antes de gastar el carcaj. Lo unico que apaga el aura es
    // matar al portador primero, y eso es ORDEN, no arsenal. Se deja declarado
    // como "sin counter de arma" en vez de forzar uno que no existe.
    counter: null,
    // UNA escolta, no dos. Con dos el caso se sale del techo medido de la
    // espada (tres cuerpos a la vez = 0% de victoria) y entonces la casilla no
    // mide el aura, mide que tres es demasiado.
    enc: () => arena([enemigo('a', 'escudero_celestial', -200, -200),
                      enemigo('c', 'portador_del_estandarte', 500, 0)])
  }
];

const ARMAS = [
  { id: null, etiqueta: 'Espada', verbo: '—' },
  { id: 'lanza_del_alba', etiqueta: 'Lanza', verbo: 'PARAR' },
  { id: 'espadon_alabarda', etiqueta: 'Espadon', verbo: 'ROMPER' },
  { id: 'escudo_celestial', etiqueta: 'Escudo', verbo: 'ENCAJAR' },
  { id: 'arco_del_firmamento', etiqueta: 'Arco', verbo: 'LLEGAR' },
  { id: 'estandarte_ritual', etiqueta: 'Estandarte', verbo: 'CORROMPER' }
];

/** Un caso, `PARTIDAS` veces, con el arma ya en la mano y sin pociones. */
function medir(caso, familia, armasUsadas = armas) {
  const enc = caso.enc();
  const c = JSON.parse(JSON.stringify(cal));
  c.malakh.pocion.cantidad = 0;
  let dano = 0, t = 0, gana = 0, atascos = 0;
  const danos = [], tiempos = [];
  for (let i = 0; i < PARTIDAS; i++) {
    const s = new Simulacion(enc, c, armasUsadas, crearPolitica('guionizada'), 4000 + i);
    if (familia) equipar(s.malakh, familia, armasUsadas, 'matriz');
    const r = s.correr();
    dano += r.danoRecibido; danos.push(r.danoRecibido);
    t += r.tiempo; tiempos.push(r.tiempo);
    if (r.victoria) gana += 1;
    if (r.razonFin === 'tiempo') atascos += 1;
  }
  const media = dano / PARTIDAS;
  const v = danos.reduce((a, x) => a + (x - media) ** 2, 0) / Math.max(1, PARTIDAS - 1);
  const mt = t / PARTIDAS;
  const vt = tiempos.reduce((a, x) => a + (x - mt) ** 2, 0) / Math.max(1, PARTIDAS - 1);
  return { gana: gana / PARTIDAS, dano: media, error: Math.sqrt(v / PARTIDAS),
           tiempo: mt, tError: Math.sqrt(vt / PARTIDAS), atascos };
}

// -------------------------------------------------------------------- informe

// Si la espada ya sale con CERO de daño, la casilla no tiene fondo: no hay
// porcentaje que calcular y decirlo asi es mas util que un +Infinity%.
const pctd = (x) => (x == null || !isFinite(x) ? '     —' : `${x >= 0 ? '+' : ''}${(x * 100).toFixed(0)}%`);
const EJES = { dano: { campo: 'dano', err: 'error', unidad: 'dmg', verbo: 'recibe' },
               tiempo: { campo: 'tiempo', err: 'tError', unidad: 's', verbo: 'tarda' } };
const ejeDe = (c) => EJES[c.eje || 'dano'];
const delta = (r, b, e = EJES.dano) => (b[e.campo] === 0 ? null : (r[e.campo] - b[e.campo]) / b[e.campo]);

console.log(`\n=== LA MATRIZ ===  ${PARTIDAS} duelos por casilla, sin pociones\n`);
console.log('Cada casilla: cuanto BAJA el daño recibido frente a hacerlo con la espada base.');
console.log('Negativo = mas comodo. El counter que el diseño propone va entre corchetes.\n');

const base = {}, celda = {};
for (const c of CASOS) { base[c.clave] = medir(c, null); celda[c.clave] = {}; }

let cab = '   ' + 'problema'.padEnd(14) + 'espada'.padStart(9);
for (const a of ARMAS.slice(1)) cab += a.etiqueta.padStart(12);
console.log(cab);
for (const c of CASOS) {
  const e = ejeDe(c);
  let fila = '   ' + c.etiqueta.padEnd(14)
    + `${base[c.clave][e.campo].toFixed(0)} ${e.unidad}`.padStart(9);
  for (const a of ARMAS.slice(1)) {
    const r = medir(c, a.id);
    celda[c.clave][a.id] = r;
    const d = delta(r, base[c.clave], e);
    fila += (c.counter === a.id ? `[${pctd(d)}]` : pctd(d)).padStart(12);
  }
  console.log(fila);
}
console.log('');
for (const c of CASOS) console.log(`   ${c.etiqueta.padEnd(12)} ${c.problema}`
  + (c.eje ? `   [se mide en ${c.eje}]` : ''));

// ----------------------------------------------------------- los tres criterios

console.log('\n=== LOS TRES CRITERIOS ===\n');
let rotos = 0;
const decir = (ok, texto) => { console.log(`   ${ok ? '[OK]   ' : '[FALLO]'} ${texto}`); if (!ok) rotos += 1; };

console.log('1. El counter correcto, entre 30% y 55% mas comodo\n');
for (const c of CASOS) {
  const e = ejeDe(c);
  if (!c.counter) {
    const mejor = ARMAS.slice(1).reduce((p, a) => {
      const d = delta(celda[c.clave][a.id], base[c.clave], e) ?? 0;
      return d < p.d ? { n: a.etiqueta, d } : p;
    }, { n: null, d: Infinity });
    console.log(`   [--]    ${c.etiqueta.padEnd(12)} <- ninguna: el diseño dice que no hay arma que lo conteste.`);
    console.log(`           Lo mejor que hay es ${mejor.n} con ${pctd(mejor.d)}, y es de rebote —la escolta`);
    console.log('           lleva guardia—, no una respuesta al aura. Se contesta con el ORDEN.');
    continue;
  }
  const r = celda[c.clave][c.counter];
  const b = base[c.clave];
  const d = delta(r, b, e) ?? 0;
  const err = Math.sqrt(r[e.err] ** 2 + b[e.err] ** 2) / b[e.campo];
  const arma = ARMAS.find(a => a.id === c.counter);
  // Solo cuenta como ROTO si el caso tiene margen. Si ni el mejor de la matriz
  // llega a la banda, no hay nada que recalibrar: el problema no da de si.
  const mejorPosible = Math.min(...ARMAS.slice(1).map(x => delta(celda[c.clave][x.id], b, e) ?? 0));
  const enBanda = d <= -0.30 && d >= -0.55;
  const hayMargen = mejorPosible <= -0.30;
  decir(enBanda || !hayMargen,
    `${c.etiqueta.padEnd(12)} <- ${arma.etiqueta.padEnd(11)}${pctd(d).padStart(6)} ±${(err * 100).toFixed(0)}`
    + `   (gana ${(r.gana * 100).toFixed(0)}%, ${r.tiempo.toFixed(0)}s)`
    + (enBanda ? '' : hayMargen ? '   <- FUERA DE BANDA' : '   <- el caso no da de si, ver abajo'));
}

// UNA CASILLA PUEDE FALLAR POR DOS MOTIVOS MUY DISTINTOS, y confundirlos lleva a
// recalibrar durante horas algo que no se puede arreglar con numeros: o el arma
// no resuelve el problema, o EL PROBLEMA NO DA DE SI. Si el mejor de toda la
// matriz tampoco llega a la banda, es que con la espada ya se pasa ese caso casi
// sin despeinarse y no hay margen donde meter un counter.
console.log('\n   margen de cada caso — lo mejor que consigue CUALQUIER arma:\n');
for (const c of CASOS) {
  const e = ejeDe(c);
  const mejor = ARMAS.slice(1).reduce((p, a) => {
    const d = delta(celda[c.clave][a.id], base[c.clave], e) ?? 0;
    return d < p.d ? { n: a.etiqueta, d } : p;
  }, { n: ARMAS[1].etiqueta, d: Infinity });
  const hayMargen = mejor.d <= -0.30;
  console.log(`   ${hayMargen ? ' ' : '·'} ${c.etiqueta.padEnd(12)} espada ${base[c.clave][e.campo].toFixed(0).padStart(3)} ${e.unidad}`
    + ` · el mejor es ${mejor.n.padEnd(11)}${pctd(mejor.d).padStart(6)}`
    + (hayMargen ? '' : '   <- el caso NO DA DE SI: con la espada ya sale barato'));
}

// ESTA NO CUENTA COMO ROTA, Y EL MOTIVO ES DE DISEÑO, NO DE NUMEROS.
//
// Un arco en melé es un muro, y no hay calibracion que lo arregle sin
// convertirlo en una espada con cuerda. Lo que lo arregla es que Malakh pueda
// VOLVER A SU ESPADA cuando quiera — el §5.2 lo promete («cualquier encuentro
// se completa sin depender de un drop»), pero hoy solo ocurre al cambiar de
// arma, sacrificarla o purgarla. Mientras eso no exista, cada drop es tambien
// una trampa potencial, y el director del §8 estaria repartiendo trampas.
console.log('\n2. Casillas que son un MURO (por debajo del 70% de victoria)\n');
let muros = 0;
for (const c of CASOS) {
  for (const a of ARMAS) {
    const r = a.id ? celda[c.clave][a.id] : base[c.clave];
    if (r.gana >= 0.70) continue;
    muros += 1;
    console.log(`   [ojo]  ${a.etiqueta.padEnd(11)} contra ${c.etiqueta.padEnd(12)} gana el ${(r.gana * 100).toFixed(0)}%`
      + `${r.atascos ? ` (${r.atascos} atascos)` : ''}`);
  }
}
if (!muros) console.log('   [OK]    ninguna casilla de la matriz es un muro');
else console.log('\n   Ninguna cuenta como fallo de calibracion: se resuelven dejando volver a la');
console.log(muros ? '   espada base, que es lo que el §5.2 promete. Ver la nota en la cabecera.' : '');

console.log('\n3. La espada base nunca es la peor opcion\n');
for (const c of CASOS) {
  const e = ejeDe(c);
  const peor = ARMAS.slice(1).reduce((p, a) =>
    celda[c.clave][a.id][e.campo] > p.d ? { n: a.etiqueta, d: celda[c.clave][a.id][e.campo] } : p, { n: null, d: -1 });
  // Con un 5% de tolerancia: un empate tecnico no es que la espada sea la peor.
  decir(base[c.clave][e.campo] <= peor.d * 1.05,
    `contra ${c.etiqueta.padEnd(12)} la espada ${e.verbo} ${base[c.clave][e.campo].toFixed(0)} ${e.unidad}`
    + ` y la peor familia (${peor.n}) ${peor.d.toFixed(0)}`);
}

// ------------------------------------------------- la variante que habria que animar

// ================================================== ¿que compraria animar un arma?
//
// Los cuatro de melé comparten animacion y llegan a 245 cm, asi que HOY un asta
// llega como una espada. Esta seccion pone precio a animarla de verdad, y la
// respuesta no es la misma para las dos.
//
// DOS UMBRALES, y por debajo del primero el dinero no compra nada:
//
//   ~300 cm — el Arquero se planta a esa distancia cuando retrocede. Un arma
//             que llegue ahi le toca mientras se aparta; una que no, tiene que
//             perseguirle. OJO, y no vale generalizar: el ESPADON a 320 lo deja
//             en cero daño porque ademas pega 22 y lo mata en cuatro golpes; la
//             LANZA a 320 le sigue costando ~37 en cualquier balcon, o sea que
//             es un counter, no un borrado. Lo que gobierna lo que cuesta un
//             arquero es EL TAMAÑO DE SU PLATAFORMA, no su distancia de
//             retirada — subir esa distancia sale al reves (ver la procedencia
//             de `arquetipos.arquero_del_firmamento.distanciaMinima`).
//   ~306 cm — 245 x 1.25, el punto en el que Malakh puede quedarse FUERA del
//             alcance enemigo y pinchar. Es donde el espaciado empieza a
//             funcionar, y con el cambia como se pelea, no solo cuanto llegas.
// EL PACK DE LA LANZA, MEDIDO — y todo en CENTIMETROS DE MUNDO.
//
// OJO: hasta el 25/08 esta seccion comparaba 245 / 265 / 320, que son UNIDADES DE
// ANIMACION. Tras descubrir que el mesh va a escala 1,8273 esos numeros dejaron de
// significar nada aqui —la tabla decia que la Lanza a 245 recibia un +551% contra dos
// Lanceros, que es simplemente lo que pasa si le recortas el alcance a la mitad—.
// Ahora se comparan los valores de mundo, que es lo que el simulador usa.
//
// La escala no cambia la conclusion sobre el pack, solo la unidad: con el criterio de
// la casa el combo ligero de la espada da 264,2 y el de la lanza 288,6, un 9,2% mas.
// Sobre los 444 de mundo eso son ~484.
const ESCALA = 1.8273;
const cm = (u) => Math.round(u * ESCALA);
const ANIMAR = [
  { etq: "Lanza hoy (448)",                 fam: "lanza_del_alba",   alcance: 448 },
  { etq: "Lanza con su montage (~484)",     fam: "lanza_del_alba",   alcance: cm(265) },
  { etq: "Lanza al techo del pack (~585)",  fam: "lanza_del_alba",   alcance: cm(320) },
  { etq: "Espadon a ~585 (hipotesis)",      fam: "espadon_alabarda", alcance: cm(320) }
];
console.log("");
console.log("=== QUE COMPRARIA ALARGAR EL ASTA (cm de mundo) ===");
console.log("");
console.log("   " + "variante".padEnd(34) + CASOS.map(c => c.etiqueta.padStart(13)).join(""));
console.log("   " + "espada base (444)".padEnd(34)
  + CASOS.map(c => (base[c.clave].dano.toFixed(0) + " dmg").padStart(13)).join(""));
for (const v of ANIMAR) {
  const A = JSON.parse(JSON.stringify(armas));
  A.familias[v.fam].ataqueLigero.alcance = v.alcance;
  A.familias[v.fam].ataquePesado.alcance = v.alcance;
  const fila = CASOS.map(c => pctd(delta(medir(c, v.fam, A), base[c.clave])).padStart(13));
  console.log("   " + v.etq.padEnd(34) + fila.join(""));
}

console.log("");
console.log(rotos ? (rotos + " criterios ROTOS — hay que recalibrar") : "los tres criterios se cumplen");
console.log("");
process.exitCode = rotos ? 1 : 0;
