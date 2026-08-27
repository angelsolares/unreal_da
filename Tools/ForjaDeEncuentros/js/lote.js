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

/**
 * 200 se quedaban cortas y el veredicto lo pagaba.
 *
 * Con 200 partidas, una composicion daba las nueve puertas en verde y la MISMA
 * composicion con 2000 dejaba dos en ambar. No era el encuentro: era la muestra.
 * Junto con el error tipico que ahora acompaña a cada diferencia, 400 deja los
 * margenes en el orden del 3% y ya se puede creer lo que dice el panel.
 */
export const PARTIDAS_POR_DEFECTO = 400;

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
    // LAS MEDIAS SON LAS QUE DECIDEN, y la mediana solo se enseña.
    //
    // El daño de este juego llega en escalones de 20 y de 30, asi que la
    // mediana de las partidas ganadas SALTA entre 70 y 100 segun la muestra: un
    // 30% de diferencia que no es del encuentro, es del muestreo. Con 200
    // partidas una composicion daba las nueve puertas en verde y con 500 las
    // mismas dos se caian a ambar. Un veredicto que depende de cuantas partidas
    // corriste no es un veredicto.
    tiempoMedio: tiempos.length ? +media(tiempos).toFixed(1) : null,
    danoMedio: danos.length ? +media(danos).toFixed(1) : null,
    hpFinalMedia: gan.length ? +media(gan.map(r => r.hpFinal)).toFixed(1) : null,
    // Y su error tipico, que es lo que separa "mejor" de "parece mejor".
    tiempoError: errorTipico(tiempos),
    danoError: errorTipico(danos),
    pocionesMediana: gan.length ? +mediana(gan.map(r => r.pocionesBebidas)).toFixed(1) : null,
    armasPorPartida: +media(resultados.map(r => (r.armasRecogidas || []).length)).toFixed(2),
    descartesPorPartida: +media(resultados.map(r => r.descartesUsados || 0)).toFixed(2),
    maxDropsSimultaneos: Math.max(0, ...resultados.map(r => r.maxDropsSimultaneos || 0)),
    // Cuantos enemigos le llegaron a la vez, en el peor caso y en la mediana.
    // Con activacion escalonada (§6) es la cifra que explica el resultado: el
    // techo de la espada sola son dos, y el tercero es un acantilado.
    maxEnemigosALaVez: Math.max(0, ...resultados.map(r => r.maxEnemigosALaVez || 0)),
    enemigosALaVezMediana: +mediana(resultados.map(r => r.maxEnemigosALaVez || 0)).toFixed(1),
    recogidas,
    danoPorFuente: agregar(resultados, 'danoPorFuente'),
    danoPorArma: agregar(resultados, 'danoPorArma')
  };
}

/**
 * Error tipico de la media. Sin esto, una diferencia del 16% con 200 partidas y
 * una del 16% con 2000 valen lo mismo en el panel, y no valen lo mismo.
 */
function errorTipico(xs) {
  if (!xs || xs.length < 2) return 0;
  const m = media(xs);
  const v = xs.reduce((a, x) => a + (x - m) ** 2, 0) / (xs.length - 1);
  return Math.sqrt(v / xs.length);
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
  //
  // Dos formas de dejar a un enemigo fuera del alcance, y las dos son el mismo
  // soft-lock: por geometria (flota en un balcon sin rampa) o por tiempo (su
  // oleada no se activa nunca). La segunda no la ve nadie mirando el mapa.
  const inalcanzables = problemas.filter(
    p => p.codigo === 'inalcanzable' || p.codigo === 'oleada-inalcanzable');
  puertas.push({
    id: 'alcanzable',
    titulo: 'Todo enemigo alcanzable, y toda oleada activable',
    referencia: '§7.3 Evitar soft-locks',
    estado: inalcanzables.length ? 'fallo' : 'ok',
    texto: inalcanzables.length
      ? inalcanzables.map(p => p.texto).join(' ')
      : 'Ningun enemigo queda fuera del alcance de la espada, ni esperando una oleada que no llega.'
  });

  // --- 2. Ganable solo con espada, PERO QUE DUELA ---
  //
  // ESTA PUERTA AVISA POR LOS DOS LADOS, y el motivo es un criterio de Angel del 26/08:
  // «los combates siempre deben ser posibles de ganar sólo con la espada pero que esto sea
  // bastante complicado, que se sienta que es necesario el arsenal».
  //
  // Hasta entonces la puerta daba OK a partir del 90% y con eso premiaba justo lo
  // contrario: un encuentro que se pasa de calle con la espada deja el arsenal en
  // decorado, y el §5.2 no promete un paseo, promete que NUNCA dependas de un drop. Las
  // dos mitades del criterio son bandas distintas y hay que medirlas por separado:
  //
  //     < 70%   FALLO   no se puede con espada sola: cada drop pasa a ser una trampa
  //   70 - 90%  OK      ganable y cuesta — la zona que el diseño busca
  //     > 90%   AVISO   se pasa comodo: el arsenal no se siente necesario
  //
  // OJO CON LEER ESTE NUMERO COMO SI FUERA EL DEL JUGADOR. Es la tasa de una politica
  // guionizada: no lee el encuentro, no cambia de plan y no aprende entre intentos. Sirve
  // para descartar los extremos —imposible o trivial—, no para afinar la dificultad. Eso
  // se decide jugando.
  const tasa = base?.resumen.tasaVictoria ?? 0;
  const comodo = tasa > 0.90;
  puertas.push({
    id: 'ganable-espada',
    titulo: 'Ganable solo con la espada base, y que cueste',
    referencia: '§5.2 Regla de oro / §12 Criterios',
    estado: tasa < 0.70 ? 'fallo' : comodo ? 'aviso' : 'ok',
    texto: `Sin tocar un arma del suelo, "${base?.nombre}" gana el ${(tasa * 100).toFixed(0)}% de ${n} partidas`
      + (base?.resumen.porMuerte ? `, muere en ${base.resumen.porMuerte}` : '')
      + (base?.resumen.porTiempo ? ` y se queda sin tiempo en ${base.resumen.porTiempo}` : '') + '.'
      + (comodo
        ? ' Se pasa comodo: por encima del 90% el arsenal no se siente necesario.'
        : tasa < 0.70
          ? ' No llega: por debajo del 70% cada drop es una trampa, y el §5.2 promete lo contrario.'
          : ' Ganable y cuesta, que es donde tiene que estar.'),
    dato: tasa
  });

  // --- 3. LA PREGUNTA DE LA FASE B: ¿la ventaja existe? ---
  if (vent && base) {
    const dT = delta(vent.resumen.tiempoMedio, base.resumen.tiempoMedio,
                     vent.resumen.tiempoError, base.resumen.tiempoError);
    const dD = delta(vent.resumen.danoMedio, base.resumen.danoMedio,
                     vent.resumen.danoError, base.resumen.danoError);
    const dV = (vent.resumen.tasaVictoria - base.resumen.tasaVictoria);
    // TRES SEÑALES QUE APUNTAN A LO MISMO SUMAN, y esto corrige un veredicto que
    // se contradecia a si mismo. Hasta el 26/08 bastaba con que UNA de las tres
    // cruzara su liston, y si las tres mejoraban un poco sin llegar a el, el
    // panel decia «recoger armas da practicamente igual» de un +10 pts de
    // victoria, un -8% de tiempo y un -11% de daño. Eso no es dar igual.
    //
    // Se mantiene la via fuerte —una sola señal grande basta— y se añade la
    // acumulada: DOS de las tres, con un liston mas bajo, tambien cuentan. Que
    // dos medidas independientes se muevan a la vez y en el mismo sentido es
    // mejor evidencia que una sola rozando el umbral, no peor.
    const fuerte = mejorQue(dT, -0.10) || mejorQue(dD, -0.15) || dV >= 0.15;
    const flojas = [mejorQue(dT, -0.05), mejorQue(dD, -0.08), dV >= 0.05]
      .filter(Boolean).length;
    const mejora = fuerte || flojas >= 2;
    const fuerteMal = peorQue(dT, 0.10) || peorQue(dD, 0.20) || dV <= -0.15;
    const flojasMal = [peorQue(dT, 0.05), peorQue(dD, 0.08), dV <= -0.05]
      .filter(Boolean).length;
    const empeora = fuerteMal || flojasMal >= 2;
    puertas.push({
      id: 'ventaja-existe',
      titulo: 'Las armas temporales pagan',
      referencia: '§5.2 / §4 Arsenal de oportunidad',
      estado: mejora ? 'ok' : empeora ? 'fallo' : 'aviso',
      texto: (vent.resumen.armasPorPartida < 0.5)
        ? `La ruta de ventaja apenas recoge armas (${vent.resumen.armasPorPartida} por partida). No hay ventaja que medir: revisa los drops.`
        : mejora
          ? `Recogiendo armas: ${pct(dV, true)} de victorias, ${pct(dT)} de tiempo, ${pct(dD)} de daño. ${fuerte ? "La mecanica paga." : "Paga por acumulacion: ninguna señal es grande, pero " + flojas + " de 3 van a favor."}`
          : empeora
            ? `Recoger armas sale PEOR que no recogerlas: ${pct(dV, true)} de victorias, ${pct(dT)} de tiempo, ${pct(dD)} de daño. O las armas estan flojas, o el desvio para cogerlas cuesta mas de lo que dan.`
            : `Recoger armas da practicamente igual (${pct(dV, true)} victorias, ${pct(dT)} tiempo, ${pct(dD)} daño). El arsenal es decorativo en esta arena.`,
      dato: { dT, dD, dV }
    });
  }

  // --- 4. El encuentro enseña algo ---
  const ref = vent?.resumen.hpFinalMedia != null ? vent : base;
  const resto = ref?.resumen.hpFinalMedia == null ? null : ref.resumen.hpFinalMedia / calibracion.malakh.hp;
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
          : `Termina con el ${(resto * 100).toFixed(0)}% de vida de media (mediana ${ref.resumen.hpFinalMediana}) y ${ref.resumen.pocionesMediana} pociones bebidas. Cuesta sin ahogar.`,
    dato: resto
  });

  // --- 5. ¿Importa el orden, aun sin armas? ---
  if (guion && base && guion.resumen.tiempoMedio != null && base.resumen.tiempoMedio != null) {
    const dT = delta(guion.resumen.tiempoMedio, base.resumen.tiempoMedio,
                     guion.resumen.tiempoError, base.resumen.tiempoError);
    const dD = delta(guion.resumen.danoMedio, base.resumen.danoMedio,
                     guion.resumen.danoError, base.resumen.danoError);
    const mejora = mejorQue(dT, -0.08) || mejorQue(dD, -0.15);
    const igual = indistinguible(dT, 0.08) && indistinguible(dD, 0.15);
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
  //
  // GARANTIZADO es permiso de mano Y probabilidad entera. Un Mercy Drop
  // (probabilidad 0, piedad activa) tiene permiso pero NO promete llegar:
  // solo aparece si el jugador va mal, y exigirle el 70% de recogidas es
  // pedirle a la red de seguridad que se use en cada partida. Salio el 26/08
  // al adoptar la piedad del §8: la puerta lo marco en rojo siendo la piedad
  // exactamente lo que debia ser.
  const garantizados = encuentro.enemigos.filter(e =>
    (e.drop?.principal || e.drop?.secundaria) && (e.drop?.probabilidad ?? 1) >= 1);
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
          ? malas.map(f => `"${f.etiqueta}" lleva ${f.nombreArma || 'su arma'} y desde la puerta ${
              f.estado === 'ausente'
                ? 'NO ESTA: su oleada entra despues, asi que el jugador no puede contar con esa arma al planear'
                : f.estado === 'tapado'
                  ? 'esta TAPADO'
                  : `esta a ${f.distancia} cm, demasiado lejos para leerse`}.`).join(' ')
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

/**
 * Diferencia relativa CON su margen. Devuelve `{valor, error}`.
 *
 * El margen se propaga a lo bruto desde los errores tipicos de las dos medias.
 * No es una prueba de hipotesis: es lo justo para que una puerta no se ponga
 * verde por un 16% que en realidad es un 13% con la muestra de al lado.
 */
function delta(a, b, ea = 0, eb = 0) {
  if (a == null || b == null || !b) return null;
  return {
    valor: (a - b) / b,
    error: Math.sqrt(ea * ea + eb * eb) / Math.abs(b)
  };
}

/** ¿La diferencia cruza el umbral CON su margen a favor? */
const mejorQue = (d, umbral) => d != null && d.valor + d.error <= umbral;
const peorQue = (d, umbral) => d != null && d.valor - d.error >= umbral;
const indistinguible = (d, umbral) => d != null && Math.abs(d.valor) - d.error < umbral;

function pct(x, esPuntos = false) {
  if (x && typeof x === 'object') {
    const s = pct(x.valor, esPuntos);
    return `${s} ±${(x.error * 100).toFixed(0)}`;
  }
  if (x == null) return '—';
  if (esPuntos) {
    const s = (x * 100).toFixed(0);
    return x >= 0 ? `+${s} pts` : `${s} pts`;
  }
  const s = (x * 100).toFixed(0);
  return x <= 0 ? `${s}%` : `+${s}%`;
}
