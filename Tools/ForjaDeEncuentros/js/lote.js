// Lote de simulaciones y panel de veredicto.
//
// Esto es la razon de existir de la herramienta: contestar con numeros la
// afirmacion del §5.2 del PDF, que hasta ahora nadie habia medido.
//
// Fase A mide lo que se puede medir con espada sola:
//   - ¿es ganable sin armas temporales?           (§7.3, anti soft-lock)
//   - ¿el orden de bajas cambia algo?             (§5, mitad de la pregunta)
//   - ¿la arena enseña algo o es un paseo?
// La otra mitad —¿la lanza acorta la pelea?— llega en la Fase B.

import { Simulacion } from './sim.js';
import { crearPoliticas, POLITICA_BASE } from './politicas.js';
import { validar } from './esquema.js';
import { mediana, percentil, media } from './rng.js';

export const PARTIDAS_POR_DEFECTO = 200;

export function correrLote(encuentro, calibracion, opciones = {}) {
  const n = opciones.partidas || PARTIDAS_POR_DEFECTO;
  const semillaBase = opciones.semillaBase ?? 1234;
  const politicas = crearPoliticas();

  const porPolitica = {};
  let testigo = null;

  for (const pol of politicas) {
    const resultados = [];
    for (let i = 0; i < n; i++) {
      const semilla = semillaBase + i;
      const sim = new Simulacion(encuentro, calibracion, pol, semilla);
      resultados.push(sim.correr());
    }
    porPolitica[pol.id] = {
      id: pol.id,
      nombre: pol.nombre,
      descripcion: pol.descripcion,
      resultados,
      resumen: resumir(resultados)
    };
  }

  // Partida testigo: la mediana de la ruta guionizada, grabada para el reproductor.
  const guion = porPolitica['guionizada'];
  if (guion) {
    const victorias = guion.resultados.filter(r => r.victoria);
    const muestra = (victorias.length ? victorias : guion.resultados)
      .slice().sort((a, b) => a.tiempo - b.tiempo);
    const elegida = muestra[Math.floor(muestra.length / 2)];
    if (elegida) {
      const pol = crearPoliticas().find(p => p.id === 'guionizada');
      const sim = new Simulacion(encuentro, calibracion, pol, elegida.semilla, { grabar: true });
      testigo = sim.correr();
    }
  }

  return {
    partidas: n,
    porPolitica,
    testigo,
    veredicto: dictaminar(encuentro, calibracion, porPolitica, n)
  };
}

function resumir(resultados) {
  const tiemposVictoria = resultados.filter(r => r.victoria).map(r => r.tiempo);
  const danos = resultados.filter(r => r.victoria).map(r => r.danoRecibido);
  const todos = resultados.map(r => r.tiempo);
  return {
    partidas: resultados.length,
    victorias: resultados.filter(r => r.victoria).length,
    tasaVictoria: resultados.filter(r => r.victoria).length / resultados.length,
    porTiempo: resultados.filter(r => r.razonFin === 'tiempo').length,
    porMuerte: resultados.filter(r => r.razonFin === 'muerte').length,
    tiempoMediana: tiemposVictoria.length ? +mediana(tiemposVictoria).toFixed(1) : null,
    tiempoP10: tiemposVictoria.length ? +percentil(tiemposVictoria, 0.1).toFixed(1) : null,
    tiempoP90: tiemposVictoria.length ? +percentil(tiemposVictoria, 0.9).toFixed(1) : null,
    tiempoMedioTodas: +media(todos).toFixed(1),
    danoMediana: danos.length ? +mediana(danos).toFixed(1) : null,
    danoP90: danos.length ? +percentil(danos, 0.9).toFixed(1) : null,
    hpFinalMediana: resultados.filter(r => r.victoria).length
      ? +mediana(resultados.filter(r => r.victoria).map(r => r.hpFinal)).toFixed(1) : null,
    danoPorFuente: agregarFuentes(resultados)
  };
}

function agregarFuentes(resultados) {
  const total = {};
  for (const r of resultados) {
    for (const [k, v] of Object.entries(r.danoPorFuente || {})) {
      total[k] = (total[k] || 0) + v;
    }
  }
  const suma = Object.values(total).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(total)
    .map(([arquetipo, v]) => ({ arquetipo, total: +v.toFixed(0), fraccion: v / suma }))
    .sort((a, b) => b.total - a.total);
}

// ------------------------------------------------------------------ veredicto

/** Cada puerta: {id, titulo, estado: 'ok'|'aviso'|'fallo'|'na', texto, referencia} */
function dictaminar(encuentro, calibracion, porPolitica, n) {
  const puertas = [];
  const base = porPolitica[POLITICA_BASE];
  const guion = porPolitica['guionizada'];

  // --- 1. Alcanzabilidad (estatica, sin simular) ---
  const problemas = validar(encuentro);
  const inalcanzables = problemas.filter(p => p.codigo === 'inalcanzable');
  puertas.push({
    id: 'alcanzable',
    titulo: 'Todo enemigo alcanzable a pie',
    referencia: '§7.3 Evitar soft-locks',
    estado: inalcanzables.length ? 'fallo' : 'ok',
    texto: inalcanzables.length
      ? inalcanzables.map(p => p.texto).join(' ')
      : 'Ningun enemigo queda fuera del alcance de la espada por geometria.'
  });

  // --- 2. Ganable solo con espada ---
  const tasa = base?.resumen.tasaVictoria ?? 0;
  puertas.push({
    id: 'ganable-espada',
    titulo: 'Ganable solo con la espada base',
    referencia: '§5.2 Regla de oro / §12 Criterios de aceptacion',
    estado: tasa >= 0.90 ? 'ok' : tasa >= 0.70 ? 'aviso' : 'fallo',
    texto: `La politica "${base?.nombre}" gana el ${(tasa * 100).toFixed(0)}% de ${n} partidas`
      + (base?.resumen.porMuerte ? `, muere en ${base.resumen.porMuerte}` : '')
      + (base?.resumen.porTiempo ? ` y se queda sin tiempo en ${base.resumen.porTiempo}` : '')
      + '.',
    dato: tasa
  });

  // --- 3. El encuentro enseña algo ---
  //     Se mide por la vida con la que SALE, no por el daño recibido: con pociones
  //     el daño acumulado puede pasar de 100 y el porcentaje se volvia absurdo.
  const danoBase = base?.resumen.danoMediana;
  const hpMax = calibracion.malakh.hp;
  const hpFinal = base?.resumen.hpFinalMediana;
  const resto = hpFinal == null ? null : hpFinal / hpMax;
  const vidas = danoBase == null ? null : danoBase / hpMax;
  puertas.push({
    id: 'no-trivial',
    titulo: 'El encuentro cuesta algo',
    referencia: '§5 Puzzle tactico',
    estado: resto == null ? 'na' : resto > 0.85 ? 'aviso' : resto < 0.12 ? 'aviso' : 'ok',
    texto: resto == null
      ? 'Sin victorias que medir.'
      : resto > 0.85
        ? `Malakh termina con el ${(resto * 100).toFixed(0)}% de vida casi sin despeinarse. La arena no enseña nada.`
        : resto < 0.12
          ? `Malakh termina con el ${(resto * 100).toFixed(0)}% de vida: gana por los pelos en la mediana. Con un error de mas, muere.`
          : `Termina con el ${(resto * 100).toFixed(0)}% de vida tras encajar ${danoBase} de daño`
            + (vidas > 1 ? ` (${vidas.toFixed(1)} barras, o sea que se cura por el camino)` : '')
            + '. Cuesta sin ahogar.',
    dato: resto
  });

  // --- 4. ¿Importa el orden de bajas? ---
  if (guion && base && guion.resumen.tiempoMediana != null && base.resumen.tiempoMediana != null) {
    const dT = (guion.resumen.tiempoMediana - base.resumen.tiempoMediana) / base.resumen.tiempoMediana;
    const dD = base.resumen.danoMediana
      ? (guion.resumen.danoMediana - base.resumen.danoMediana) / base.resumen.danoMediana
      : 0;
    const mejora = dT <= -0.08 || dD <= -0.15;
    const igual = Math.abs(dT) < 0.08 && Math.abs(dD) < 0.15;
    puertas.push({
      id: 'orden-importa',
      titulo: 'El orden de bajas cambia el resultado',
      referencia: '§5 Orden de bajas implicito',
      estado: mejora ? 'ok' : igual ? 'aviso' : 'fallo',
      texto: mejora
        ? `Tu orden previsto es mejor que atacar al mas cercano: ${pct(dT)} de tiempo, ${pct(dD)} de daño.`
        : igual
          ? `Tu orden previsto y "atacar al mas cercano" dan practicamente lo mismo (${pct(dT)} tiempo, ${pct(dD)} daño). La composicion no premia leer la arena.`
          : `Tu orden previsto es PEOR que atacar al mas cercano: ${pct(dT)} de tiempo, ${pct(dD)} de daño. O el orden esta mal, o la arena no es lo que crees.`,
      dato: { dT, dD }
    });
  }

  // --- 5. Watchdog del §7.3 ---
  const atascos = Object.values(porPolitica).reduce((a, p) => a + p.resumen.porTiempo, 0);
  puertas.push({
    id: 'watchdog',
    titulo: 'Sin partidas atascadas',
    referencia: '§7.3 watchdog de arena sellada',
    estado: atascos === 0 ? 'ok' : atascos > n * 0.05 ? 'fallo' : 'aviso',
    texto: atascos === 0
      ? 'Ninguna partida agoto el limite de tiempo.'
      : `${atascos} partidas agotaron el limite. Suele ser un enemigo que no se puede alcanzar o un arquero que huye sin fin.`,
    dato: atascos
  });

  // --- avisos estaticos que no son puertas ---
  const otros = problemas.filter(p => p.codigo !== 'inalcanzable');

  const fallos = puertas.filter(p => p.estado === 'fallo').length;
  const avisos = puertas.filter(p => p.estado === 'aviso').length;
  return {
    puertas,
    problemasEstaticos: otros,
    resumen: fallos ? 'fallo' : avisos ? 'aviso' : 'ok',
    titular: fallos
      ? `${fallos} puerta${fallos > 1 ? 's' : ''} en rojo: no lo lleves a Unreal todavia.`
      : avisos
        ? `Pasa, con ${avisos} aviso${avisos > 1 ? 's' : ''} que merecen una vuelta.`
        : 'Las cinco puertas en verde. Este encuentro se sostiene solo con espada.'
  };
}

function pct(x) {
  const s = (x * 100).toFixed(0);
  return x <= 0 ? `${s}%` : `+${s}%`;
}
