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

const MODELO = process.env.OPENAI_MODEL || 'gpt-5.6-sol';

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
async function pedir({ sistema, usuario, schema, nombreSchema, maxTokens = 4000 }) {
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
  return r.choices?.[0]?.message?.content || '';
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
  hay durabilidad y no hay desgaste: un arma temporal solo termina por swap,
  por su ataque de descarte, por agotar un recurso natural (flechas) o por el
  seal break al completar el encuentro (§3).
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

Arquetipos disponibles y el arma que suelta cada uno:
  lancero_del_alba        -> Lanza del Alba (alcance/control; su descarte es arrojarla)
  arquero_del_firmamento  -> Arco del Firmamento (rango; flechas como recurso)
  escudero_celestial      -> Escudo Celestial (off-hand; defensa/parry)
  elite_pesado            -> Espadon/Alabarda (guard break/AoE)
  portador_del_estandarte -> Estandarte ritual (control de zona)

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
      sistema: REGLAS,
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
      maxTokens: 3000
    })
  };
}

export async function variantes(cuerpo) {
  const { datos, esquema, cuantas = 3 } = cuerpo;
  const bruto = await pedir({
    sistema: REGLAS,
    usuario: `Aqui tienes un encuentro y como le ha ido en el simulador.

${JSON.stringify(datos, null, 2)}

Propon ${cuantas} variantes que enseñen lo mismo con OTRA geometria. Reglas:

- Reutiliza la misma arena: no toques limites, entrada ni trigger. Solo cambias
  la composicion, las posiciones, las coberturas y el orden previsto.
- Cada variante debe poder ganarse SOLO con la espada base (§12). Con los numeros
  actuales eso significa no amontonar mas de tres enemigos a la vez sobre Malakh:
  usa la distancia, las coberturas y la cota para escalonar el combate.
- Marca como "garantizado" solo el drop que es la llave del puzzle, y ponlo donde
  se vea desde la entrada (§5.1). Los demas, "estandar" o "ninguno".
- No pongas enemigos con cota alta salvo que la arena ya tenga una plataforma con
  acceso: sin acceso es un soft-lock (§7.3).

Devuelve solo el JSON del esquema.`,
    schema: esquema,
    nombreSchema: 'variantes_de_encuentro',
    maxTokens: 8000
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
      sistema: REGLAS,
      usuario: `Este es el registro de una sola partida del simulador, reducido a sus hitos.

${JSON.stringify(datos, null, 2)}

Cuentalo como la "historia de combate recordable" del §15: un parrafo, presente,
sin numeros, sin nombres de campo, como si lo contara alguien que acaba de verlo
jugar. Si la partida es plana y no da para una historia, dilo en una frase en vez
de inventar epica.`,
      maxTokens: 1200
    })
  };
}

export const TRABAJOS = { criticar, variantes, narrar };
