// Servidor estatico sin dependencias. Hace falta porque los modulos ES no
// cargan desde file:// (el navegador los bloquea por CORS).
//   node serve.mjs        -> http://localhost:5175

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const raiz = path.dirname(fileURLToPath(import.meta.url));
const puerto = Number(process.argv[2] || 5175);

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png'
};

/**
 * Rutas de la capa de IA (fase D). El modulo se importa solo cuando se pide:
 * asi la herramienta entera —editor, simulador, 3D— sigue funcionando sin
 * instalar nada, y quien no use la IA no paga su dependencia.
 */
async function rutaIA(req, res, accion) {
  const enviar = (codigo, cuerpo) => {
    res.writeHead(codigo, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(cuerpo));
  };

  let ia;
  try {
    ia = await import('./ia.mjs');
  } catch (err) {
    return enviar(500, { error: 'No se pudo cargar ia.mjs: ' + err.message });
  }

  if (accion === 'estado') return enviar(200, await ia.estado());
  if (!ia.TRABAJOS[accion]) return enviar(404, { error: `Trabajo desconocido: ${accion}` });
  if (req.method !== 'POST') return enviar(405, { error: 'Usa POST' });

  const trozos = [];
  for await (const t of req) trozos.push(t);
  let cuerpo;
  try {
    cuerpo = JSON.parse(Buffer.concat(trozos).toString('utf8') || '{}');
  } catch (err) {
    return enviar(400, { error: 'Cuerpo JSON invalido: ' + err.message });
  }

  try {
    enviar(200, await ia.TRABAJOS[accion](cuerpo));
  } catch (err) {
    // El motivo importa mas que el codigo: la interfaz lo enseña tal cual.
    enviar(err.codigo === 'sin-ia' ? 503 : 502, {
      error: err.message,
      codigo: err.codigo || 'error-openai',
      bruto: err.bruto
    });
  }
}

/** Rutas del puente con Unreal (fase E). Mismo patron perezoso que la IA. */
async function rutaUnreal(req, res, accion) {
  const enviar = (codigo, cuerpo) => {
    res.writeHead(codigo, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(cuerpo));
  };

  let puente, exportador;
  try {
    puente = await import('./puente.mjs');
    exportador = await import('./exportador.mjs');
  } catch (err) {
    return enviar(500, { error: 'No se pudo cargar el puente: ' + err.message });
  }

  if (accion === 'estado') return enviar(200, await puente.estado());
  if (!exportador.TRABAJOS[accion]) return enviar(404, { error: `Trabajo desconocido: ${accion}` });
  if (req.method !== 'POST') return enviar(405, { error: 'Usa POST' });

  const trozos = [];
  for await (const t of req) trozos.push(t);
  let cuerpo;
  try {
    cuerpo = JSON.parse(Buffer.concat(trozos).toString('utf8') || '{}');
  } catch (err) {
    return enviar(400, { error: 'Cuerpo JSON invalido: ' + err.message });
  }

  try {
    enviar(200, await exportador.TRABAJOS[accion](cuerpo));
  } catch (err) {
    puente.reiniciarSesion();
    enviar(502, { error: err.message, codigo: err.codigo || 'error-unreal' });
  }
}

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);

  if (url.startsWith('/unreal/')) {
    rutaUnreal(req, res, url.slice(8)).catch(err => {
      res.writeHead(500, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message || err) }));
    });
    return;
  }

  if (url.startsWith('/ia/')) {
    rutaIA(req, res, url.slice(4)).catch(err => {
      res.writeHead(500, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message || err) }));
    });
    return;
  }

  const rel = url === '/' ? 'index.html' : url.slice(1);
  const destino = path.join(raiz, rel);

  // No servir nada de fuera de la carpeta.
  if (!destino.startsWith(raiz)) { res.writeHead(403).end('403'); return; }

  fs.readFile(destino, (err, datos) => {
    if (err) { res.writeHead(404, { 'content-type': 'text/plain' }).end('404 ' + rel); return; }
    res.writeHead(200, {
      'content-type': TIPOS[path.extname(destino)] || 'application/octet-stream',
      'cache-control': 'no-store'
    });
    res.end(datos);
  });
}).listen(puerto, () => {
  console.log(`Forja de Encuentros -> http://localhost:${puerto}`);
  console.log(process.env.OPENAI_API_KEY
    ? `IA: activa, modelo ${process.env.OPENAI_MODEL || 'gpt-5.6-sol'} (cambialo con OPENAI_MODEL)`
    : 'IA: apagada. Exporta OPENAI_API_KEY y ejecuta: npm install openai');
});
