// Lote de simulaciones y panel de veredicto.
//
// Esto es la razon de existir de la herramienta: contestar con numeros la
// afirmacion del §5.2 del PDF, que hasta ahora nadie habia medido.
//
//   "la ruta tactica ideal debe reducir tiempo, riesgo o recursos,
//    pero nunca ser requisito"
//
// Son DOS afirmaciones y cada una tiene su puerta:
//   - la ruta con armas tiene que ser MEJOR      -> puerta "la ventaja existe"
//   - la espada sola tiene que BASTAR            -> puerta "ganable solo con espada"
// Un encuentro que falla la primera no necesita armas temporales.
// Un encuentro que falla la segunda incumple el §12.

import { Simulacion } from './sim.js';
import { crearPoliticas, crearPolitica, POLITICA_BASE, POLITICA_VENTAJA } from './politicas.js';
import { validar } from './esquema.js';
import { resumenDeLectura } from './lectura.js';
import { mediana, percentil, media } from './rng.js';

export const PARTIDAS_POR_DEFECTO = 200;

export function correrLote(encuentro, calibracion, armas, opciones = {}) {
  const n = opciones.partidas || PARTIDAS_POR_DEFECTO;
  const semillaBase = opciones.semillaBase ?? 1234;

  const porPolitica = {};
  for (const pol of crearPoliticas()) {
    const resultados = [];
    for (let i = 0; i < n; i++) {
      resultados.push(new Simulacion(encuentro, calibracion, armas, pol, semillaBase + i).correr());
    }
    porPolitica[pol.id] = {
      id: pol.id, nombre: pol.nombre, descripcion: pol.descripcion,
      resultados, resumen: resumir(resultados)
    };
  }

  return {
    partidas: n,
    porPolitica,
    testigo: grabarTestigo(encuentro, calibracion, armas, porPolitica[POLITICA_VENTAJA]),
    veredicto: dictaminar(encuentro, calibracion, armas, porPolitica, n)
  };
}

/** Graba la partida mediana de la ruta de ventaja, para el reproductor. */
function grabarTestigo(encuentro, calibracion, armas, grupo) {
  if (!grupo) return null;
  const victorias = grupo.resultados.filter(r => r.victoria);
  const muestra = (victorias.length ? victorias : grupo.resultados)
    .slice().sort((a, b) => a.tiempo - b.tiempo);
  const elegida = muestra[Math.floor(muestra.length / 2)];
  if (!elegida) return null;
  return new Simulacion(encuentro, calibracion, armas, crearPolitica(POLITICA_VENTAJA),
                        elegida.semilla, { grabar: true }).correr();
}

function resumir(resultados) {
  const gan = resultados.filter(r => r.victoria);
  const tiempos = gan.map(r => r.tiempo);
  const danos = gan.map(r => r.danoRecibido);

  const recogidas = {};
  for (const r of resultados) {
    for (const a of r.armasRecogidas || []) {
      recogidas[a.familia] = (recogidas[a.familia] || 0) + 1;
    }
  }

  return {
    partidas: resultados.length,
    victorias: gan.length,
    tasaVictoria: gan.length / resultados.length,
    porTiempo: resultados.filter(r => r.razonFin === 'tiempo').length,
    porMuerte: resultados.filter(r => r.razonFin === 'muerte').length,
    tiempoMediana: tiempos.length ? +mediana(tiempos).toFixed(1) : null,
    tiempoP10: tiempos.length ? +percentil(tiempos, 0.1).toFixed(1) : null,
    tiempoP90: tiempos.length ? +percentil(tiempos, 0.9).toFixed(1) : null,
    tiempoMedioTodas: +media(resultados.map(r => r.tiempo)).toFixed(1),
    danoMediana: danos.length ? +mediana(danos).toFixed(1) : null,
    hpFinalMediana: gan.length ? +mediana(gan.map(r => r.hpFinal)).toFixed(1) : null,
    pocionesMediana: gan.length ? +mediana(gan.map(r => r.pocionesBebidas)).toFixed(1) : null,
    armasPorPartida: +media(resultados.map(r => (r.armasRecogidas || []).length)).toFixed(2),
    descartesPorPartida: +media(resultados.map(r => r.descartesUsados || 0)).toFixed(2),
    maxDropsSimultaneos: Math.max(0, ...resultados.map(r => r.maxDropsSimultaneos || 0)),
    recogidas,
    danoPorFuente: agregar(resultados, 'danoPorFuente'),
    danoPorArma: agregar(resultados, 'danoPorArma')
  };
}

function agregar(resultados, campo) {
  const total = {};
  for (const r of resultados) {
    for (const [k, v] of Object.entries(r[campo] || {})) total[k] = (total[k] || 0) + v;
  }
  const suma = Object.values(total).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(total)
    .map(([clave, v]) => ({ clave, arquetipo: clave, total: +v.toFixed(0), fraccion: v / suma }))
    .sort((a, b) => b.total - a.total);
}

// ------------------------------------------------------------------ veredicto

function dictaminar(encuentro, calibracion, armas, porPolitica, n) {
  const puertas = [];
  const base = porPolitica[POLITICA_BASE];
  const guion = porPolitica['guionizada'];
  const vent = porPolitica[POLITICA_VENTAJA];
  const problemas = validar(encuentro);

  // --- 1. Alcanzabilidad (estatica) ---
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
    referencia: '§5.2 Regla de oro / §12 Criterios',
    estado: tasa >= 0.90 ? 'ok' : tasa >= 0.70 ? 'aviso' : 'fallo',
    texto: `Sin tocar un arma del suelo, "${base?.nombre}" gana el ${(tasa * 100).toFixed(0)}% de ${n} partidas`
      + (base?.resumen.porMuerte ? `, muere en ${base.resumen.porMuerte}` : '')
      + (base?.resumen.porTiempo ? ` y se queda sin tiempo en ${base.resumen.porTiempo}` : '') + '.',
    dato: tasa
  });

  // --- 3. LA PREGUNTA DE LA FASE B: ¿la ventaja existe? ---
  if (vent && base) {
    const dT = delta(vent.resumen.tiempoMediana, base.resumen.tiempoMediana);
    const dD = delta(vent.resumen.danoMediana, base.resumen.danoMediana);
    const dV = (vent.resumen.tasaVictoria - base.resumen.tasaVictoria);
    const mejora = (dT != null && dT <= -0.10) || (dD != null && dD <= -0.15) || dV >= 0.15;
    const empeora = (dT != null && dT >= 0.10) || (dD != null && dD >= 0.20) || dV <= -0.15;
    puertas.push({
      id: 'ventaja-existe',
      titulo: 'Las armas temporales pagan',
      referencia: '§5.2 / §4 Arsenal de oportunidad',
      estado: mejora ? 'ok' : empeora ? 'fallo' : 'aviso',
      texto: (vent.resumen.armasPorPartida < 0.5)
        ? `La ruta de ventaja apenas recoge armas (${vent.resumen.armasPorPartida} por partida). No hay ventaja que medir: revisa los drops.`
        : mejora
          ? `Recogiendo armas: ${pct(dV, true)} de victorias, ${pct(dT)} de tiempo, ${pct(dD)} de daño. La mecanica paga.`
          : empeora
            ? `Recoger armas sale PEOR que no recogerlas: ${pct(dV, true)} de victorias, ${pct(dT)} de tiempo, ${pct(dD)} de daño. O las armas estan flojas, o el desvio para cogerlas cuesta mas de lo que dan.`
            : `Recoger armas da practicamente igual (${pct(dV, true)} victorias, ${pct(dT)} tiempo, ${pct(dD)} daño). El arsenal es decorativo en esta arena.`,
      dato: { dT, dD, dV }
    });
  }

  // --- 4. El encuentro enseña algo ---
  const ref = vent?.resumen.hpFinalMediana != null ? vent : base;
  const resto = ref?.resumen.hpFinalMediana == null ? null : ref.resumen.hpFinalMediana / calibracion.malakh.hp;
  puertas.push({
    id: 'no-trivial',
    titulo: 'El encuentro cuesta algo',
    referencia: '§5 Puzzle tactico',
    estado: resto == null ? 'na' : resto > 0.85 ? 'aviso' : resto < 0.12 ? 'aviso' : 'ok',
    texto: resto == null
      ? 'Sin victorias que medir.'
      : resto > 0.85
        ? `Termina con el ${(resto * 100).toFixed(0)}% de vida casi sin despeinarse. La arena no enseña nada.`
        : resto < 0.12
          ? `Termina con el ${(resto * 100).toFixed(0)}% de vida: gana por los pelos en la mediana. Con un error de mas, muere.`
          : `Termina con el ${(resto * 100).toFixed(0)}% de vida y ${ref.resumen.pocionesMediana} pociones bebidas. Cuesta sin ahogar.`,
    dato: resto
  });

  // --- 5. ¿Importa el orden, aun sin armas? ---
  if (guion && base && guion.resumen.tiempoMediana != null && base.resumen.tiempoMediana != null) {
    const dT = delta(guion.resumen.tiempoMediana, base.resumen.tiempoMediana);
    const dD = delta(guion.resumen.danoMediana, base.resumen.danoMediana);
    const mejora = dT <= -0.08 || dD <= -0.15;
    const igual = Math.abs(dT) < 0.08 && Math.abs(dD) < 0.15;
    puertas.push({
      id: 'orden-importa',
      titulo: 'El orden de bajas ya cambia algo por si solo',
      referencia: '§5 Orden de bajas implicito',
      estado: mejora ? 'ok' : igual ? 'aviso' : 'fallo',
      texto: mejora
        ? `Aun sin armas, tu orden es mejor que ir al mas cercano: ${pct(dT)} tiempo, ${pct(dD)} daño.`
        : igual
          ? `Sin armas, tu orden y "el mas cercano" dan lo mismo (${pct(dT)} tiempo, ${pct(dD)} daño). Toda la ventaja depende del arsenal.`
          : `Sin armas tu orden es PEOR (${pct(dT)} tiempo, ${pct(dD)} daño). Puede estar bien si las armas lo compensan — mira la puerta de arriba.`,
      dato: { dT, dD }
    });
  }

  // --- 6. Los drops garantizados llegan a las manos ---
  const garantizados = encuentro.enemigos.filter(e => e.drop?.principal || e.drop?.secundaria);
  if (garantizados.length && vent) {
    const llegan = garantizados.map(e => {
      const veces = vent.resultados.filter(r =>
        (r.armasRecogidas || []).some(a => a.origen === e.id)).length;
      return { id: e.id, etiqueta: e.etiqueta || e.id, fraccion: veces / vent.resultados.length };
    });
    const peor = llegan.reduce((a, b) => (a.fraccion <= b.fraccion ? a : b));
    puertas.push({
      id: 'drop-llega',
      titulo: 'La llave tactica llega a las manos',
      referencia: '§4.1 / §8 Guaranteed Tactical Drop',
      estado: peor.fraccion >= 0.7 ? 'ok' : peor.fraccion >= 0.3 ? 'aviso' : 'fallo',
      texto: peor.fraccion >= 0.7
        ? `Los ${garantizados.length} drops garantizados se recogen casi siempre (el peor, "${peor.etiqueta}", en el ${(peor.fraccion * 100).toFixed(0)}%).`
        : `El drop garantizado de "${peor.etiqueta}" solo llega a las manos en el ${(peor.fraccion * 100).toFixed(0)}% de las partidas. Marcarlo como garantizado no sirve de nada si cae donde no se pasa, o si expira antes (TTL ${armas.reglas.ttlEnSuelo}s).`,
      dato: llegan
    });
  }

  // --- 7. La arena se LEE desde la puerta (§5.1) ---
  const lect = resumenDeLectura(encuentro, calibracion);
  if (lect.filas.length) {
    const malas = lect.llavesIlegibles;
    puertas.push({
      id: 'se-lee',
      titulo: 'La llave tactica se ve desde la entrada',
      referencia: '§5.1 Lectura antes que UI',
      estado: !lect.llaves.length ? 'na' : malas.length ? (malas.length === lect.llaves.length ? 'fallo' : 'aviso') : 'ok',
      texto: !lect.llaves.length
        ? 'No hay ningun drop garantizado que leer.'
        : malas.length
          ? malas.map(f => `"${f.etiqueta}" lleva ${f.nombreArma || 'su arma'} y desde la puerta esta ${f.estado === 'tapado' ? 'TAPADO' : `a ${f.distancia} cm, demasiado lejos para leerse`}.`).join(' ')
            + ' El §5.1 pide que la silueta comunique la estrategia; si no se ve, la ruta no se descubre, se tropieza.'
          : `Las ${lect.llaves.length} llaves tacticas se ven al entrar (la mas pequeña ocupa ${Math.min(...lect.llaves.map(f => f.grados)).toFixed(1)}° de silueta).`,
      dato: lect
    });
  }

  // --- 8. No saturar el suelo (§8) ---
  const maxDrops = Math.max(0, ...Object.values(porPolitica).map(p => p.resumen.maxDropsSimultaneos));
  puertas.push({
    id: 'no-saturar',
    titulo: 'El suelo no se llena de armas',
    referencia: '§8 NO LOOT GAME',
    estado: maxDrops <= 2 ? 'ok' : maxDrops <= 3 ? 'aviso' : 'fallo',
    texto: maxDrops <= 2
      ? `Como mucho ${maxDrops} armas en el suelo a la vez. La decision sigue siendo una decision.`
      : `Hasta ${maxDrops} armas en el suelo a la vez. El PDF avisa (§8): con un arsenal tirado por ahi se diluye la eleccion. Baja el TTL o pon mas "No Drop".`,
    dato: maxDrops
  });

  // --- 9. Watchdog del §7.3 ---
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

  const fallos = puertas.filter(p => p.estado === 'fallo').length;
  const avisos = puertas.filter(p => p.estado === 'aviso').length;
  return {
    puertas,
    problemasEstaticos: problemas.filter(p => p.codigo !== 'inalcanzable'),
    resumen: fallos ? 'fallo' : avisos ? 'aviso' : 'ok',
    titular: fallos
      ? `${fallos} puerta${fallos > 1 ? 's' : ''} en rojo: no lo lleves a Unreal todavia.`
      : avisos
        ? `Pasa, con ${avisos} aviso${avisos > 1 ? 's' : ''} que merecen una vuelta.`
        : 'Todas las puertas en verde. La espada basta y las armas pagan.'
  };
}

function delta(a, b) {
  if (a == null || b == null || !b) return null;
  return (a - b) / b;
}

function pct(x, esPuntos = false) {
  if (x == null) return '—';
  if (esPuntos) {
    const s = (x * 100).toFixed(0);
    return x >= 0 ? `+${s} pts` : `${s} pts`;
  }
  const s = (x * 100).toFixed(0);
  return x <= 0 ? `${s}%` : `+${s}%`;
}
