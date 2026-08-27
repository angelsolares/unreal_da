// El esquema `Encuentro` v2: el contrato con Unreal.
//
// La fuente de verdad es Tools/MCP/ENCUENTROS_CONTRATO.md, acordado con la sesion
// de Unreal. Si algo cambia aqui, se cambia alli primero y se sube schemaVersion.
//
// Lo que el motor fija y no se negocia:
//   - Centimetros, 1:1 con Unreal. Sin conversion.
//   - Z arriba, suelo plano en z = 0.
//   - Solo yaw, en grados. VERIFICADO contra el editor: forward = (cos yaw, sin yaw),
//     que es exactamente atan2(dy, dx). No hay espejo entre la herramienta y Unreal.
//   - Un nivel suelto reutilizable, NO una Level Instance: las coordenadas del JSON
//     son de mundo directas. Por eso v2 ya no lleva origenMundo ni submapa.
//
// QUE SIGNIFICA `cota` EN CADA SITIO — significaba tres cosas y ninguna estaba escrita:
//   coberturas  -> la BASE del bloque. `altura` es lo que mide hacia arriba desde ahi.
//   plataformas -> la SUPERFICIE QUE SE PISA. Unreal le pone el grosor por debajo.
//   enemigos    -> la superficie sobre la que estan de pie.
//   jugador     -> idem.

import { ARQUETIPOS, ORDEN_ARQUETIPOS } from './catalogo.js';
import { dist } from './geometria.js';

export const VERSION_ESQUEMA = 2;

// ------------------------------------------------------------------ vocabulario

/** Vocabulario CERRADO. Un arquetipo fuera de esta lista es un error de carga. */
export const ARQUETIPOS_VALIDOS = ORDEN_ARQUETIPOS;

/**
 * Armas con las que puede empezar Malakh. Cerrado, como los arquetipos.
 * Fase A es `["espada"]`; la Fase B es cambiar esa linea.
 */
export const LOADOUT_VALIDO = ['espada', 'lanza', 'arco', 'escudo', 'espadon', 'estandarte'];

/**
 * Como se activa una oleada (§6: las recetas escalonan la entrada al combate).
 *
 *   inicio        al romper el sello. Al menos una oleada TIENE que ser de estas.
 *   tiempo        `segundos` despues del sello.
 *   bajas         cuando han caido `cuantas` enemigos en total.
 *   oleadaLimpia  cuando la oleada `oleada` no tiene a nadie vivo.
 *
 * Vocabulario CERRADO, como los arquetipos: lo que no esta aqui, Unreal no
 * sabria cablearlo en `BP_DA_Arena`, y un encuentro que solo existe en el
 * simulador no vale para nada.
 */
export const ACTIVACION_VALIDA = ['inicio', 'tiempo', 'bajas', 'oleadaLimpia'];

/**
 * Donde esta un enemigo antes de que su oleada se active.
 *
 *   en-escena  ya esta plantado en la arena, quieto, y SE VE desde la puerta.
 *              Es el unico modo que respeta el §5.1: la silueta comunica.
 *   entra      no esta hasta que le toca. Es una emboscada, y por eso la puerta
 *              de lectura del veredicto lo cuenta como ilegible.
 */
export const PRESENCIA_VALIDA = ['en-escena', 'entra'];

export const VICTORIA_VALIDA = ['eliminar-todos'];
export const PURGE_VALIDA = ['purgar-todo-al-romper-sello'];
export const CHECKPOINT_VALIDA = ['antes-del-trigger'];

// ------------------------------------------------------------------ geometria

/** Un rectangulo del schema -> el poligono que usa toda la geometria interna. */
export const poliDeRect = (r) => [
  { x: r.min.x, y: r.min.y },
  { x: r.max.x, y: r.min.y },
  { x: r.max.x, y: r.max.y },
  { x: r.min.x, y: r.max.y }
];

export const rectDesdeCentro = (cx, cy, largoX, anchoY) => ({
  min: { x: Math.round(cx - largoX / 2), y: Math.round(cy - anchoY / 2) },
  max: { x: Math.round(cx + largoX / 2), y: Math.round(cy + anchoY / 2) }
});

export const centroDeRect = (r) => ({ x: (r.min.x + r.max.x) / 2, y: (r.min.y + r.max.y) / 2 });

export const dentroDeRect = (p, r) =>
  p.x >= r.min.x && p.x <= r.max.x && p.y >= r.min.y && p.y <= r.max.y;

// ------------------------------------------------------------------ plantillas

export function encuentroVacio(id = 'nuevo-encuentro') {
  return {
    schemaVersion: VERSION_ESQUEMA,
    id,
    nombre: 'Encuentro sin nombre',
    unidades: 'cm',
    arena: {
      bounds: { min: { x: -1500, y: -1500 }, max: { x: 1500, y: 1500 } },
      trigger: { x: -900, y: 0, radio: 200 },
      checkpoint: { x: -1600, y: 0 }
    },
    jugador: {
      pos: { x: -1200, y: 0 },
      cota: 0,
      yaw: 0,
      vida: 100,
      loadout: ['espada']
    },
    coberturas: [],
    plataformas: [],
    // Sin oleadas declaradas, todo el mundo entra al romper el sello: es como
    // se comportaban todos los encuentros antes de que esto existiera, y ese
    // comportamiento no cambia.
    oleadas: [],
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
    // Dos booleanos, que es lo unico que BP_DA_WeaponDropComponent sabe hacer.
    //
    // La ranura la decide EL ARMA, no el enemigo. El escudo del escudero es
    // off-hand: metiendo su valor por defecto en `principal` nacia mudo —dos
    // casillas en blanco que parecian un borrado— y su escudo, que es la llave
    // de media receta del §6, no lo soltaba nadie.
    drop: meta.armaEsOffHand
      ? { principal: false, secundaria: !!meta.sueltaPorDefecto }
      : { principal: !!meta.sueltaPorDefecto, secundaria: false },
    // El director del §8 cabe en dos numeros por enemigo (los mismos que
    // expone BP_DA_WeaponDropComponent): probabilidad 1.0 = garantizado,
    // 0.5 = oportunidad, 0.0 = nada; piedad = el interruptor del Mercy
    // Drop. Los defectos son el comportamiento de siempre.
    // null = la primera oleada declarada. Un enemigo sin oleada no se queda
    // fuera del encuentro por descuido.
    oleada: null,
    etiqueta: ''
  };
}

export function nuevaCobertura(cx, cy, largoX = 400, anchoY = 400) {
  return {
    id: nuevoId('cob'),
    ...rectDesdeCentro(cx, cy, largoX, anchoY),
    cota: 0,
    altura: 200,
    bloqueaVision: true,
    bloqueaPaso: true,
    etiqueta: ''
  };
}

export function nuevaPlataforma(cx, cy, largoX = 600, anchoY = 600, cota = 300) {
  return {
    id: nuevoId('plat'),
    ...rectDesdeCentro(cx, cy, largoX, anchoY),
    cota,
    accesos: [],
    etiqueta: 'balcon'
  };
}

/** Una rampa: al pie abajo, arriba en la plataforma. */
export function nuevaRampa(desde, hasta, ancho = 300) {
  return {
    desde: { x: Math.round(desde.x), y: Math.round(desde.y) },
    hasta: { x: Math.round(hasta.x), y: Math.round(hasta.y) },
    ancho
  };
}

// ------------------------------------------------------------------- solidos

/**
 * Todo lo solido del encuentro, en una sola lista y ya como poligonos.
 *
 * Una plataforma NO es solo un suelo elevado: es un bloque. Desde abajo tapa el
 * paso y tapa la vista igual que un muro de su altura. Aqui se unifican para que
 * el simulador, la lectura del §5.1 y el editor no puedan discrepar.
 */
export function obstaculosDe(enc) {
  const coberturas = (enc.coberturas || []).map(c => ({
    id: c.id,
    poli: poliDeRect(c),
    cota: c.cota || 0,                 // base del bloque
    altura: c.altura || 0,
    bloqueaVision: c.bloqueaVision !== false,
    bloqueaPaso: c.bloqueaPaso !== false
  }));
  const plataformas = (enc.plataformas || []).map(p => ({
    id: p.id,
    poli: poliDeRect(p),
    cota: 0,                           // arranca en el suelo
    altura: p.cota || 0,               // y su cima es la superficie que se pisa
    bloqueaVision: true,
    bloqueaPaso: true,
    esPlataforma: true
  })).filter(p => p.altura > 20);
  return [...coberturas, ...plataformas];
}

export function plataformaBajo(enc, p) {
  for (const plat of enc.plataformas || []) {
    if (dentroDeRect(p, plat)) return plat;
  }
  return null;
}

export function etiquetaDe(e) {
  const meta = ARQUETIPOS[e.arquetipo];
  const base = meta ? meta.glifo : '?';
  return e.etiqueta ? `${base}·${e.etiqueta}` : `${base}·${String(e.id).slice(-4)}`;
}

/** ¿Suelta este enemigo su arma? Dos booleanos, sin probabilidad. */
export function sueltaArma(enemigo, esOffHand) {
  const d = enemigo.drop || {};
  return esOffHand ? !!d.secundaria : !!d.principal;
}

// -------------------------------------------------------------------- oleadas

/** Una oleada nueva, ya con su activacion. */
export function nuevaOleada(id, activacion = { tipo: 'inicio' }) {
  return { id, nombre: '', activacion, retardo: 0, presencia: 'en-escena' };
}

export const OLEADA_UNICA = '__unica';

/**
 * Las oleadas del encuentro, normalizadas y con su lista de enemigos.
 *
 * Un encuentro SIN oleadas declaradas devuelve una sola, implicita, con todo el
 * mundo dentro y activacion `inicio`: exactamente el comportamiento de siempre.
 * Todo lo que consume oleadas pasa por aqui, para que el simulador, la lectura
 * del §5.1 y el exportador no puedan discrepar sobre quien entra cuando.
 */
export function oleadasDe(enc) {
  const decl = enc.oleadas || [];
  const enemigos = enc.enemigos || [];
  if (!decl.length) {
    return [{
      id: OLEADA_UNICA, nombre: 'Todos', implicita: true,
      activacion: { tipo: 'inicio' }, retardo: 0, presencia: 'en-escena',
      enemigos: enemigos.map(e => e.id)
    }];
  }
  const primera = decl[0].id;
  const conocidas = new Set(decl.map(o => o.id));
  return decl.map(o => ({
    id: o.id,
    nombre: o.nombre || o.id,
    implicita: false,
    activacion: o.activacion || { tipo: 'inicio' },
    retardo: o.retardo || 0,
    presencia: o.presencia || 'en-escena',
    // Un enemigo con una oleada que no existe cae en la primera. Es un ERROR de
    // validacion, pero mientras tanto pelea: un enemigo desaparecido en silencio
    // es peor que un aviso en rojo.
    enemigos: enemigos
      .filter(e => (e.oleada && conocidas.has(e.oleada) ? e.oleada : primera) === o.id)
      .map(e => e.id)
  }));
}

/** La oleada a la que pertenece un enemigo, ya normalizada. */
export function oleadaDeEnemigo(enc, id) {
  return oleadasDe(enc).find(o => o.enemigos.includes(id)) || null;
}

/**
 * Quien esta plantado en la arena cuando el jugador cruza el umbral.
 *
 * Es la lista que mira el §5.1: lo que no esta, no se lee. Una oleada
 * `en-escena` cuenta aunque todavia no se haya activado — esta ahi, quieta.
 */
export function enemigosPresentesAlEntrar(enc) {
  const enEscena = new Set();
  for (const o of oleadasDe(enc)) {
    if (o.presencia !== 'entra' || o.activacion.tipo === 'inicio') {
      for (const id of o.enemigos) enEscena.add(id);
    }
  }
  return (enc.enemigos || []).filter(e => enEscena.has(e.id));
}

/**
 * Que oleadas pueden llegar a activarse alguna vez.
 *
 * Una oleada que nunca se activa deja a sus enemigos vivos para siempre: la
 * victoria es "eliminar-todos", asi que el encuentro se queda colgado hasta que
 * salte el watchdog. Es un SOFT-LOCK de manual, y por eso se comprueba en seco
 * en vez de gastar 200 partidas en descubrirlo.
 */
export function oleadasActivables(enc) {
  const olas = oleadasDe(enc);
  const total = (enc.enemigos || []).length;
  const vivas = new Set();
  const alcanzables = [];
  let disponibles = 0;   // enemigos que ya podrian estar muertos a esas alturas

  let cambio = true;
  while (cambio) {
    cambio = false;
    for (const o of olas) {
      if (vivas.has(o.id)) continue;
      const a = o.activacion || {};
      let puede = false;
      if (a.tipo === 'inicio') puede = true;
      else if (a.tipo === 'tiempo') puede = (a.segundos ?? 0) >= 0;
      // Con `cuantas` >= total, el ultimo en morir cierra el encuentro antes de
      // que la oleada llegue a existir.
      else if (a.tipo === 'bajas') puede = (a.cuantas ?? 0) <= disponibles && (a.cuantas ?? 0) < total;
      else if (a.tipo === 'oleadaLimpia') puede = vivas.has(a.oleada);
      if (!puede) continue;
      vivas.add(o.id);
      alcanzables.push(o);
      disponibles += o.enemigos.length;
      cambio = true;
    }
  }
  return { alcanzables, colgadas: olas.filter(o => !vivas.has(o.id)) };
}

/**
 * Quita las oleadas que se han quedado sin nadie y vuelve a encadenar las que
 * sobreviven, EN SU ORDEN.
 *
 * Hace falta en cuanto algo recorta la lista de enemigos —el techo de la espada
 * de `js/diagnostico.js`, una variante de la IA— porque una oleada vacia se da
 * por limpia al instante y la cadena entera se desploma: los que quedan entran
 * todos de golpe y lo que se mide ya no es el encuentro.
 */
export function podarOleadas(enc) {
  if (!(enc.oleadas || []).length) return enc;
  const vivos = new Set((enc.enemigos || []).map(e => e.id));
  const conGente = oleadasDe(enc).filter(o => o.enemigos.some(id => vivos.has(id)));

  enc.oleadas = conGente.map((o, i) => ({
    id: o.id,
    nombre: o.nombre,
    activacion: i === 0
      ? { tipo: 'inicio' }
      : (o.activacion.tipo === 'oleadaLimpia'
          ? { tipo: 'oleadaLimpia', oleada: conGente[i - 1].id }
          : o.activacion),
    retardo: o.retardo,
    presencia: o.presencia
  }));
  const validas = new Set(enc.oleadas.map(o => o.id));
  for (const e of enc.enemigos || []) {
    if (e.oleada && !validas.has(e.oleada)) e.oleada = enc.oleadas[0]?.id || null;
  }
  return enc;
}

// ------------------------------------------------------------------ validacion

export function validar(enc) {
  const problemas = [];
  const aviso = (nivel, codigo, texto, refs = []) => problemas.push({ nivel, codigo, texto, refs });

  if (enc.schemaVersion !== VERSION_ESQUEMA) {
    aviso('aviso', 'version', `schemaVersion ${enc.schemaVersion}; esta herramienta habla v${VERSION_ESQUEMA}.`);
  }

  // --- vocabulario cerrado (contrato §1.2): fuera de la tabla es ERROR de carga ---
  for (const e of enc.enemigos || []) {
    if (!ARQUETIPOS_VALIDOS.includes(e.arquetipo)) {
      aviso('error', 'arquetipo-desconocido',
        `"${e.arquetipo}" no esta en el vocabulario. Unreal no sabria que Blueprint poner, y un enemigo ausente en silencio es peor que un fallo.`, [e.id]);
    }
  }

  const ids = new Set();
  for (const e of enc.enemigos || []) {
    if (ids.has(e.id)) {
      aviso('error', 'id-repetido', `El id "${e.id}" esta dos veces. Los resultados se reportan por id.`, [e.id]);
    }
    ids.add(e.id);
  }

  if (!enc.enemigos?.length) aviso('error', 'sin-enemigos', 'El encuentro no tiene enemigos.');

  // --- jugador ---
  if (!enc.jugador?.pos) {
    aviso('error', 'sin-jugador', 'Falta la seccion `jugador`: sin ella el experimento no es reproducible.');
  } else {
    for (const arma of enc.jugador.loadout || []) {
      if (!LOADOUT_VALIDO.includes(arma)) {
        aviso('error', 'loadout-desconocido', `"${arma}" no esta en el vocabulario de armas.`);
      }
    }
    if (!(enc.jugador.loadout || []).includes('espada')) {
      aviso('aviso', 'sin-espada',
        'El loadout no incluye la espada. El PDF dice que Malakh SIEMPRE la conserva (§ regla central).');
    }
  }

  // --- enums declarados (contrato §1.5) ---
  const enums = [
    ['victoria.tipo', enc.victoria?.tipo, VICTORIA_VALIDA],
    ['purgePolicy', enc.purgePolicy, PURGE_VALIDA],
    ['checkpointPolicy', enc.checkpointPolicy, CHECKPOINT_VALIDA]
  ];
  for (const [campo, valor, validos] of enums) {
    if (valor && !validos.includes(valor)) {
      aviso('error', 'enum-invalido', `${campo} = "${valor}". Validos: ${validos.join(', ')}.`);
    }
  }

  // --- arena ---
  const b = enc.arena?.bounds;
  if (!b?.min || !b?.max) {
    aviso('error', 'arena-invalida', 'La arena necesita bounds con min y max.');
  } else {
    if (b.max.x <= b.min.x || b.max.y <= b.min.y) {
      aviso('error', 'arena-invalida', 'bounds.max tiene que ser mayor que bounds.min en las dos direcciones.');
    }
    for (const e of enc.enemigos || []) {
      if (!dentroDeRect(e.pos, b)) {
        aviso('aviso', 'fuera-de-arena', `${etiquetaDe(e)} esta fuera del perimetro.`, [e.id]);
      }
    }
    if (enc.jugador?.pos && !dentroDeRect(enc.jugador.pos, b)) {
      aviso('aviso', 'jugador-fuera', 'El jugador arranca fuera de la arena.');
    }
  }

  // §7.3: el checkpoint no puede caer dentro del trigger que sella
  const t = enc.arena?.trigger;
  if (t && enc.arena?.checkpoint && dist(enc.arena.checkpoint, t) <= t.radio) {
    aviso('error', 'checkpoint-en-trigger',
      'El checkpoint cae dentro del trigger del sello (§7.3): al reaparecer se resellaria la arena sola.');
  }

  // --- rampas (contrato §1.3) ---
  for (const plat of enc.plataformas || []) {
    for (const r of plat.accesos || []) {
      if (!r.desde || !r.hasta) {
        aviso('error', 'rampa-incompleta',
          `Una rampa de "${plat.etiqueta || plat.id}" no tiene desde/hasta. Un punto suelto no se puede construir.`, [plat.id]);
        continue;
      }
      if (!r.ancho || r.ancho < 100) {
        aviso('aviso', 'rampa-estrecha',
          `Rampa de "${plat.etiqueta || plat.id}" con ancho ${r.ancho || 0} cm: no cabe un enemigo con holgura.`, [plat.id]);
      }
      if (!dentroDeRect(r.hasta, plat)) {
        aviso('aviso', 'rampa-no-llega',
          `La rampa de "${plat.etiqueta || plat.id}" no acaba dentro de la plataforma.`, [plat.id]);
      }
      const largo = dist(r.desde, r.hasta);
      const pendiente = largo > 1 ? (plat.cota || 0) / largo : Infinity;
      if (pendiente > 1) {
        aviso('aviso', 'rampa-empinada',
          `La rampa de "${plat.etiqueta || plat.id}" sube ${plat.cota} cm en ${Math.round(largo)} cm: mas de 45 grados.`, [plat.id]);
      }
    }
  }

  // --- alcanzabilidad y el invariante de cota (contrato §2.1) ---
  for (const e of enc.enemigos || []) {
    const cota = e.cota || 0;
    if (cota <= 50) continue;
    const plat = plataformaBajo(enc, e.pos);
    if (!plat) {
      aviso('error', 'inalcanzable',
        `${etiquetaDe(e)} esta a cota ${cota} y no hay plataforma debajo: flota. Inalcanzable con espada: SOFT-LOCK.`, [e.id]);
    } else if (Math.abs((plat.cota || 0) - cota) > 5) {
      aviso('error', 'cota-no-cuadra',
        `${etiquetaDe(e)} esta a cota ${cota} pero la plataforma "${plat.etiqueta || plat.id}" que lo contiene esta a ${plat.cota}. O se cae o se queda flotando.`, [e.id, plat.id]);
    } else if (!plat.accesos?.length) {
      aviso('error', 'inalcanzable',
        `${etiquetaDe(e)} esta sobre "${plat.etiqueta || plat.id}", que no tiene ninguna rampa. Inalcanzable a pie: SOFT-LOCK.`, [e.id, plat.id]);
    }
  }

  // --- oleadas (§6: activacion escalonada) ---
  if ((enc.oleadas || []).length) {
    const vistas = new Set();
    for (const o of enc.oleadas) {
      if (!o.id) {
        aviso('error', 'oleada-sin-id', 'Hay una oleada sin `id`. Los enemigos se asignan por id.');
        continue;
      }
      if (vistas.has(o.id)) {
        aviso('error', 'oleada-repetida', `La oleada "${o.id}" esta dos veces.`);
      }
      vistas.add(o.id);

      const a = o.activacion || {};
      if (!ACTIVACION_VALIDA.includes(a.tipo)) {
        aviso('error', 'enum-invalido',
          `La oleada "${o.id}" se activa por "${a.tipo}". Validos: ${ACTIVACION_VALIDA.join(', ')}.`);
      }
      if (a.tipo === 'oleadaLimpia' && !enc.oleadas.some(x => x.id === a.oleada)) {
        aviso('error', 'oleada-referencia',
          `La oleada "${o.id}" espera a que se limpie "${a.oleada}", que no existe.`);
      }
      if (a.tipo === 'oleadaLimpia' && a.oleada === o.id) {
        aviso('error', 'oleada-referencia', `La oleada "${o.id}" se espera a si misma: no se activaria nunca.`);
      }
      if (o.presencia && !PRESENCIA_VALIDA.includes(o.presencia)) {
        aviso('error', 'enum-invalido',
          `La oleada "${o.id}" tiene presencia "${o.presencia}". Validas: ${PRESENCIA_VALIDA.join(', ')}.`);
      }
    }

    for (const e of enc.enemigos || []) {
      if (e.oleada && !vistas.has(e.oleada)) {
        aviso('error', 'oleada-referencia',
          `${etiquetaDe(e)} dice ser de la oleada "${e.oleada}", que no existe. Se le mete en la primera para que no desaparezca.`, [e.id]);
      }
    }

    if (!enc.oleadas.some(o => (o.activacion || {}).tipo === 'inicio')) {
      aviso('error', 'oleada-inalcanzable',
        'Ninguna oleada se activa al romper el sello: la arena se cierra y no pasa nada. Al menos una tiene que ser `inicio`.');
    }

    // El soft-lock caro: una oleada que no se activa nunca deja a los suyos
    // vivos, y "eliminar-todos" no se cumple jamas.
    const { colgadas } = oleadasActivables(enc);
    for (const o of colgadas) {
      aviso('error', 'oleada-inalcanzable',
        `La oleada "${o.nombre}" (${o.enemigos.length} enemigos) no se puede activar nunca con esas condiciones: sus enemigos se quedan vivos y el encuentro no se cierra. SOFT-LOCK.`);
    }

    for (const o of oleadasDe(enc)) {
      if (!o.enemigos.length) {
        aviso('aviso', 'oleada-vacia', `La oleada "${o.nombre}" no tiene enemigos: no hace nada.`);
      }
    }
  }

  // --- drops ---
  const sueltan = (enc.enemigos || []).filter(e => e.drop?.principal || e.drop?.secundaria);
  if ((enc.enemigos || []).length >= 3 && !sueltan.length) {
    aviso('aviso', 'sin-drops',
      'Nadie suelta arma. Sin arsenal no hay ruta de ventaja que medir (§4, §8).');
  }

  for (const id of enc.ordenPrevisto || []) {
    if (!(enc.enemigos || []).some(e => e.id === id)) {
      aviso('aviso', 'orden-huerfano', `El orden previsto menciona "${id}", que ya no existe.`);
    }
  }

  return problemas;
}

// ------------------------------------------------------------------ migracion

/**
 * v1 -> v2. Los archivos viejos siguen abriendose.
 * Lo que cambia: bounds y las cajas pasan a min/max, los accesos pasan de punto
 * a rampa, `arena.entrada` se convierte en la seccion `jugador`, y el `drop` de
 * cuatro politicas se reduce a los dos booleanos que el componente sabe hacer.
 */
function migrarDeV1(v1) {
  const cajaDePoli = (poli) => {
    const xs = poli.map(p => p.x), ys = poli.map(p => p.y);
    return {
      min: { x: Math.min(...xs), y: Math.min(...ys) },
      max: { x: Math.max(...xs), y: Math.max(...ys) }
    };
  };

  const enc = encuentroVacio(v1.id || 'migrado');
  enc.nombre = v1.nombre || enc.nombre;
  enc.notasDiseno = v1.notasDiseno || '';

  if (v1.arena?.bounds) enc.arena.bounds = cajaDePoli(v1.arena.bounds);
  if (v1.arena?.trigger) enc.arena.trigger = { ...v1.arena.trigger };
  if (v1.arena?.checkpoint) enc.arena.checkpoint = { ...v1.arena.checkpoint };

  enc.jugador = {
    pos: v1.arena?.entrada ? { ...v1.arena.entrada } : { x: -1200, y: 0 },
    cota: 0,
    yaw: 0,
    vida: 100,
    loadout: ['espada']
  };

  enc.coberturas = (v1.coberturas || []).map(c => ({
    id: c.id || nuevoId('cob'),
    ...cajaDePoli(c.poli),
    cota: c.cota || 0,
    altura: c.altura || 200,
    bloqueaVision: c.bloqueaVision !== false,
    bloqueaPaso: c.bloqueaPaso !== false,
    etiqueta: c.etiqueta || ''
  }));

  enc.plataformas = (v1.plataformas || []).map(p => {
    const caja = cajaDePoli(p.poli);
    const centro = centroDeRect(caja);
    return {
      id: p.id || nuevoId('plat'),
      ...caja,
      cota: p.cota || 0,
      // Un acceso v1 era un punto al pie. Se le inventa el tramo que sube hacia
      // el centro de la plataforma, con ancho por defecto. Queda MARCADO en las
      // notas porque es una suposicion, no un dato del archivo viejo.
      accesos: (p.accesos || []).map(a => {
        const dx = centro.x - a.x, dy = centro.y - a.y;
        const l = Math.hypot(dx, dy) || 1;
        const largoRampa = Math.max(200, (p.cota || 0) * 1.5);
        return nuevaRampa(a, {
          x: a.x + (dx / l) * largoRampa,
          y: a.y + (dy / l) * largoRampa
        }, 300);
      }),
      etiqueta: p.etiqueta || ''
    };
  });

  enc.enemigos = (v1.enemigos || []).map(e => ({
    id: e.id || nuevoId('en'),
    arquetipo: e.arquetipo,
    pos: { ...e.pos },
    cota: e.cota || 0,
    yaw: e.yaw ?? 180,
    // "garantizado" -> suelta; "estandar"/"piedad"/"ninguno" -> no suelta.
    // La probabilidad no existe en BP_DA_WeaponDropComponent, asi que fingirla
    // seria probar algo que el juego no puede hacer.
    drop: mapaDropV1(e.drop, e.arquetipo),
    etiqueta: e.etiqueta || ''
  }));

  enc.ordenPrevisto = v1.ordenPrevisto || [];
  if (enc.plataformas.some(p => p.accesos.length)) {
    enc.notasDiseno = (enc.notasDiseno ? enc.notasDiseno + '\n\n' : '')
      + 'MIGRADO DE v1: las rampas se han inventado a partir de los puntos de acceso '
      + 'viejos (direccion hacia el centro de la plataforma, ancho 300). Reviselas.';
  }
  return enc;
}

function mapaDropV1(dropV1, arquetipo) {
  const meta = ARQUETIPOS[arquetipo];
  const suelta = dropV1 === 'garantizado';
  return meta?.armaEsOffHand
    ? { principal: false, secundaria: suelta }
    : { principal: suelta, secundaria: false };
}

// ------------------------------------------------------------------ serializar

export function aJSON(enc) { return JSON.stringify(enc, null, 2); }

export function desdeJSON(texto) {
  const bruto = typeof texto === 'string' ? JSON.parse(texto) : texto;
  if ((bruto.schemaVersion || 1) < 2) return migrarDeV1(bruto);

  const base = encuentroVacio(bruto.id || 'importado');
  return {
    ...base, ...bruto,
    schemaVersion: VERSION_ESQUEMA,
    arena: { ...base.arena, ...(bruto.arena || {}) },
    jugador: { ...base.jugador, ...(bruto.jugador || {}) },
    coberturas: bruto.coberturas || [],
    plataformas: (bruto.plataformas || []).map(p => ({ accesos: [], ...p })),
    oleadas: (bruto.oleadas || []).map(o => ({
      nombre: '', retardo: 0, presencia: 'en-escena', activacion: { tipo: 'inicio' }, ...o
    })),
    enemigos: (bruto.enemigos || []).map(e => ({
      cota: 0, yaw: 180, drop: { principal: false, secundaria: false }, oleada: null, etiqueta: '', ...e
    })),
    ordenPrevisto: bruto.ordenPrevisto || []
  };
}

export function cajaDelEncuentro(enc) {
  const b = enc.arena.bounds;
  const puntos = [
    b.min, b.max,
    ...(enc.enemigos || []).map(e => e.pos),
    enc.jugador?.pos, enc.arena.checkpoint, enc.arena.trigger,
    ...(enc.coberturas || []).flatMap(c => [c.min, c.max]),
    ...(enc.plataformas || []).flatMap(p => [p.min, p.max]),
    ...(enc.plataformas || []).flatMap(p => (p.accesos || []).flatMap(r => [r.desde, r.hasta]))
  ].filter(Boolean);
  const xs = puntos.map(p => p.x), ys = puntos.map(p => p.y);
  return { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
}
