// ¿Por que la Lanza del pack empeora un 84% contra el Arquero del balcon?
//
//   node pruebas/embestida.mjs
//
// Dos explicaciones posibles y muy distintas: (a) DISEÑO — embestir contra
// quien esta en alto es tirarse al descubierto, y esta bien que duela; o (b)
// ARTEFACTO — la puerta de ataque es plana e ignora la cota, asi que Malakh se
// planta debajo del balcon dando estocadas al aire. Se distinguen mirando si
// los golpes ATERRIZAN.
import { Simulacion } from '../js/sim.js';
import { crearPolitica } from '../js/politicas.js';
import { equipar } from '../js/armas.js';
import { cal, armas } from './cargar.mjs';

const PARTIDAS = Number(process.env.PARTIDAS || 400);
const balcon = { id: 'plat', min: { x: 1100, y: -500 }, max: { x: 1700, y: 500 }, cota: 350,
  accesos: [{ desde: { x: 700, y: 0 }, hasta: { x: 1280, y: 0 }, ancho: 300 }], etiqueta: 'balcon' };
const enc = () => ({
  schemaVersion: 2, id: 'x', nombre: 'x', unidades: 'cm',
  arena: { bounds: { min: { x: -2200, y: -1700 }, max: { x: 2200, y: 1700 } },
           trigger: { x: -1500, y: 0, radio: 250 }, checkpoint: { x: -2100, y: 0 } },
  jugador: { pos: { x: -1400, y: 0 }, cota: 0, yaw: 0, vida: 100, loadout: ['espada'] },
  coberturas: [], plataformas: [balcon], oleadas: [],
  enemigos: [{ id: 'a', arquetipo: 'arquero_del_firmamento', pos: { x: 1400, y: 0 }, cota: 350,
               yaw: 180, drop: { principal: false, secundaria: false }, etiqueta: 'a' }],
  ordenPrevisto: ['a'], victoria: { tipo: 'eliminar-todos' },
  purgePolicy: 'purgar-todo-al-romper-sello', checkpointPolicy: 'antes-del-trigger'
});

function medir(familia, mod) {
  const A = JSON.parse(JSON.stringify(armas));
  if (mod) mod(A.familias[familia]);
  const c = JSON.parse(JSON.stringify(cal)); c.malakh.pocion.cantidad = 0;
  let dano = 0, gana = 0, t = 0, tirados = 0, dados = 0, subio = 0;
  for (let i = 0; i < PARTIDAS; i++) {
    const s = new Simulacion(enc(), c, A, crearPolitica('guionizada'), 4000 + i);
    if (familia) equipar(s.malakh, familia, A, 'x');
    const r = s.correr();
    dano += r.danoRecibido; t += r.tiempo; if (r.victoria) gana += 1;
    const ev = s.eventos || [];
    tirados += ev.filter(e => e.tipo === 'ataque' && e.agente === s.malakh.id).length;
    dados += s.malakh.golpesAsestados || 0;
    if ((s.malakh.cota || 0) > 50) subio += 1;
  }
  return { dano: dano / PARTIDAS, gana: gana / PARTIDAS, t: t / PARTIDAS,
           tirados: tirados / PARTIDAS, dados: dados / PARTIDAS, subio: subio / PARTIDAS };
}

const filas = [
  ['espada base',            null,             null],
  ['Lanza hoy (245)',        'lanza_del_alba', null],
  ['Lanza pack, sin abrir',   'lanza_del_alba', f => { f.ataqueLigero.alcance = 224; f.ataqueLigero.embestida = 112;
                                                      f.ataquePesado.alcance = 221; f.ataquePesado.embestida = 296; }],
  ['Lanza pack, abre ataque',  'lanza_del_alba', f => { f.ataqueLigero.alcance = 224; f.ataqueLigero.embestida = 112;
                                                        f.ataqueLigero.embestidaAbreAtaque = true;
                                                        f.ataquePesado.alcance = 221; f.ataquePesado.embestida = 296;
                                                        f.ataquePesado.embestidaAbreAtaque = true; }],
  ['Lanza pack, solo pesado',  'lanza_del_alba', f => { f.ataqueLigero.alcance = 224;
                                                        f.ataquePesado.alcance = 221; f.ataquePesado.embestida = 296; }],
  ['Lanza 320 (hipotesis)',    'lanza_del_alba', f => { f.ataqueLigero.alcance = 320; f.ataquePesado.alcance = 320; }]
];
console.log('');
console.log('ARQUERO EN BALCON — ' + PARTIDAS + ' duelos');
console.log('');
console.log('   ' + 'variante'.padEnd(24) + 'dmg'.padStart(7) + 'gana'.padStart(7)
  + 'seg'.padStart(7) + 'tira'.padStart(7) + 'acierta'.padStart(9) + 'aciertos'.padStart(10) + 'sube'.padStart(7));
for (const [etq, fam, mod] of filas) {
  const r = medir(fam, mod);
  const pct = r.tirados ? (r.dados / r.tirados) : 0;
  console.log('   ' + etq.padEnd(24) + r.dano.toFixed(0).padStart(7)
    + (r.gana * 100).toFixed(0).padStart(6) + '%' + r.t.toFixed(0).padStart(7)
    + r.tirados.toFixed(1).padStart(7) + ((pct * 100).toFixed(0) + '%').padStart(9)
    + r.dados.toFixed(1).padStart(10) + ((r.subio * 100).toFixed(0) + '%').padStart(7));
}
console.log('');
console.log('   tira    = ataques lanzados por partida');
console.log('   acierta = de esos, cuantos aterrizan. Si se hunde, la puerta de ataque miente.');
console.log('   sube    = partidas que acabaron con Malakh EN el balcon.');
console.log('');
