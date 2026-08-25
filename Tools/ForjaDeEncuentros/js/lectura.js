// "Lectura antes que UI" (§5.1 del PDF), hecho numero.
//
// El documento apuesta toda la mecanica a una idea:
//
//     "Silueta / arma: Lanza larga y brillante visible desde entrada
//      -> Ese enemigo CONTIENE una herramienta que puede cambiar la arena"
//
// Si el que lleva la llave tactica no se VE desde la puerta, esa señal no
// existe y el jugador no puede descubrir la ruta: solo tropezarse con ella.
// Aqui se comprueba, enemigo a enemigo, desde los ojos de Malakh en la entrada.
//
// Vive aparte de la vista 3D a proposito: asi el veredicto lo puede usar sin
// navegador y las pruebas de node lo cubren.

import { dist, hayVision } from './geometria.js';
import { obstaculosDe, sueltaArma, enemigosPresentesAlEntrar } from './esquema.js';
import { FAMILIAS } from './catalogo.js';

/**
 * Mas alla de esta distancia una silueta deja de leerse como algo concreto.
 * Es una SUPOSICION de diseño, no una medida: 40 m es el orden de magnitud en
 * el que un cuerpo humano deja de tener detalle legible a 1080p con FOV normal.
 */
export const LIMITE_LECTURA = 4000;

/** Grados que ocupa algo de `tamano` cm de ancho visto a `distancia` cm. */
export function tamanoAngular(tamano, distancia) {
  if (distancia <= 1) return 180;
  return 2 * Math.atan(tamano / 2 / distancia) * 180 / Math.PI;
}

/**
 * Lo que Malakh ve al cruzar el umbral, antes de que empiece nada.
 * Devuelve una fila por enemigo.
 */
export function lecturaDesdeLaEntrada(encuentro, calibracion) {
  const ojos = encuentro.jugador.pos;
  const alturaOjos = calibracion.malakh.alturaOjos;
  // Con oleadas (§6), lo que todavia no esta en la arena no se puede leer. Una
  // oleada `en-escena` si cuenta: esta plantada y quieta, que es justo lo que el
  // §5.1 quiere. Una `entra` es una emboscada, y aqui se dice.
  const presentes = new Set(enemigosPresentesAlEntrar(encuentro).map(e => e.id));

  return encuentro.enemigos.map(e => {
    const perfil = calibracion.arquetipos[e.arquetipo] || {};
    const d = dist(ojos, e.pos);
    const presenteAlEntrar = presentes.has(e.id);
    const visible = presenteAlEntrar &&
      hayVision(ojos, 0, e.pos, e.cota || 0, obstaculosDe(encuentro), alturaOjos);

    // La silueta es el cuerpo mas lo que lleva. Eso es justo lo que el §5.1
    // quiere que se lea: no "hay un enemigo" sino "ese lleva una lanza".
    const fam = FAMILIAS[perfil.arma];
    const anchoCuerpo = (perfil.radio || 45) * 2;
    const anchoSilueta = anchoCuerpo + (fam ? siluetaDelArma(fam.id) : 0);

    const grados = tamanoAngular(anchoSilueta, d);
    const gradosCuerpo = tamanoAngular(anchoCuerpo, d);

    let estado;
    if (!presenteAlEntrar) estado = 'ausente';
    else if (!visible) estado = 'tapado';
    else if (d > LIMITE_LECTURA) estado = 'lejos';
    else estado = 'legible';

    return {
      id: e.id,
      presenteAlEntrar,
      etiqueta: e.etiqueta || e.id,
      arquetipo: e.arquetipo,
      arma: perfil.arma || null,
      nombreArma: fam?.nombre || null,
      llaveTactica: sueltaArma(e, !!fam?.esOffHand),
      distancia: Math.round(d),
      cota: e.cota || 0,
      visible,
      estado,
      grados: +grados.toFixed(2),
      gradosCuerpo: +gradosCuerpo.toFixed(2),
      // cuanto de la silueta es el arma: si es poco, el arma no se distingue
      fraccionArma: +(1 - gradosCuerpo / grados).toFixed(2)
    };
  });
}

/** Cuanto ancho añade cada arma a la silueta, en cm. Suposicion de diseño. */
function siluetaDelArma(familia) {
  switch (familia) {
    case 'lanza_del_alba': return 260;      // larga y atravesada: se ve de lejos
    case 'estandarte_ritual': return 200;   // alta, con tela
    case 'espadon_alabarda': return 170;
    case 'arco_del_firmamento': return 110;
    case 'escudo_celestial': return 90;     // pegado al cuerpo: apenas cambia la silueta
    default: return 0;
  }
}

/**
 * Resumen para el veredicto. La pregunta que contesta:
 * ¿las llaves tacticas del encuentro se ven desde la puerta?
 */
export function resumenDeLectura(encuentro, calibracion) {
  const filas = lecturaDesdeLaEntrada(encuentro, calibracion);
  const llaves = filas.filter(f => f.llaveTactica);
  const llavesIlegibles = llaves.filter(f => f.estado !== 'legible');
  const nadieVisible = filas.length > 0 && filas.every(f => !f.visible);

  return {
    filas,
    llaves,
    llavesIlegibles,
    nadieVisible,
    visiblesAlEntrar: filas.filter(f => f.visible).length
  };
}
