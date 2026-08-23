// Cliente de la capa de IA.
//
// Aqui esta la regla de la fase D, y no es negociable:
//
//     LA IA PROPONE, EL SIMULADOR DISPONE.
//
// Una variante generada no se enseña hasta que ha pasado por validar() y por el
// lote de 200 partidas. Lo que se ve en pantalla no es "lo que dijo el modelo",
// es "lo que dijo el modelo, y esto es lo que pasa cuando se juega". Si el
// veredicto la tumba, se enseña tumbada.
//
// La clave de OpenAI nunca pasa por aqui: vive en el proceso del servidor.

import { resumirParaIA, hitosDeLaPartida, expandirPropuesta, ESQUEMA_PROPUESTA } from './esquema-ia.js';
import { validar } from './esquema.js';
import { correrLote } from './lote.js';

const PARTIDAS_VARIANTE = 100;   // menos que las 200 del veredicto: son un cribado

async function llamar(ruta, cuerpo) {
  const r = await fetch(`/ia/${ruta}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(cuerpo)
  });
  const datos = await r.json().catch(() => ({ error: `Respuesta ilegible (HTTP ${r.status})` }));
  if (!r.ok) {
    const e = new Error(datos.error || `HTTP ${r.status}`);
    e.codigo = datos.codigo;
    e.bruto = datos.bruto;
    throw e;
  }
  return datos;
}

export async function estadoIA() {
  try {
    return await (await fetch('/ia/estado')).json();
  } catch (err) {
    return { disponible: false, motivo: 'El servidor no responde: ' + err.message };
  }
}

export async function criticar(enc, cal, lote) {
  const { texto } = await llamar('criticar', { datos: resumirParaIA(enc, cal, lote) });
  return texto;
}

export async function narrar(enc, testigo) {
  const datos = hitosDeLaPartida(testigo, enc);
  if (!datos) throw new Error('No hay partida testigo. Simula primero.');
  const { texto } = await llamar('narrar', { datos });
  return texto;
}

/**
 * Pide variantes y las JUZGA antes de devolverlas.
 * Cada una vuelve con su veredicto propio, y ordenadas por lo que dice el
 * simulador, no por el orden en que las escupio el modelo.
 */
export async function generarVariantes(enc, cal, armas, lote, alProgresar = () => {}) {
  alProgresar('Pidiendo variantes…');
  const respuesta = await llamar('variantes', {
    datos: resumirParaIA(enc, cal, lote),
    esquema: ESQUEMA_PROPUESTA,
    cuantas: 3
  });

  const propuestas = respuesta.variantes || [];
  if (!propuestas.length) throw new Error('El modelo no propuso ninguna variante.');

  const juzgadas = [];
  for (let i = 0; i < propuestas.length; i++) {
    const p = propuestas[i];
    alProgresar(`Simulando "${p.nombre}" (${i + 1} de ${propuestas.length})…`);
    await new Promise(r => setTimeout(r, 20));   // dejar pintar el progreso

    let encuentro, problemas, resultado = null, fallo = null;
    try {
      encuentro = expandirPropuesta(p, enc);
      problemas = validar(encuentro);
      // Un error de validacion no impide simular: el veredicto lo dira mejor.
      resultado = correrLote(encuentro, cal, armas, { partidas: PARTIDAS_VARIANTE });
    } catch (err) {
      fallo = err.message;
    }

    juzgadas.push({
      propuesta: p,
      encuentro,
      problemas: problemas || [],
      lote: resultado,
      fallo,
      nota: resultado ? puntuar(resultado) : -Infinity
    });
  }

  juzgadas.sort((a, b) => b.nota - a.nota);
  return juzgadas;
}

/**
 * Una nota para ordenar las variantes. No es un juicio de calidad: es el orden
 * en el que merece la pena mirarlas. Pesa lo que el PDF dice que importa —
 * que se pueda ganar con espada sola, y que las armas aporten algo.
 */
function puntuar(lote) {
  const p = (id) => lote.veredicto.puertas.find(x => x.id === id);
  const peso = { ok: 1, aviso: 0.4, na: 0.4, fallo: 0 };
  const clave = ['ganable-espada', 'ventaja-existe', 'no-trivial', 'se-lee', 'watchdog'];
  let n = 0;
  for (const id of clave) n += peso[p(id)?.estado ?? 'na'];
  return n / clave.length;
}
