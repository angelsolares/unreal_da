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

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
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
});
