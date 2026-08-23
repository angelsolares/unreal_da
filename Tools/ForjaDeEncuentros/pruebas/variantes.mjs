// La tuberia de la fase D, sin gastar una llamada.
//
// No puedo probar lo que devuelve OpenAI, pero SI todo lo que viene despues, que
// es lo que decide si una variante se enseña o no: expandir la propuesta, validar
// el encuentro y simularlo. Se le meten respuestas de mentira —incluidas las
// malas, que son las que rompen cosas— y se comprueba que la herramienta aguanta.
//
//   node pruebas/variantes.mjs

import { expandirPropuesta, ESQUEMA_PROPUESTA, resumirParaIA, hitosDeLaPartida } from '../js/esquema-ia.js';
import { validar } from '../js/esquema.js';
import { correrLote } from '../js/lote.js';
import { cal, armas, encuentro } from './cargar.mjs';

const base = encuentro();
let fallos = 0;
const comprobar = (nombre, ok, detalle = '') => {
  console.log(`   ${ok ? 'OK  ' : 'MAL '} ${nombre}${detalle ? '  — ' + detalle : ''}`);
  if (!ok) fallos++;
};

// --- 1. El resumen que se le manda al modelo ---
console.log('--- resumen para el modelo ---');
const lote = correrLote(base, cal, armas, { partidas: 40 });
const resumen = resumirParaIA(base, cal, lote);
const json = JSON.stringify(resumen);
comprobar('lleva el encuentro y el veredicto', !!resumen.encuentro && !!resumen.veredicto);
comprobar('no cuela eventos ni fotogramas', !json.includes('fotogramas') && !json.includes('"eventos"'));
comprobar('es compacto', json.length < 12000, `${(json.length / 1024).toFixed(1)} KB`);

// --- 2. Una propuesta buena ---
console.log('\n--- propuesta razonable ---');
const buena = {
  nombre: 'La rampa vigilada',
  queEnsena: 'Un enemigo secundario puede ser la llave del grupo.',
  porQueFunciona: 'Geometria: el pasillo obliga a pasar por delante del lancero.',
  enemigos: [
    { arquetipo: 'lancero_del_alba', x: -300, y: 0, cota: 0, drop: 'garantizado', etiqueta: 'guardia del paso' },
    { arquetipo: 'escudero_celestial', x: 500, y: -400, cota: 0, drop: 'estandar', etiqueta: 'flanco' },
    { arquetipo: 'arquero_del_firmamento', x: 1600, y: 600, cota: 350, drop: 'ninguno', etiqueta: 'balcon' }
  ],
  coberturas: [{ x: 200, y: 0, ancho: 300, largo: 500, altura: 300, etiqueta: 'muro' }],
  ordenPrevisto: ['guardia del paso', 'balcon', 'flanco']
};
const encB = expandirPropuesta(buena, base);
comprobar('hereda la arena del encuentro base',
  JSON.stringify(encB.arena.bounds) === JSON.stringify(base.arena.bounds));
comprobar('hereda las plataformas', encB.plataformas.length === base.plataformas.length);
comprobar('crea los 3 enemigos', encB.enemigos.length === 3);
comprobar('traduce el orden por etiqueta', encB.ordenPrevisto.length === 3 &&
  encB.enemigos.find(e => e.id === encB.ordenPrevisto[0])?.etiqueta === 'guardia del paso');
comprobar('respeta las politicas de drop',
  encB.enemigos.filter(e => e.drop === 'garantizado').length === 1);
comprobar('valida sin errores', validar(encB).filter(p => p.nivel === 'error').length === 0);
const loteB = correrLote(encB, cal, armas, { partidas: 40 });
comprobar('se simula', loteB.veredicto.puertas.length > 0,
  `espada ${(loteB.porPolitica['cercano'].resumen.tasaVictoria * 100).toFixed(0)}%`);

// --- 3. Propuestas malas: la herramienta no puede caerse ---
console.log('\n--- propuestas defectuosas ---');
const malas = [
  ['arquetipo inventado', { nombre: 'x', enemigos: [{ arquetipo: 'dragon_rojo', x: 0, y: 0, cota: 0, drop: 'estandar', etiqueta: 'a' }], coberturas: [], ordenPrevisto: [] }],
  ['drop inventado', { nombre: 'x', enemigos: [{ arquetipo: 'lancero_del_alba', x: 0, y: 0, cota: 0, drop: 'legendario', etiqueta: 'a' }], coberturas: [], ordenPrevisto: [] }],
  ['orden con etiquetas que no existen', { nombre: 'x', enemigos: [{ arquetipo: 'lancero_del_alba', x: 0, y: 0, cota: 0, drop: 'estandar', etiqueta: 'a' }], coberturas: [], ordenPrevisto: ['fantasma', 'otro'] }],
  ['campos ausentes', { nombre: 'x', enemigos: [{ arquetipo: 'escudero_celestial', x: 100, y: 100 }] }],
  ['cota alta sin plataforma', { nombre: 'x', enemigos: [{ arquetipo: 'arquero_del_firmamento', x: -1000, y: -1200, cota: 900, drop: 'garantizado', etiqueta: 'a' }, { arquetipo: 'lancero_del_alba', x: 0, y: 0, cota: 0, drop: 'estandar', etiqueta: 'b' }], coberturas: [], ordenPrevisto: [] }]
];

for (const [nombre, propuesta] of malas) {
  try {
    const e = expandirPropuesta(propuesta, base);
    const problemas = validar(e);
    const l = correrLote(e, cal, armas, { partidas: 10 });
    const errores = problemas.filter(p => p.nivel === 'error').map(p => p.codigo);
    comprobar(nombre, true, `${e.enemigos.length} enemigos, simula, errores: [${errores.join(', ') || 'ninguno'}]`);
  } catch (err) {
    comprobar(nombre, false, 'REVIENTA: ' + err.message);
  }
}

// --- 4. Que el arquetipo inventado se descarta, no se cuela ---
console.log('\n--- higiene ---');
const conBasura = expandirPropuesta(malas[0][1], base);
comprobar('el arquetipo inventado se descarta', conBasura.enemigos.length === 0);
const conDropMalo = expandirPropuesta(malas[1][1], base);
comprobar('el drop inventado cae a "estandar"', conDropMalo.enemigos[0]?.drop === 'estandar');

// --- 5. Los hitos para el narrador ---
console.log('\n--- hitos de la partida ---');
const hitos = hitosDeLaPartida(lote.testigo, base);
comprobar('se extraen hitos', !!hitos && hitos.hitos.length > 0, `${hitos?.hitos.length} hitos`);
comprobar('no arrastra el log entero', JSON.stringify(hitos).length < 20000);

// --- 6. El esquema es valido para modo estricto ---
console.log('\n--- esquema estricto ---');
const revisar = (nodo, ruta = 'raiz') => {
  if (nodo.type === 'object') {
    if (nodo.additionalProperties !== false) comprobar(`${ruta}: additionalProperties false`, false);
    const props = Object.keys(nodo.properties || {});
    const req = nodo.required || [];
    const faltan = props.filter(p => !req.includes(p));
    if (faltan.length) comprobar(`${ruta}: todos los campos en required`, false, `faltan ${faltan.join(', ')}`);
    for (const [k, v] of Object.entries(nodo.properties || {})) revisar(v, `${ruta}.${k}`);
  }
  if (nodo.type === 'array' && nodo.items) revisar(nodo.items, `${ruta}[]`);
};
revisar(ESQUEMA_PROPUESTA);
comprobar('el esquema cumple las reglas de strict', true);

console.log(fallos ? `\n${fallos} comprobaciones MAL` : '\ntodo correcto');
process.exitCode = fallos ? 1 : 0;
