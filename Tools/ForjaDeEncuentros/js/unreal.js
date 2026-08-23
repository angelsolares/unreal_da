// Cliente del puente con Unreal.
//
// El navegador no habla con el editor: habla con el servidor de la Forja, y ese
// con el MCP del editor. Igual que con la clave de OpenAI, lo que no tiene que
// estar en el navegador no esta en el navegador.

async function llamar(ruta, cuerpo) {
  const r = await fetch(`/unreal/${ruta}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(cuerpo)
  });
  const datos = await r.json().catch(() => ({ error: `Respuesta ilegible (HTTP ${r.status})` }));
  if (!r.ok) {
    const e = new Error(datos.error || `HTTP ${r.status}`);
    e.codigo = datos.codigo;
    throw e;
  }
  return datos;
}

export async function estadoUnreal() {
  try {
    return await (await fetch('/unreal/estado')).json();
  } catch (err) {
    return { conectado: false, motivo: 'El servidor no responde: ' + err.message };
  }
}

export function exportar(encuentro, offset, confirmarNivel) {
  return llamar('exportar', { encuentro, offset, confirmarNivel });
}

export function importar(offset) {
  return llamar('importar', { offset });
}

/**
 * Compara lo que hay en el editor con lo que dice el JSON.
 * Es la pregunta util despues de mover cosas a mano en Unreal: ¿que ha cambiado?
 */
export function comparar(encuentro, leido) {
  const filas = [];
  const usados = new Set();

  for (const e of encuentro.enemigos) {
    const et = (e.etiqueta || '').replace(/\s+/g, '_');
    const enEditor = leido.enemigos.find(x => !usados.has(x.etiqueta) && et && x.etiqueta.endsWith(et));
    if (enEditor) usados.add(enEditor.etiqueta);
    if (!enEditor) {
      filas.push({ etiqueta: e.etiqueta || e.id, estado: 'falta', texto: 'No esta en el editor' });
      continue;
    }
    const dx = enEditor.pos.x - e.pos.x;
    const dy = enEditor.pos.y - e.pos.y;
    const dz = enEditor.cota - (e.cota || 0);
    const movido = Math.abs(dx) > 2 || Math.abs(dy) > 2 || Math.abs(dz) > 2;
    filas.push({
      etiqueta: e.etiqueta || e.id,
      estado: movido ? 'movido' : 'igual',
      texto: movido
        ? `movido (${dx >= 0 ? '+' : ''}${dx}, ${dy >= 0 ? '+' : ''}${dy}, ${dz >= 0 ? '+' : ''}${dz}) cm`
        : 'en su sitio',
      delta: { dx, dy, dz },
      nuevo: { pos: enEditor.pos, cota: enEditor.cota }
    });
  }

  for (const x of leido.enemigos) {
    if (!usados.has(x.etiqueta)) {
      filas.push({ etiqueta: x.etiqueta, estado: 'sobra', texto: 'Esta en el editor pero no en el JSON' });
    }
  }
  return filas;
}

/** Aplica al encuentro lo que se ha movido en el editor. */
export function aplicarCambios(encuentro, filas) {
  let n = 0;
  for (const f of filas) {
    if (f.estado !== 'movido' || !f.nuevo) continue;
    const e = encuentro.enemigos.find(x => (x.etiqueta || x.id) === f.etiqueta);
    if (!e) continue;
    e.pos = { x: f.nuevo.pos.x, y: f.nuevo.pos.y };
    e.cota = f.nuevo.cota;
    n++;
  }
  return n;
}
