// Leer y guardar datos/arquetipos.json desde la interfaz.
//
// Ese fichero es lo que la IA usa para razonar sobre cada enemigo: papel, como
// pelea, como se le contesta. Tenerlo editable solo abriendo el JSON a mano era
// una friccion tonta —justo el sitio donde mas ganas dan de escribir una frase
// mientras miras la arena—, asi que se edita desde el panel.
//
// Se escribe con lista blanca de claves: solo arquetipos que existen y solo los
// campos previstos. Un POST torcido no puede meter estructura rara en el fichero
// que alimenta al modelo.

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RUTA = path.join(AQUI, 'datos/arquetipos.json');

/** Los unicos campos que se pueden escribir, y en este orden. */
export const CAMPOS = [
  { id: 'papel', etiqueta: 'Papel', ayuda: 'Para que esta en la arena, en media linea.' },
  { id: 'comoPelea', etiqueta: 'Como pelea', ayuda: 'Su comportamiento: alcances, ritmo, que castiga.' },
  { id: 'comoSeContesta', etiqueta: 'Como se le contesta', ayuda: 'La respuesta que quieres que el jugador descubra.' },
  { id: 'queAporta', etiqueta: 'Que aporta su arma', ayuda: 'Que cambia para Malakh cuando la coge.' },
  { id: 'dondeColocarlo', etiqueta: 'Donde colocarlo', ayuda: 'Que posiciones le sacan partido.' },
  { id: 'cuidadoCon', etiqueta: 'Cuidado con', ayuda: 'El error que se comete al componerlo.' }
];

export async function leer() {
  const j = JSON.parse(await fs.readFile(RUTA, 'utf8'));
  return { arquetipos: j.arquetipos || {}, reglas: j.reglasDeComposicion || {}, campos: CAMPOS };
}

/**
 * Guarda la descripcion de UN arquetipo. Devuelve lo que quedo escrito, releido
 * del disco: si el fichero no se pudo escribir, se nota aqui y no en la proxima
 * peticion a la IA.
 */
export async function guardar(cuerpo) {
  const { arquetipo, campos } = cuerpo;
  const j = JSON.parse(await fs.readFile(RUTA, 'utf8'));

  if (!j.arquetipos?.[arquetipo]) {
    const e = new Error(`Arquetipo desconocido: ${arquetipo}`);
    e.codigo = 'arquetipo-desconocido';
    throw e;
  }

  const permitidos = new Set(CAMPOS.map(c => c.id));
  let tocados = 0;
  for (const [k, v] of Object.entries(campos || {})) {
    if (!permitidos.has(k)) continue;
    j.arquetipos[arquetipo][k] = String(v ?? '').trim();
    tocados++;
  }
  if (!tocados) {
    const e = new Error('No habia ningun campo valido que guardar.');
    e.codigo = 'sin-campos';
    throw e;
  }

  await fs.writeFile(RUTA, JSON.stringify(j, null, 2) + '\n', 'utf8');

  // Releer: el disco es la verdad, no lo que creemos haber escrito.
  const comprobado = JSON.parse(await fs.readFile(RUTA, 'utf8'));
  return {
    guardado: true,
    arquetipo,
    campos: tocados,
    enDisco: comprobado.arquetipos[arquetipo],
    nota: 'La proxima peticion a la IA ya usa esto. No hace falta reiniciar.'
  };
}

export const TRABAJOS = { leer, guardar };
