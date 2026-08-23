// El puente con el editor de Unreal.
//
// El MCP del proyecto escucha JSON-RPC 2.0 en http://127.0.0.1:8000/mcp, asi que
// el servidor de la Forja le puede hablar directo con fetch. El navegador NO
// habla con el editor: habla con este proceso, y este con el editor.
//
// El handshake tiene tres pasos y el tercero se olvida siempre:
//   1. initialize                  -> devuelve la cabecera Mcp-Session-Id
//   2. notifications/initialized   -> sin esto, todo lo demas falla
//   3. tools/call                  -> ya con la sesion en la cabecera
//
// Aviso que vale mas que el codigo: EL EDITOR MIENTE EN LAS DOS DIRECCIONES.
// `save` devuelve true sin guardar y hay llamadas que devuelven exito sin haber
// hecho nada. Por eso aqui nada se da por bueno: todo lo que se escribe se
// vuelve a leer y se compara.

const URL_MCP = process.env.UNREAL_MCP_URL || 'http://127.0.0.1:8000/mcp';
const CABECERAS = {
  'content-type': 'application/json',
  'accept': 'application/json, text/event-stream'
};

let sesion = null;

/** El cuerpo puede venir como JSON pelado o como SSE (`data: {...}`). */
function parsear(texto) {
  const limpio = texto.trim();
  if (limpio.startsWith('{')) return JSON.parse(limpio);
  for (const linea of limpio.split('\n')) {
    if (linea.startsWith('data:')) return JSON.parse(linea.slice(5).trim());
  }
  throw new Error('Respuesta del MCP ilegible: ' + limpio.slice(0, 200));
}

async function rpc(metodo, params, { notificacion = false } = {}) {
  const cuerpo = { jsonrpc: '2.0', method: metodo, params };
  if (!notificacion) cuerpo.id = Math.floor(Math.random() * 1e9);

  const r = await fetch(URL_MCP, {
    method: 'POST',
    headers: sesion ? { ...CABECERAS, 'mcp-session-id': sesion } : CABECERAS,
    body: JSON.stringify(cuerpo)
  });

  const nuevaSesion = r.headers.get('mcp-session-id');
  if (nuevaSesion) sesion = nuevaSesion;
  if (notificacion) return null;

  const texto = await r.text();
  if (!r.ok) throw new Error(`MCP HTTP ${r.status}: ${texto.slice(0, 300)}`);
  const j = parsear(texto);
  if (j.error) throw new Error(`MCP: ${j.error.message || JSON.stringify(j.error)}`);
  return j.result;
}

async function conectar() {
  if (sesion) return;
  await rpc('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'forja-de-encuentros', version: '0.5.0' }
  });
  // Sin este aviso el servidor se queda a medio abrir y las llamadas fallan.
  await rpc('notifications/initialized', {}, { notificacion: true });
}

/** Ejecuta Python dentro del editor y devuelve su stdout. */
export async function python(codigo) {
  await conectar();
  const res = await rpc('tools/call', {
    name: 'execute_python_code',
    arguments: { code: codigo }
  });
  const texto = (res?.content || []).map(c => c.text || '').join('');
  let j;
  try { j = JSON.parse(texto); } catch { return { salida: texto, exito: true }; }
  if (j.success === false) {
    const e = new Error(j.error_message || 'Python fallo en el editor');
    e.codigo = 'python-editor';
    throw e;
  }
  return { salida: j.output ?? '', exito: true };
}

export async function estado() {
  try {
    const { salida } = await python(
      'import unreal\n' +
      'lvl = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)\n' +
      'w = lvl.get_current_level().get_outer()\n' +
      'print(w.get_name())\n' +
      'print(w.get_path_name())'
    );
    const [nombre, ruta] = salida.trim().split('\n');
    return { conectado: true, nivel: nombre, ruta, url: URL_MCP };
  } catch (err) {
    sesion = null;   // que el siguiente intento rehaga el handshake
    return {
      conectado: false,
      url: URL_MCP,
      motivo: err.message.includes('fetch failed')
        ? 'El editor no responde. ¿Esta Unreal abierto con el servidor MCP arrancado?'
        : err.message
    };
  }
}

export function reiniciarSesion() { sesion = null; }
