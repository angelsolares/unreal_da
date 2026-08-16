// Helper: habla con el MCP del editor de Unreal por HTTP (JSON-RPC 2.0) y
// guarda las capturas como PNG en disco, para no meter base64 en el contexto.
//
// Uso:
//   node ue.mjs shot <out.png> <x> <y> <z> <pitch> <yaw>
//   node ue.mjs call <toolset|-> <tool> <argsJson>
//   node ue.mjs script <fichero.py>

import { writeFileSync, readFileSync } from 'node:fs';
import http from 'node:http';

const HOST = '127.0.0.1';
const PORT = 8000;
const PATH = '/mcp';
let sessionId = null;
let nextId = 1;

// Se usa node:http en vez de fetch a proposito: undici corta a los 5 min
// (UND_ERR_HEADERS_TIMEOUT) y hay consultas al editor que tardan mas.
function post(bodyStr, headers) {
  return new Promise((resolve, reject) => {
    const req = http.request(
      { host: HOST, port: PORT, path: PATH, method: 'POST', headers },
      (res) => {
        let data = '';
        res.setEncoding('utf8');
        res.on('data', (c) => (data += c));
        res.on('end', () => resolve({ headers: res.headers, text: data }));
      },
    );
    req.on('error', reject);
    req.setTimeout(0);
    req.end(bodyStr);
  });
}

async function rpc(method, params, isNotification = false) {
  const body = { jsonrpc: '2.0', method };
  if (params !== undefined) body.params = params;
  if (!isNotification) body.id = nextId++;
  const bodyStr = JSON.stringify(body);

  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
    'Content-Length': Buffer.byteLength(bodyStr),
  };
  if (sessionId) headers['Mcp-Session-Id'] = sessionId;

  const res = await post(bodyStr, headers);
  const sid = res.headers['mcp-session-id'];
  if (sid) sessionId = sid;
  if (isNotification) return null;

  // La respuesta puede venir como SSE ("data: {...}") o como JSON pelado.
  const line = res.text.split('\n').find((l) => l.startsWith('data:'));
  const json = JSON.parse(line ? line.slice(5).trim() : res.text);
  if (json.error) throw new Error(JSON.stringify(json.error));
  return json.result;
}

async function connect() {
  await rpc('initialize', {
    protocolVersion: '2025-06-18',
    capabilities: {},
    clientInfo: { name: 'da-helper', version: '1.0' },
  });
  await rpc('notifications/initialized', {}, true);
}

// Devuelve el texto del primer content de la respuesta de tools/call.
function payload(result) {
  const c = (result.content || []).find((x) => x.type === 'text');
  return c ? c.text : JSON.stringify(result);
}

async function callTool(toolset, tool, args) {
  const a = { tool_name: tool, arguments: args };
  if (toolset && toolset !== '-') a.toolset_name = toolset;
  const r = await rpc('tools/call', { name: 'call_tool', arguments: a });
  return payload(r);
}

const [, , cmd, ...rest] = process.argv;
await connect();

if (cmd === 'shot') {
  const [out, x, y, z, pitch, yaw] = rest;
  const txt = await callTool('EditorToolset.EditorAppToolset', 'CaptureViewport', {
    captureTransform: {
      location: { x: +x, y: +y, z: +z },
      rotation: { pitch: +pitch, yaw: +yaw, roll: 0 },
    },
    annotations: {
      gridSpacing: 0, gridExtent: 0, gridHeight: 0,
      maxLabelDistance: 0, classFilter: null, maxLabels: 0,
    },
  });
  const data = JSON.parse(txt).returnValue.image.data;
  writeFileSync(out, Buffer.from(data, 'base64'));
  console.log(`OK ${out} (${Math.round(data.length * 0.75 / 1024)} KB)`);
} else if (cmd === 'thumb') {
  // Miniatura de un asset: se renderiza en su propia escena de previsualizacion,
  // asi que sirve para distinguir un ajuste del viewport del nivel de algo global.
  const [out, asset] = rest;
  const txt = await callTool('EditorToolset.EditorAppToolset', 'CaptureAssetImage', {
    assetPath: asset,
  });
  const data = JSON.parse(txt).returnValue.data;
  writeFileSync(out, Buffer.from(data, 'base64'));
  console.log(`OK ${out}`);
} else if (cmd === 'call') {
  const [toolset, tool, argsJson] = rest;
  console.log(await callTool(toolset, tool, JSON.parse(argsJson || '{}')));
} else if (cmd === 'script') {
  const src = readFileSync(rest[0], 'utf8');
  console.log(
    await callTool(
      'editor_toolset.toolsets.programmatic.ProgrammaticToolset',
      'execute_tool_script',
      { script: src },
    ),
  );
} else {
  console.error('comando desconocido');
  process.exit(1);
}
