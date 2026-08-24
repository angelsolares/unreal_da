// La capa de IA, del lado del servidor.
//
// Vive aqui y no en el navegador por una razon concreta: la clave de OpenAI.
// Una clave en el navegador es una clave publicada, y no hay truco que lo
// arregle. El navegador habla con este proceso; este proceso habla con OpenAI.
//
// Tres trabajos, y ninguno de ellos decide nada:
//   criticar  — lee el encuentro y su veredicto, y opina en el vocabulario del PDF
//   variantes — propone composiciones nuevas, que el SIMULADOR juzga despues
//   narrar    — convierte el log de una partida en la historia del §15
//
// Se carga de forma perezosa: si no hay clave o no esta instalado el paquete,
// el resto de la herramienta funciona igual y la interfaz lo dice.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const MODELO = process.env.OPENAI_MODEL || 'gpt-5.6-sol';
const AQUI = path.dirname(fileURLToPath(import.meta.url));

/**
 * Que hace cada enemigo, en palabras. Vive en datos/arquetipos.json para que se
 * pueda editar sin tocar codigo, y se lee en cada peticion: cambias el fichero,
 * recargas, y el modelo ya razona con lo nuevo. Sin reiniciar el servidor.
 */
function fichasDeArquetipos() {
  try {
    const j = JSON.parse(fs.readFileSync(path.join(AQUI, 'datos/arquetipos.json'), 'utf8'));
    const trozos = [];
    for (const [id, a] of Object.entries(j.arquetipos || {})) {
      trozos.push(
        `### ${id} — ${a.nombre}\n` +
        `Papel: ${a.papel}\n` +
        `Como pelea: ${a.comoPelea}\n` +
        `Como se le contesta: ${a.comoSeContesta}\n` +
        `Que aporta su arma: ${a.queAporta}\n` +
        `Donde colocarlo: ${a.dondeColocarlo}\n` +
        `Cuidado con: ${a.cuidadoCon}`
      );
    }
    const reglas = Object.values(j.reglasDeComposicion || {}).map(r => `- ${r}`).join('\n');
    // La ficha del jugador va PRIMERO. Sin ella el modelo juzgaba composiciones
    // contra un Malakh imaginario: no sabia ni lo que tarda en matar a uno.
    const m = j.malakh
      ? '\n\n## QUIEN LO JUEGA\n\n' + Object.entries(j.malakh)
          .filter(([k]) => k !== 'nombre')
          .map(([k, v]) => `${k}: ${v}`).join('\n')
      : '';
    return `${m}\n\n## QUE HACE CADA ENEMIGO\n\n${trozos.join('\n\n')}\n\n## AL COMPONER\n\n${reglas}`;
  } catch (err) {
    return `\n\n(No se pudo leer datos/arquetipos.json: ${err.message})`;
  }
}

let cliente = null;
let motivoNoDisponible = null;

async function obtenerCliente() {
  if (cliente) return cliente;
  if (!process.env.OPENAI_API_KEY) {
    motivoNoDisponible = 'Falta OPENAI_API_KEY en el entorno.';
    return null;
  }
  try {
    const { default: OpenAI } = await import('openai');
    cliente = new OpenAI();
    return cliente;
  } catch (err) {
    motivoNoDisponible = `Falta el paquete: npm install openai  (${err.message})`;
    return null;
  }
}

export async function estado() {
  const c = await obtenerCliente();
  return {
    disponible: !!c,
    modelo: MODELO,
    motivo: c ? null : motivoNoDisponible,
    nota: 'El modelo se cambia con la variable de entorno OPENAI_MODEL.'
  };
}

/**
 * Una llamada, con o sin schema.
 * Se intenta primero la Responses API y se cae a chat.completions si el SDK o
 * el modelo no la tienen. No se cual de las dos acepta este modelo, y prefiero
 * probar las dos a clavar la equivocada.
 */
async function pedir({ sistema, usuario, schema, nombreSchema, maxTokens = 16000 }) {
  const c = await obtenerCliente();
  if (!c) {
    const e = new Error(motivoNoDisponible);
    e.codigo = 'sin-ia';
    throw e;
  }

  if (c.responses?.create) {
    try {
      const r = await c.responses.create({
        model: MODELO,
        instructions: sistema,
        input: usuario,
        max_output_tokens: maxTokens,
        ...(schema ? {
          text: { format: { type: 'json_schema', name: nombreSchema, schema, strict: true } }
        } : {})
      });
      const texto = r.output_text ?? extraerDeResponses(r);
      // Este es un modelo de razonamiento: los tokens de razonamiento salen del
      // MISMO presupuesto que la respuesta. Si se acaba, el texto llega cortado a
      // media frase. Eso hay que DECIRLO, no colar media critica como si fuera
      // entera.
      if (r.status === 'incomplete') {
        return marcarCortado(texto, r.incomplete_details?.reason, r.usage);
      }
      if (texto) return texto;
    } catch (err) {
      // Si la Responses API no acepta este modelo, se prueba la otra puerta.
      if (!/not.*support|unknown|unrecognized|invalid.*model|404/i.test(err.message || '')) throw err;
    }
  }

  const r = await c.chat.completions.create({
    model: MODELO,
    max_completion_tokens: maxTokens,
    messages: [
      { role: 'system', content: sistema },
      { role: 'user', content: usuario }
    ],
    ...(schema ? {
      response_format: { type: 'json_schema', json_schema: { name: nombreSchema, strict: true, schema } }
    } : {})
  });
  const texto = r.choices?.[0]?.message?.content || '';
  if (r.choices?.[0]?.finish_reason === 'length') {
    return marcarCortado(texto, 'max_output_tokens', r.usage);
  }
  return texto;
}

function marcarCortado(texto, motivo, usage) {
  const razonamiento = usage?.output_tokens_details?.reasoning_tokens
    ?? usage?.completion_tokens_details?.reasoning_tokens;
  const detalle = razonamiento ? ` (${razonamiento} tokens se fueron en razonar)` : '';
  return `${texto || ''}\n\n⚠ RESPUESTA CORTADA — se agoto el presupuesto de tokens${detalle}. `
    + `Motivo: ${motivo || 'desconocido'}. Sube maxTokens en ia.mjs si esto se repite.`;
}

function extraerDeResponses(r) {
  const trozos = [];
  for (const item of r.output || []) {
    for (const c of item.content || []) {
      if (typeof c.text === 'string') trozos.push(c.text);
    }
  }
  return trozos.join('');
}

// --------------------------------------------------------------- el contexto

/**
 * El PDF, resumido a lo que el modelo necesita para opinar con criterio.
 * Va en el system y es IDENTICO en las tres llamadas, para que se cachee.
 */
const REGLAS = `Eres un diseñador de combate trabajando en Dark Angels, un action-RPG en Unreal
Engine 5.8 sobre el framework Dynamic Combat System. Hablas español, con frases
cortas y sin adornos.

El documento de referencia es "Divine Weapon Corruption + Encounter Combat Loop v2".
Sus reglas, que no se discuten:

- Malakh SIEMPRE conserva su espada principal. Es permanente y suficiente para
  terminar cualquier encuentro (§5.2 y §12). Ninguna arena puede exigir un arma
  temporal para ganarse.
- Las armas de los enemigos son oportunidades TEMPORALES. No hay inventario, no
  hay durabilidad y no hay desgaste: un arma temporal EQUIPADA solo termina por
  swap, por su ataque de descarte, por agotar un recurso natural (flechas) o por
  el seal break al completar el encuentro (§3).
- OJO, son dos cosas distintas y no las confundas: el arma EN LA MANO no caduca
  nunca (§3), pero el arma TIRADA EN EL SUELO si tiene una ventana limitada — el
  §4.1 pide literalmente que "permanezca fisicamente en el mundo durante una
  ventana breve y clara". Un TTL sobre el drop del suelo cumple el PDF; un
  temporizador sobre el arma equipada lo violaria. La herramienta hace lo
  primero. No lo señales como error.
- El swap es irreversible: al coger otra, la anterior se desmaterializa (§4.1).
- La corrupcion celestial→oscura es visual y narrativa. NO es un temporizador ni
  una barra de durabilidad (§3).
- El orden de bajas optimo debe DESCUBRIRSE, nunca dictarse por interfaz (§5).
  Se comunica con posicion, presion, silueta, geometria, timing y reaccion
  enemiga (§5.1).
- La ruta tactica buena reduce tiempo, riesgo o recursos, pero NUNCA es requisito
  (§5.2). Si el jugador la ignora, la pelea se vuelve mas dificil, no imposible.
- No es un juego de loot (§8): nada de rarezas, niveles ni comparar DPS. El valor
  del arma viene del contexto: "esta lanza sirve AHORA".
- Los drops se diseñan, no se sortean: Guaranteed Tactical Drop para las llaves
  del puzzle, Standard u No Drop para el resto (§8).

Los drops son DOS BOOLEANOS por enemigo, no una probabilidad: sueltaArmaPrincipal
y sueltaOffHand. El componente del juego solo sabe hacer eso. El ESCUDO va por la
ranura off-hand; todo lo demas por la principal.

Coordenadas: centimetros. X positivo se aleja de la entrada de Malakh, Y positivo
va a su derecha. La cota es altura; una plataforma alta necesita un acceso o el
enemigo es inalcanzable a pie, lo que es un soft-lock (§7.3).

Contexto que debes tener en cuenta y que sale de simular estas arenas 200 veces:
con los numeros actuales, la espada sola aguanta unos 2-3 enemigos a la vez. Una
composicion de cinco a la vez hoy no se gana solo con espada.`;

// ------------------------------------------------------------------ trabajos

export async function criticar(cuerpo) {
  const { datos } = cuerpo;
  return {
    texto: await pedir({
      sistema: REGLAS + fichasDeArquetipos(),
      usuario: `Este es un encuentro y los numeros que ha dado el simulador tras 200 partidas
por politica. Critícalo como diseñador.

${JSON.stringify(datos, null, 2)}

Responde en cuatro apartados cortos y concretos, citando la seccion del PDF cuando
proceda. No repitas los numeros: interpretalos.

1. QUE FUNCIONA — que hace bien esta composicion.
2. QUE NO — el problema mas grave, uno solo, el que arreglarias primero.
3. LA SEÑAL — si la ruta de ventaja se puede descubrir mirando la arena (§5.1) o
   solo tropezando con ella.
4. UN CAMBIO — una sola modificacion concreta (mover a quien, a donde, o cambiar
   que politica de drop) y que esperas que le pase al veredicto.

Si algo del veredicto te parece que mide mal, dilo.`,
      maxTokens: 16000
    })
  };
}

export async function variantes(cuerpo) {
  const { datos, esquema, cuantas = 3 } = cuerpo;
  const bruto = await pedir({
    sistema: REGLAS + fichasDeArquetipos(),
    usuario: `Aqui tienes un encuentro y como le ha ido en el simulador.

${JSON.stringify(datos, null, 2)}

Propon ${cuantas} variantes que enseñen lo mismo con OTRA geometria. Reglas:

- Reutiliza la misma arena: no toques limites, entrada ni trigger. Solo cambias
  la composicion, las posiciones, las coberturas y el orden previsto.
- Cada variante debe poder ganarse SOLO con la espada base (§12), y eso es lo
  primero que se comprueba: se simulan 100 partidas sin tocar un arma del suelo y
  hay que ganar el 90%. Esto NO es retorica. Los numeros medidos dicen que la
  espada aguanta 2-3 enemigos SIMULTANEOS, asi que lo que decide la variante no
  es cuantos enemigos pones sino cuantos llegan a la vez: separalos con
  distancia, cortales la vision con coberturas, y escalona su entrada. Dos
  enemigos bien colocados hacen mejor encuentro que cuatro amontonados.
- Que las variantes no sean tres veces la misma idea. Si las tres enseñan lo
  mismo, has propuesto una.
- Marca como "garantizado" solo el drop que es la llave del puzzle, y ponlo donde
  se vea desde la entrada (§5.1). Los demas, "estandar" o "ninguno".
- No pongas enemigos con cota alta salvo que la arena ya tenga una plataforma con
  acceso: sin acceso es un soft-lock (§7.3).

Devuelve solo el JSON del esquema.`,
    schema: esquema,
    nombreSchema: 'variantes_de_encuentro',
    maxTokens: 40000
  });

  let json;
  try {
    json = JSON.parse(bruto);
  } catch {
    const e = new Error('El modelo no devolvio JSON valido.');
    e.codigo = 'json-invalido';
    e.bruto = String(bruto).slice(0, 2000);
    throw e;
  }
  return json;
}

export async function narrar(cuerpo) {
  const { datos } = cuerpo;
  return {
    texto: await pedir({
      sistema: REGLAS + fichasDeArquetipos(),
      usuario: `Este es el registro de una sola partida del simulador, reducido a sus hitos.

${JSON.stringify(datos, null, 2)}

Cuentalo como la "historia de combate recordable" del §15: un parrafo, presente,
sin numeros, sin nombres de campo, como si lo contara alguien que acaba de verlo
jugar. Si la partida es plana y no da para una historia, dilo en una frase en vez
de inventar epica.`,
      maxTokens: 8000
    })
  };
}

export const TRABAJOS = { criticar, variantes, narrar };
