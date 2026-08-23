// Los tres paneles de la derecha: veredicto, propiedades y calibracion.

import { ARQUETIPOS, POLITICAS_DROP, FAMILIAS } from './catalogo.js';
import { validar, etiquetaDe } from './esquema.js';

const MARCAS = { ok: '✓', aviso: '!', fallo: '×', na: '–' };

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ------------------------------------------------------------------ veredicto

export function pintarVeredicto(nodo, lote, extra = {}) {
  if (!lote) {
    nodo.innerHTML = `<p class="nota">Aun no has simulado.</p>`;
    return;
  }
  const v = lote.veredicto;
  const partes = [];

  partes.push(`<div class="titular ${v.resumen}">${esc(v.titular)}</div>`);

  for (const p of v.puertas) {
    partes.push(`
      <div class="puerta ${p.estado}">
        <div class="cabeza">
          <span class="marca">${MARCAS[p.estado]}</span>
          <span class="titulo">${esc(p.titulo)}</span>
          <span class="ref">${esc(p.referencia)}</span>
        </div>
        <div class="texto">${esc(p.texto)}</div>
      </div>`);
  }

  // --- comparativa de politicas ---
  partes.push('<h2>Politicas</h2><table class="datos"><tr><th>politica</th><th>gana</th><th>tiempo</th><th>daño</th><th>armas</th></tr>');
  for (const p of Object.values(lote.porPolitica)) {
    const r = p.resumen;
    const destacada = (p.id === 'ventaja' || p.id === 'cercano') ? ' class="destacada"' : '';
    partes.push(`<tr${destacada}>
      <td title="${esc(p.descripcion)}">${esc(p.nombre)}</td>
      <td>${(r.tasaVictoria * 100).toFixed(0)}%</td>
      <td>${r.tiempoMediana ?? '—'}${r.tiempoMediana != null ? 's' : ''}</td>
      <td>${r.danoMediana ?? '—'}</td>
      <td>${r.armasPorPartida}</td>
    </tr>`);
  }
  partes.push('</table>');
  partes.push('<p class="nota">Las dos resaltadas son la comparacion del §5.2: <strong>el mas cercano</strong> es la espada sola, <strong>ruta de ventaja</strong> es con armas.</p>');

  // --- el arsenal: que se recoge y cuanto aporta ---
  const vent = lote.porPolitica['ventaja'];
  if (vent) {
    const rec = Object.entries(vent.resumen.recogidas || {}).sort((a, b) => b[1] - a[1]);
    partes.push('<h2>El arsenal en juego</h2>');
    if (!rec.length) {
      partes.push('<p class="nota">No se recoge ni un arma. O nadie las suelta, o expiran antes de que se pueda llegar.</p>');
    } else {
      partes.push('<table class="datos"><tr><th>arma</th><th>por partida</th><th>del daño</th></tr>');
      for (const [fam, veces] of rec) {
        const meta = FAMILIAS[fam] || {};
        const dano = vent.resumen.danoPorArma.find(d => d.clave === fam);
        partes.push(`<tr>
          <td><span style="color:${meta.color || '#888'}">■</span> ${esc(meta.nombre || fam)}</td>
          <td>${(veces / lote.partidas).toFixed(2)}</td>
          <td>${dano ? (dano.fraccion * 100).toFixed(0) + '%' : '0%'}</td>
        </tr>`);
      }
      const base = vent.resumen.danoPorArma.find(d => d.clave === 'espada_base');
      partes.push(`<tr><td>Espada de Malakh</td><td>—</td><td>${base ? (base.fraccion * 100).toFixed(0) + '%' : '0%'}</td></tr>`);
      partes.push('</table>');
      partes.push(`<p class="nota">Descartes por partida: <strong>${vent.resumen.descartesPorPartida}</strong>.
        Si un arma se recoge mucho pero apenas hace daño, es que se sacrifica nada mas cogerla:
        mira si eso es la cadena que querias o un desperdicio.</p>`);
    }
  }

  // --- de que muere Malakh ---
  const base = lote.porPolitica['cercano'];
  if (base?.resumen.danoPorFuente.length) {
    partes.push('<h2>De que le hacen daño</h2>');
    for (const f of base.resumen.danoPorFuente) {
      const meta = ARQUETIPOS[f.arquetipo] || {};
      partes.push(`
        <div style="margin-bottom:6px">
          <div style="display:flex;justify-content:space-between;font-size:11.5px">
            <span>${esc((meta.glifo ? meta.glifo + ' · ' : '') + f.arquetipo.replace(/_/g, ' '))}</span>
            <span style="color:var(--texto-tenue)">${(f.fraccion * 100).toFixed(0)}%</span>
          </div>
          <div class="barra"><span style="width:${(f.fraccion * 100).toFixed(0)}%;background:${meta.color || '#888'}"></span></div>
        </div>`);
    }
  }

  // --- diagnostico: el techo de la espada ---
  if (extra.techo) {
    const t = extra.techo;
    partes.push('<h2>Techo de la espada</h2>');
    partes.push(`<p class="nota">Con la calibracion actual, la espada sola aguanta
      <strong>${t.techo} de los ${t.pedidos}</strong> enemigos que pide este encuentro.</p>`);
    partes.push('<table class="datos"><tr><th>enemigos</th><th>victorias</th></tr>');
    for (const e of t.escalones) {
      partes.push(`<tr${e.n === t.techo ? ' class="destacada"' : ''}><td>${e.n}</td><td>${(e.tasa * 100).toFixed(0)}%</td></tr>`);
    }
    partes.push('</table>');
  }
  if (extra.dano) {
    const d = extra.dano;
    partes.push(d.yaPasa
      ? `<p class="nota">El daño actual (<strong>${d.actual}</strong> por golpe) ya basta.</p>`
      : d.necesario
        ? `<p class="nota">Para pasar la puerta harian falta <strong>${d.necesario}</strong> de daño por golpe
           en vez de ${d.actual} — un factor de <strong>×${d.factor}</strong>.</p>`
        : `<p class="nota">Ni con <strong>${d.techoBusqueda}</strong> de daño por golpe pasa la puerta.
           El problema no es el daño: es la composicion o la geometria.</p>`);
  }

  // --- problemas estaticos ---
  if (v.problemasEstaticos.length) {
    partes.push('<h2>Avisos del planteamiento</h2>');
    for (const p of v.problemasEstaticos) {
      partes.push(`<div class="problema ${p.nivel === 'error' ? 'error' : ''}">${esc(p.texto)}</div>`);
    }
  }

  partes.push(`
    <h2>Lo que este modelo NO sabe</h2>
    <p class="nota">
      Malakh no usa la cobertura contra los arqueros: cruza a pecho descubierto.<br>
      No hay parry, que es la opcion de mas habilidad de DCS.<br>
      No arrastra enemigos a un cuello de botella para pelearlos de uno en uno.<br>
      La IA enemiga no flanquea ni se coordina.<br>
      <strong>Todo esto tira del veredicto hacia abajo</strong>: la puerta de "ganable" es un
      suelo, no un techo. Si aqui sale verde, en manos de un jugador decente sale mas verde.
    </p>`);

  nodo.innerHTML = partes.join('');
}

// --------------------------------------------------------------- propiedades

export function pintarPropiedades(nodo, enc, seleccion, cal, acciones) {
  const partes = [];

  partes.push('<h2>Encuentro</h2>');
  partes.push(campoTexto('nombre', 'Nombre', enc.nombre));
  partes.push(campoTexto('id', 'Id (el del Data Asset)', enc.id));

  partes.push('<h2>Orden de bajas previsto</h2>');
  partes.push(`<p class="nota">Arrastra con los botones para fijar la ruta que crees haber diseñado.
    La politica "Ruta guionizada" seguira exactamente este orden.</p>`);
  partes.push('<div id="lista-enemigos">');
  const orden = enc.ordenPrevisto || [];
  const ordenados = [...enc.enemigos].sort((a, b) => {
    const ia = orden.indexOf(a.id), ib = orden.indexOf(b.id);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  for (const e of ordenados) {
    const meta = ARQUETIPOS[e.arquetipo] || {};
    const i = orden.indexOf(e.id);
    partes.push(`
      <div class="chip-enemigo ${seleccion?.id === e.id ? 'sel' : ''}" data-enemigo="${esc(e.id)}">
        <span class="orden">${i >= 0 ? i + 1 : '·'}</span>
        <span class="punto" style="background:${meta.color || '#888'}"></span>
        <span style="flex:1">${esc(etiquetaDe(e))}</span>
        <button data-subir="${esc(e.id)}" style="padding:1px 5px">↑</button>
        <button data-bajar="${esc(e.id)}" style="padding:1px 5px">↓</button>
      </div>`);
  }
  partes.push('</div>');

  if (seleccion?.tipo === 'enemigo') {
    const e = seleccion.ref;
    const meta = ARQUETIPOS[e.arquetipo] || {};
    const perfil = cal.arquetipos[e.arquetipo] || {};
    const fam = FAMILIAS[perfil.arma];
    partes.push(`<h2>${esc(perfil.nombre || e.arquetipo)}</h2>`);
    partes.push(campoTexto('etiqueta', 'Etiqueta', e.etiqueta || ''));
    partes.push(`<div class="campo-fila"><div style="flex:1">
      <label>X (cm)</label><input type="number" data-campo="pos.x" value="${Math.round(e.pos.x)}" /></div>
      <div style="flex:1"><label>Y (cm)</label><input type="number" data-campo="pos.y" value="${Math.round(e.pos.y)}" /></div>
      <div style="flex:1"><label>Cota</label><input type="number" data-campo="cota" value="${e.cota || 0}" /></div></div>`);
    partes.push(`<label>Yaw</label><input type="number" data-campo="yaw" value="${Math.round(e.yaw ?? 180)}" />`);
    partes.push('<label>Politica de drop (§8)</label><select data-campo="drop">');
    for (const [k, d] of Object.entries(POLITICAS_DROP)) {
      partes.push(`<option value="${k}" ${e.drop === k ? 'selected' : ''}>${esc(d.etiqueta)}</option>`);
    }
    partes.push('</select>');
    if (fam) {
      partes.push(`<p class="nota">Suelta <strong>${esc(fam.nombre)}</strong> — ${esc(fam.rol)}.<br>
        Descarte: ${esc(fam.ataqueDescarte.nombre)}${fam.ataqueDescarte.implementado ? ' <span class="marca-fuente medido">ya existe</span>' : ' <span class="marca-fuente estimado">por hacer</span>'}</p>`);
    }
    partes.push(`<p class="nota">HP ${perfil.hp} · daño ${perfil.dano} · alcance ${perfil.alcanceAtaque} cm · aggro ${perfil.rangoAggro} cm</p>`);
    partes.push(`<button data-borrar="${esc(e.id)}" style="margin-top:8px">Borrar enemigo</button>`);
  } else if (seleccion?.tipo === 'cobertura' || seleccion?.tipo === 'plataforma') {
    const o = seleccion.ref;
    partes.push(`<h2>${seleccion.tipo}</h2>`);
    partes.push(campoTexto('etiqueta', 'Etiqueta', o.etiqueta || ''));
    if (seleccion.tipo === 'cobertura') {
      partes.push(`<label>Altura (cm)</label><input type="number" data-campo="altura" value="${o.altura}" />`);
      partes.push(`<p class="nota">Por encima de ${cal.malakh.alturaOjos} cm corta la linea de vision.
        Un arquero en cota alta ve por encima igualmente.</p>`);
    } else {
      partes.push(`<label>Cota (cm)</label><input type="number" data-campo="cota" value="${o.cota}" />`);
      partes.push(`<p class="nota">Accesos: ${(o.accesos || []).length}.
        ${(o.accesos || []).length ? '' : '<strong>Sin acceso es un soft-lock.</strong> Usa el modo "Poner acceso".'}</p>`);
    }
    partes.push(`<button data-borrar-forma="${esc(o.id)}" style="margin-top:8px">Borrar</button>`);
  } else {
    partes.push('<p class="nota">Pincha un enemigo, una cobertura o una plataforma para editarla.</p>');
  }

  nodo.innerHTML = partes.join('');
}

function campoTexto(campo, etiqueta, valor) {
  return `<label>${esc(etiqueta)}</label><input type="text" data-campo="${esc(campo)}" value="${esc(valor)}" />`;
}

// --------------------------------------------------------------- calibracion

export function pintarCalibracion(nodo, cal) {
  const p = cal.procedencia || {};
  const marca = (clave) => {
    const t = p[clave] || '';
    if (/^medido/i.test(t)) return '<span class="marca-fuente medido">medido</span>';
    if (/^PARCIAL/i.test(t)) return '<span class="marca-fuente estimado">parcial</span>';
    if (t) return '<span class="marca-fuente estimado">estimado</span>';
    return '';
  };

  const filas = [
    ['malakh.hp', 'Vida', cal.malakh.hp],
    ['malakh.velocidad', 'Velocidad', cal.malakh.velocidad + ' cm/s'],
    ['malakh.danoBase', 'Daño (base + espada)', cal.malakh.danoBase + cal.malakh.armaBase.dano],
    ['malakh.ataqueLigero.duracion', 'Ataque ligero', cal.malakh.ataqueLigero.duracion + ' s'],
    ['malakh.ataquePesado.duracion', 'Ataque pesado', cal.malakh.ataquePesado.duracion + ' s'],
    ['malakh.ataqueLigero.alcance', 'Alcance espada', cal.malakh.ataqueLigero.alcance + ' cm'],
    ['malakh.esquiva', 'Esquiva (i-frames)', `${cal.malakh.esquiva.iframeInicio}–${cal.malakh.esquiva.iframeFin} s`],
    ['malakh.bloqueo', 'Bloqueo', `−${(cal.malakh.bloqueo.reduccion * 100).toFixed(0)}%`],
    ['malakh.pocion.curacion', 'Pocion', `${cal.malakh.pocion.curacion} HP ×${cal.malakh.pocion.cantidad}`],
    ['malakh.reaccionGolpe', 'Reaccion a golpe', cal.malakh.reaccionGolpe + ' s']
  ];

  const partes = ['<h2>Malakh</h2><table class="datos">'];
  for (const [clave, nombre, valor] of filas) {
    partes.push(`<tr><td title="${esc(p[clave] || '')}">${esc(nombre)} ${marca(clave)}</td><td>${esc(valor)}</td></tr>`);
  }
  partes.push('</table>');

  partes.push('<h2>Enemigos</h2><table class="datos"><tr><th></th><th>HP</th><th>daño</th><th>vel</th><th>alcance</th></tr>');
  for (const [id, a] of Object.entries(cal.arquetipos)) {
    const meta = ARQUETIPOS[id] || {};
    partes.push(`<tr><td><span style="color:${meta.color}">${meta.glifo || '?'}</span> ${esc(a.nombre)}</td>
      <td>${a.hp}</td><td>${a.dano}</td><td>${a.velocidad}</td><td>${a.alcanceAtaque}</td></tr>`);
  }
  partes.push('</table>');

  const avisos = Object.entries(p).filter(([k]) => k.startsWith('aviso.'));
  if (avisos.length) {
    partes.push('<h2>Ojo con esto</h2>');
    for (const [, texto] of avisos) partes.push(`<div class="problema">${esc(texto)}</div>`);
  }

  partes.push(`<h2>Que falta medir</h2><p class="nota">`);
  const pendientes = Object.entries(p)
    .filter(([, t]) => /^ESTIMADO/i.test(t) && !/en bloque/i.test(t))
    .map(([k]) => k);
  partes.push(pendientes.length
    ? esc(pendientes.join(', ')) + '.<br><br>Se miden en PIE en una sesion. Hasta entonces, los porcentajes son orientativos.'
    : 'Nada pendiente.');
  partes.push('</p>');

  partes.push(`<p class="nota" style="margin-top:12px">Medido el ${esc(cal.medidoEl)} sobre ${esc(cal.medidoEn)}.</p>`);

  nodo.innerHTML = partes.join('');
}
