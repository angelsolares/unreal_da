// El esquema `Encuentro`: el contrato con Unreal.
//
// Esta forma es la que tendra el Data Asset del "Encounter Definition" (PDF §11.1).
// Todo en centimetros. El origen es LOCAL al encuentro; el exportador le suma
// despues el offset de la Level Instance del submapa de Malkuth.

import { ARQUETIPOS, ORDEN_ARQUETIPOS } from './catalogo.js';
import { rectangulo, cajaDe, dentroDePoligono, dist } from './geometria.js';

export const VERSION_ESQUEMA = 1;

export function encuentroVacio(id = 'nuevo-encuentro') {
  return {
    schemaVersion: VERSION_ESQUEMA,
    id,
    nombre: 'Encuentro sin nombre',
    unidades: 'cm',
    origenMundo: { x: 0, y: 0, z: 0 },
    submapa: '',
    arena: {
      bounds: rectangulo(0, 0, 3000, 3000),
      entrada: { x: -1200, y: 0 },
      trigger: { x: -900, y: 0, radio: 200 },
      checkpoint: { x: -1600, y: 0 }
    },
    coberturas: [],
    plataformas: [],
    enemigos: [],
    victoria: { tipo: 'eliminar-todos' },
    purgePolicy: 'purgar-todo-al-romper-sello',
    checkpointPolicy: 'antes-del-trigger',
    ordenPrevisto: [],
    notasDiseno: ''
  };
}

let contador = 0;
export function nuevoId(prefijo) {
  contador += 1;
  return `${prefijo}_${Date.now().toString(36)}${contador.toString(36)}`;
}

export function nuevoEnemigo(arquetipo, x, y) {
  const meta = ARQUETIPOS[arquetipo] || ARQUETIPOS[ORDEN_ARQUETIPOS[0]];
  return {
    id: nuevoId('en'),
    arquetipo,
    pos: { x, y },
    cota: 0,
    yaw: 180,
    drop: meta.dropPorDefecto,
    etiqueta: ''
  };
}

export function nuevaCobertura(x, y, ancho = 400, alto = 400) {
  return {
    id: nuevoId('cob'),
    poli: rectangulo(x, y, ancho, alto),
    cota: 0,
    altura: 200,
    bloqueaVision: true,
    bloqueaPaso: true,
    etiqueta: ''
  };
}

export function nuevaPlataforma(x, y, ancho = 600, alto = 600, cota = 300) {
  return {
    id: nuevoId('plat'),
    poli: rectangulo(x, y, ancho, alto),
    cota,
    accesos: [],
    etiqueta: 'balcon'
  };
}

// ------------------------------------------------------------------- validacion

/**
 * Comprobaciones estaticas: las que se pueden responder sin simular.
 * La de alcance es la mas valiosa — detecta un soft-lock del §7.3 antes de
 * construir la arena en Unreal, no despues.
 */
export function validar(enc) {
  const problemas = [];
  const aviso = (nivel, codigo, texto, refs = []) => problemas.push({ nivel, codigo, texto, refs });

  if (!enc.enemigos.length) {
    aviso('error', 'sin-enemigos', 'El encuentro no tiene enemigos.');
  }
  if (enc.arena.bounds.length < 3) {
    aviso('error', 'arena-invalida', 'La arena necesita al menos tres vertices.');
  }

  // Todo el mundo dentro de la arena
  for (const e of enc.enemigos) {
    if (enc.arena.bounds.length >= 3 && !dentroDePoligono(e.pos, enc.arena.bounds)) {
      aviso('aviso', 'fuera-de-arena', `${etiquetaDe(e)} esta fuera del perimetro de la arena.`, [e.id]);
    }
  }

  // §7.3: el checkpoint no debe estar dentro del volumen que dispara el sello
  const t = enc.arena.trigger;
  if (t && enc.arena.checkpoint) {
    if (dist(enc.arena.checkpoint, t) <= t.radio) {
      aviso('error', 'checkpoint-en-trigger',
        'El checkpoint cae dentro del trigger del sello. El PDF (§7.3) lo prohibe: al reaparecer se resellaria la arena sola.');
    }
  }

  // Alcanzabilidad: cualquier enemigo en cota alta necesita un acceso.
  //
  // Los dos casos de abajo son el MISMO soft-lock, aunque no lo parezcan: el
  // simulador solo permite golpear con menos de 120 cm de diferencia de cota, asi
  // que un enemigo flotando sin plataforma es tan inalcanzable como uno en un
  // balcon sin rampa. Por eso los dos llevan el codigo `inalcanzable` y los dos
  // tumban la puerta del §7.3.
  for (const e of enc.enemigos) {
    if ((e.cota || 0) <= 50) continue;
    const plat = plataformaBajo(enc, e.pos);
    if (!plat) {
      aviso('error', 'inalcanzable',
        `${etiquetaDe(e)} esta a cota ${e.cota} y no hay ninguna plataforma debajo: flota. Con espada sola es inalcanzable: SOFT-LOCK.`, [e.id]);
    } else if (!plat.accesos || plat.accesos.length === 0) {
      aviso('error', 'inalcanzable',
        `${etiquetaDe(e)} esta sobre "${plat.etiqueta || plat.id}" sin ningun acceso. Con espada sola es inalcanzable: SOFT-LOCK.`, [e.id, plat.id]);
    }
  }

  // Drops garantizados: §8 pide que la llave tactica sea determinista
  const garantizados = enc.enemigos.filter(e => e.drop === 'garantizado');
  if (enc.enemigos.length >= 3 && garantizados.length === 0) {
    aviso('aviso', 'sin-drop-garantizado',
      'Ningun enemigo tiene Guaranteed Tactical Drop. La ruta de ventaja quedaria a merced del RNG (§8).');
  }

  // Orden previsto coherente
  for (const id of enc.ordenPrevisto || []) {
    if (!enc.enemigos.some(e => e.id === id)) {
      aviso('aviso', 'orden-huerfano', `El orden previsto menciona "${id}", que ya no existe.`);
    }
  }

  return problemas;
}

/**
 * Todo lo solido del encuentro, en una sola lista.
 *
 * Una plataforma NO es solo un suelo elevado: es un bloque. Desde abajo tapa el
 * paso y tapa la vista igual que un muro de su altura. El simulador la trataba
 * como aire y los agentes cruzaban por dentro del balcon —se veia clarisimo en
 * la vista 3D, donde si esta dibujada maciza—. Aqui se unifican los dos para que
 * el simulador, la lectura del §5.1 y el editor no puedan discrepar.
 */
export function obstaculosDe(enc) {
  const coberturas = (enc.coberturas || []).map(c => ({
    id: c.id,
    poli: c.poli,
    cota: c.cota || 0,
    altura: c.altura || 0,
    bloqueaVision: c.bloqueaVision !== false,
    bloqueaPaso: c.bloqueaPaso !== false
  }));
  const plataformas = (enc.plataformas || []).map(p => ({
    id: p.id,
    poli: p.poli,
    cota: 0,                    // arranca en el suelo
    altura: p.cota || 0,        // y su cima es la cota a la que se camina encima
    bloqueaVision: true,
    bloqueaPaso: true,
    esPlataforma: true
  })).filter(p => p.altura > 20);
  return [...coberturas, ...plataformas];
}

export function plataformaBajo(enc, p) {
  for (const plat of enc.plataformas) {
    if (dentroDePoligono(p, plat.poli)) return plat;
  }
  return null;
}

export function etiquetaDe(e) {
  const meta = ARQUETIPOS[e.arquetipo];
  const base = meta ? `${meta.glifo}` : '?';
  return e.etiqueta ? `${base}·${e.etiqueta}` : `${base}·${e.id.slice(-4)}`;
}

// ------------------------------------------------------------------- serializar

export function aJSON(enc) {
  return JSON.stringify(enc, null, 2);
}

export function desdeJSON(texto) {
  const enc = JSON.parse(texto);
  if (enc.schemaVersion !== VERSION_ESQUEMA) {
    console.warn(`Encuentro con schemaVersion ${enc.schemaVersion}; esta version es ${VERSION_ESQUEMA}.`);
  }
  // Rellenar lo que falte, para que un JSON escrito a mano no rompa el editor.
  const base = encuentroVacio(enc.id || 'importado');
  return {
    ...base, ...enc,
    arena: { ...base.arena, ...(enc.arena || {}) },
    coberturas: enc.coberturas || [],
    plataformas: enc.plataformas || [],
    enemigos: (enc.enemigos || []).map(e => ({ cota: 0, yaw: 180, drop: 'estandar', ...e })),
    ordenPrevisto: enc.ordenPrevisto || []
  };
}

export function cajaDelEncuentro(enc) {
  const puntos = [
    ...enc.arena.bounds,
    ...enc.enemigos.map(e => e.pos),
    enc.arena.entrada, enc.arena.checkpoint,
    ...enc.coberturas.flatMap(c => c.poli),
    ...enc.plataformas.flatMap(p => p.poli)
  ].filter(Boolean);
  return puntos.length ? cajaDe(puntos) : { minX: -1500, maxX: 1500, minY: -1500, maxY: 1500 };
}
