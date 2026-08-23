// El contrato con el modelo, y la frontera entre lo que propone y lo que decide.
//
// REGLA DE LA FASE D: la IA propone, el simulador dispone.
//
// El modelo NO devuelve un Encuentro completo. Devuelve una PROPUESTA estrecha
// —composicion y geometria— y la herramienta la expande a un Encuentro de verdad
// con sus invariantes (arena, sello, checkpoint, ids). Dos razones:
//
//   1. Menos superficie donde equivocarse. El schema estricto de OpenAI exige
//      additionalProperties:false y todos los campos en `required`, lo que choca
//      con un Encuentro lleno de campos opcionales.
//   2. Las reglas que el PDF da por sentadas (el checkpoint fuera del trigger,
//      la espada que siempre basta) no se negocian con un modelo.
//
// Nada de lo que salga de aqui se enseña sin pasar por validar() y por el lote.

import { encuentroVacio, nuevoEnemigo, nuevaCobertura, nuevoId, plataformaBajo } from './esquema.js';
import { ORDEN_ARQUETIPOS } from './catalogo.js';

/** JSON Schema estricto para la generacion de variantes. */
export const ESQUEMA_PROPUESTA = {
  type: 'object',
  additionalProperties: false,
  required: ['variantes'],
  properties: {
    variantes: {
      type: 'array',
      minItems: 1,
      maxItems: 3,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['nombre', 'queEnsena', 'porQueFunciona', 'enemigos', 'coberturas', 'ordenPrevisto'],
        properties: {
          nombre: { type: 'string' },
          queEnsena: {
            type: 'string',
            description: 'El aprendizaje del encuentro, en una frase, como la columna "Aprendizaje" del §6 del PDF.'
          },
          porQueFunciona: {
            type: 'string',
            description: 'Que señal del §5.1 (posicion, presion, silueta, geometria, timing, reaccion enemiga) comunica la ruta sin texto.'
          },
          enemigos: {
            // El tope de 4 es una restriccion DURA, no un ruego. En la primera
            // tanda real el modelo mantuvo los 5 enemigos aunque el prompt le
            // pedia menos, y el simulador tumbo las tres variantes por lo mismo:
            // la espada sola no aguanta esa presion. Lo que el prompt sugiere se
            // ignora; lo que el esquema prohibe, no.
            type: 'array',
            minItems: 2,
            maxItems: 4,
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['arquetipo', 'x', 'y', 'cota', 'sueltaArmaPrincipal', 'sueltaOffHand', 'etiqueta'],
              properties: {
                arquetipo: { type: 'string', enum: ORDEN_ARQUETIPOS },
                x: { type: 'number', description: 'cm. Positivo = hacia el fondo, lejos de la entrada.' },
                y: { type: 'number', description: 'cm. Positivo = a la derecha mirando desde la entrada.' },
                cota: {
                  type: 'number',
                  description: 'cm. La superficie sobre la que esta de pie. 0 = suelo. Solo distinto de 0 si hay una plataforma a esa misma cota debajo, o el enemigo flota y es un soft-lock.'
                },
                sueltaArmaPrincipal: {
                  type: 'boolean',
                  description: 'Si al morir deja su arma de mano principal. Lanza, arco, espadon y estandarte van por aqui.'
                },
                sueltaOffHand: {
                  type: 'boolean',
                  description: 'Si al morir deja su off-hand. Es la ranura del ESCUDO: el escudero_celestial suelta por aqui, no por la principal.'
                },
                etiqueta: { type: 'string' }
              }
            }
          },
          coberturas: {
            type: 'array',
            maxItems: 5,
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['x', 'y', 'ancho', 'largo', 'altura', 'etiqueta'],
              properties: {
                x: { type: 'number' },
                y: { type: 'number' },
                ancho: { type: 'number', description: 'cm en el eje Y' },
                largo: { type: 'number', description: 'cm en el eje X' },
                altura: { type: 'number', description: 'cm. Por encima de 160 corta la linea de vision.' },
                etiqueta: { type: 'string' }
              }
            }
          },
          ordenPrevisto: {
            type: 'array',
            description: 'Etiquetas de los enemigos, en el orden de bajas que hace la ruta buena.',
            items: { type: 'string' }
          }
        }
      }
    }
  }
};

/**
 * Expande una propuesta del modelo a un Encuentro de verdad.
 * La arena, el sello y el checkpoint se heredan del encuentro actual: son
 * decisiones de nivel, no de composicion, y el modelo no las toca.
 */
export function expandirPropuesta(variante, encuentroBase) {
  const enc = encuentroVacio(`ia-${(variante.nombre || 'variante').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40)}`);
  enc.nombre = variante.nombre || 'Variante sin nombre';
  enc.arena = JSON.parse(JSON.stringify(encuentroBase.arena));
  enc.plataformas = JSON.parse(JSON.stringify(encuentroBase.plataformas || []));
  enc.notasDiseno = [
    `Generada por IA a partir de "${encuentroBase.nombre}".`,
    `Que enseña: ${variante.queEnsena || '—'}`,
    `Por que funciona: ${variante.porQueFunciona || '—'}`,
    '',
    'OJO: esto es una propuesta, no un encuentro validado. Miralo en el veredicto antes de creerte nada.'
  ].join('\n');

  const porEtiqueta = new Map();
  for (const e of variante.enemigos || []) {
    if (!ORDEN_ARQUETIPOS.includes(e.arquetipo)) continue;
    const nuevo = nuevoEnemigo(e.arquetipo, Math.round(e.x), Math.round(e.y));
    nuevo.cota = Math.round(e.cota || 0);
    nuevo.drop = { principal: !!e.sueltaArmaPrincipal, secundaria: !!e.sueltaOffHand };
    nuevo.etiqueta = e.etiqueta || '';
    nuevo.yaw = 180;
    enc.enemigos.push(nuevo);
    if (nuevo.etiqueta) porEtiqueta.set(nuevo.etiqueta, nuevo.id);
  }

  for (const c of variante.coberturas || []) {
    const cob = nuevaCobertura(Math.round(c.x), Math.round(c.y), Math.round(c.ancho || 400), Math.round(c.largo || 400));
    cob.altura = Math.round(c.altura || 200);
    cob.etiqueta = c.etiqueta || 'cobertura';
    enc.coberturas.push(cob);
  }

  // El orden viene por etiqueta; lo que no case se ignora en vez de romper.
  enc.ordenPrevisto = (variante.ordenPrevisto || [])
    .map(et => porEtiqueta.get(et))
    .filter(Boolean);
  for (const e of enc.enemigos) {
    if (!enc.ordenPrevisto.includes(e.id)) enc.ordenPrevisto.push(e.id);
  }

  // El invariante del contrato §2.1: nadie flota. Si el modelo puso una cota que
  // no cuadra con ninguna plataforma, se le baja al suelo en vez de generar un
  // soft-lock que luego habria que cazar en el veredicto.
  for (const e of enc.enemigos) {
    const plat = plataformaBajo(enc, e.pos);
    e.cota = plat ? plat.cota : 0;
  }

  return enc;
}

/**
 * Lo que se le manda al modelo sobre el encuentro actual. Deliberadamente
 * compacto: posiciones, politicas de drop y los numeros del veredicto. Sin
 * eventos ni fotogramas, que son ruido y cuestan tokens.
 */
export function resumirParaIA(enc, cal, lote) {
  const resumen = {
    nombre: enc.nombre,
    arena: {
      limites: enc.arena.bounds,
      entradaDeMalakh: enc.jugador.pos,
      trigger: enc.arena.trigger
    },
    enemigos: enc.enemigos.map(e => ({
      etiqueta: e.etiqueta || e.id,
      arquetipo: e.arquetipo,
      x: Math.round(e.pos.x), y: Math.round(e.pos.y), cota: e.cota || 0,
      sueltaArmaPrincipal: !!e.drop?.principal,
      sueltaOffHand: !!e.drop?.secundaria,
      arma: cal.arquetipos[e.arquetipo]?.arma || null
    })),
    coberturas: (enc.coberturas || []).map(c => ({ etiqueta: c.etiqueta, altura: c.altura })),
    plataformas: (enc.plataformas || []).map(p => ({ etiqueta: p.etiqueta, cota: p.cota, rampas: (p.accesos || []).length })),
    ordenPrevisto: (enc.ordenPrevisto || []).map(id => {
      const e = enc.enemigos.find(x => x.id === id);
      return e ? (e.etiqueta || e.id) : id;
    })
  };

  if (!lote) return { encuentro: resumen };

  return {
    encuentro: resumen,
    veredicto: {
      titular: lote.veredicto.titular,
      puertas: lote.veredicto.puertas.map(p => ({
        puerta: p.titulo, estado: p.estado, referencia: p.referencia, texto: p.texto
      }))
    },
    politicas: Object.values(lote.porPolitica).map(p => ({
      politica: p.nombre,
      ganaPorcentaje: Math.round(p.resumen.tasaVictoria * 100),
      tiempoMediana: p.resumen.tiempoMediana,
      danoMediana: p.resumen.danoMediana,
      armasPorPartida: p.resumen.armasPorPartida,
      descartesPorPartida: p.resumen.descartesPorPartida
    })),
    danoRecibidoPorArquetipo: lote.porPolitica['cercano']?.resumen.danoPorFuente
      .map(f => ({ arquetipo: f.arquetipo, porcentaje: Math.round(f.fraccion * 100) })),
    danoInfligidoPorArma: lote.porPolitica['ventaja']?.resumen.danoPorArma
      .map(f => ({ arma: f.clave, porcentaje: Math.round(f.fraccion * 100) }))
  };
}

/** El log de una partida, reducido a los hitos que cuentan una historia. */
export function hitosDeLaPartida(testigo, enc) {
  if (!testigo) return null;
  const nombre = (id) => {
    if (id === 'malakh') return 'Malakh';
    const e = enc.enemigos.find(x => x.id === id);
    return e ? (e.etiqueta || e.arquetipo) : id;
  };
  const interesantes = ['baja', 'suelta', 'equipa', 'desmaterializa', 'descarte',
                        'agotada', 'guardiaRota', 'bebe', 'sealBreak', 'victoria', 'derrota'];
  return {
    duracion: testigo.tiempo,
    resultado: testigo.razonFin,
    vidaFinal: testigo.hpFinal,
    pocionesBebidas: testigo.pocionesBebidas,
    hitos: testigo.eventos
      .filter(e => interesantes.includes(e.tipo))
      .map(e => ({
        t: e.t,
        que: e.tipo,
        quien: e.agente ? nombre(e.agente) : undefined,
        arma: e.arma || undefined,
        motivo: e.motivo || undefined
      }))
  };
}
