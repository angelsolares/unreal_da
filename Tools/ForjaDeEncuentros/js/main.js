// Arranque y cableado. El estado vive aqui y todo lo demas lo lee.

import { Editor } from './editor.js';
import { pintarVeredicto, pintarPropiedades, pintarCalibracion } from './ui.js';
import { desdeJSON, aJSON, nuevoEnemigo, nuevaCobertura, nuevaPlataforma, encuentroVacio, plataformaBajo } from './esquema.js';
import { ARQUETIPOS, ORDEN_ARQUETIPOS, FAMILIAS } from './catalogo.js';
import { correrLote } from './lote.js';
import { techoDeLaEspada, danoNecesario } from './diagnostico.js';

const E = {
  enc: null,
  cal: null,
  seleccion: null,
  capas: { rangos: true, conos: true, presion: false, vision: false },
  armas: null,
  lote: null,
  extra: {},
  testigo: null,
  fotograma: null,
  reproduciendo: false,
  variantes: []
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

let editor;
let vista3d = null;

// ---------------------------------------------------------------- arranque

async function arrancar() {
  E.cal = await (await fetch('datos/calibracion.json')).json();
  E.armas = await (await fetch('datos/armas.json')).json();
  try {
    E.enc = desdeJSON(await (await fetch('datos/encuentros/romper-la-linea.json')).text());
  } catch {
    E.enc = encuentroVacio('nuevo');
  }

  editor = new Editor($('#lienzo'), () => E);
  editor.alSeleccionar = (s) => { E.seleccion = s; refrescarPaneles(); editor.pintar(); };
  editor.alCambiar = () => { editor.pintar(); refrescarPaneles(); };
  editor.alCrearCaja = crearCaja;

  construirPaleta();
  conectarUI();
  editor.encajar();
  refrescarCabecera();
  refrescarPaneles();
  pintarCalibracion($('#hoja-calibracion'), E.cal);
  prepararReproductor();
  comprobarIA();
  comprobarUnreal();
}

function construirPaleta() {
  const nodo = $('#paleta');
  nodo.innerHTML = '';
  for (const id of ORDEN_ARQUETIPOS) {
    const meta = ARQUETIPOS[id];
    const b = document.createElement('button');
    b.innerHTML = `<span style="color:${meta.color}">${meta.glifo}</span> ${E.cal.arquetipos[id]?.nombre || id}`;
    b.onclick = () => {
      const c = editor.aMundo($('#lienzo').clientWidth / 2, $('#lienzo').clientHeight / 2);
      const e = nuevoEnemigo(id, Math.round(c.x), Math.round(c.y));
      E.enc.enemigos.push(e);
      E.enc.ordenPrevisto.push(e.id);
      E.seleccion = { tipo: 'enemigo', ref: e, id: e.id };
      editor.invalidarPresion();
      editor.pintar();
      refrescarPaneles();
    };
    nodo.appendChild(b);
  }
}

function crearCaja(modo, a, b) {
  const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
  const ancho = Math.abs(a.y - b.y), alto = Math.abs(a.x - b.x);
  // El arrastre da una caja en pantalla; el schema v2 la guarda como min/max.
  if (modo === 'cobertura') {
    const c = nuevaCobertura(cx, cy, alto, ancho);
    E.enc.coberturas.push(c);
    E.seleccion = { tipo: 'cobertura', ref: c, id: c.id };
  } else {
    const p = nuevaPlataforma(cx, cy, alto, ancho);
    E.enc.plataformas.push(p);
    E.seleccion = { tipo: 'plataforma', ref: p, id: p.id };
  }
  editor.invalidarPresion();
  editor.pintar();
  refrescarPaneles();
}

// ------------------------------------------------------------------ cableado

function conectarUI() {
  $$('#herramientas button[data-modo]').forEach(b => {
    b.onclick = () => {
      $$('#herramientas button[data-modo]').forEach(o => o.classList.remove('activo'));
      b.classList.add('activo');
      editor.modo = b.dataset.modo;
    };
  });

  for (const [capa, id] of [['rangos', '#capa-rangos'], ['conos', '#capa-conos'],
                            ['presion', '#capa-presion'], ['vision', '#capa-vision']]) {
    $(id).onchange = (e) => { E.capas[capa] = e.target.checked; editor.pintar(); };
  }

  $$('.pestanas button').forEach(b => {
    b.onclick = () => {
      $$('.pestanas button').forEach(o => o.classList.remove('activo'));
      b.classList.add('activo');
      $$('.hoja').forEach(h => h.classList.remove('visible'));
      $(`#hoja-${b.dataset.hoja}`).classList.add('visible');
    };
  });

  $('#btn-exportar').onclick = exportarAUnreal;
  $('#btn-importar').onclick = importarDeUnreal;

  $('#btn-criticar').onclick = pedirCritica;
  $('#btn-variantes').onclick = pedirVariantes;
  $('#btn-narrar').onclick = pedirNarracion;

  $('#btn-2d').onclick = () => ponerVista('2d');
  $('#btn-3d').onclick = () => ponerVista('3d');
  $('#camara').onchange = (e) => vista3d?.ponerCamara(e.target.value);
  $('#capa-lineas3d').onchange = (e) => vista3d?.alternarLineasDeEntrada(e.target.checked);

  $('#sel-encuentro').onchange = (e) => cargarDeDisco(e.target.value);
  $('#btn-simular').onclick = simular;
  $('#btn-encajar').onclick = () => editor.encajar();
  $('#btn-guardar').onclick = guardar;
  $('#btn-cargar').onclick = () => $('#fichero').click();
  $('#fichero').onchange = cargar;
  $('#btn-play').onclick = alternarReproduccion;
  $('#linea-tiempo').oninput = (e) => mostrarFotograma(+e.target.value);
  // La leyenda solo tiene sentido cuando hay una partida que mirar.
  // Cambiar de velocidad en marcha: reengancha el temporizador con el ritmo nuevo.
  $('#velocidad').onchange = () => {
    if (!E.reproduciendo) return;
    pararReproduccion();
    alternarReproduccion();
  };

  window.addEventListener('keydown', (e) => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
    if (e.key === 'v' || e.key === 'V') $('#herramientas button[data-modo="seleccionar"]').click();
    if (e.key === 'f' || e.key === 'F') editor.encajar();
    if (e.key === ' ') { e.preventDefault(); alternarReproduccion(); }
    if (e.key === 'Delete' || e.key === 'Backspace') borrarSeleccion();
  });
}

/**
 * El invariante del contrato §2.1: la cota de un enemigo es 0 o la de la
 * plataforma que lo contiene. Se restablece solo cada vez que algo se mueve, en
 * vez de dejar que el JSON se corrompa y avisar despues.
 */
function reasentarEnemigos() {
  for (const e of E.enc.enemigos) {
    const plat = plataformaBajo(E.enc, e.pos);
    e.cota = plat ? plat.cota : 0;
  }
}

function borrarSeleccion() {
  const s = E.seleccion;
  if (!s) return;
  if (s.tipo === 'enemigo') {
    E.enc.enemigos = E.enc.enemigos.filter(x => x.id !== s.id);
    E.enc.ordenPrevisto = E.enc.ordenPrevisto.filter(x => x !== s.id);
  } else if (s.tipo === 'cobertura') {
    E.enc.coberturas = E.enc.coberturas.filter(x => x.id !== s.id);
  } else if (s.tipo === 'plataforma') {
    E.enc.plataformas = E.enc.plataformas.filter(x => x.id !== s.id);
  } else if (s.tipo === 'rampa' && s.padre) {
    s.padre.accesos = s.padre.accesos.filter(a => a !== s.ref);
  }
  E.seleccion = null;
  editor.invalidarPresion();
  editor.pintar();
  refrescarPaneles();
}

// ------------------------------------------------------------------ capa IA

let ia = null;   // se importa perezosamente, como la 3D

async function cargarIA() {
  if (!ia) ia = await import('./ia.js');
  return ia;
}

async function comprobarIA() {
  const nodo = $('#ia-estado');
  const { estadoIA } = await cargarIA();
  const s = await estadoIA();
  nodo.className = 'titular ' + (s.disponible ? 'ok' : 'aviso');
  nodo.innerHTML = s.disponible
    ? `Modelo <strong>${escapar(s.modelo)}</strong>. ${escapar(s.nota || '')}`
    : `IA apagada — ${escapar(s.motivo)}<br><span style="color:var(--texto-tenue)">`
      + `Exporta <code>OPENAI_API_KEY</code>, instala con <code>npm install openai</code> y reinicia el servidor.</span>`;
  $$('#ia-botones button').forEach(b => { b.disabled = !s.disponible; });
  return s.disponible;
}

const escapar = (s) => String(s ?? '').replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function ocupadaIA(texto) {
  $$('#ia-botones button').forEach(b => { b.disabled = true; });
  $('#ia-salida').innerHTML = `<p class="nota">${escapar(texto)}</p>`;
}

function libreIA() { $$('#ia-botones button').forEach(b => { b.disabled = false; }); }

function fallaIA(err) {
  $('#ia-salida').innerHTML = `<div class="titular fallo">${escapar(err.message)}</div>`
    + (err.bruto ? `<div class="prosa">${escapar(err.bruto)}</div>` : '');
  libreIA();
}

async function pedirCritica() {
  if (!E.lote) { $('#ia-salida').innerHTML = '<p class="nota">Simula primero: la critica se apoya en los numeros.</p>'; return; }
  ocupadaIA('Leyendo el encuentro y su veredicto…');
  try {
    const { criticar } = await cargarIA();
    const texto = await criticar(E.enc, E.cal, E.lote);
    $('#ia-salida').innerHTML = `<div class="prosa">${escapar(texto)}</div>`;
    libreIA();
  } catch (err) { fallaIA(err); }
}

async function pedirNarracion() {
  if (!E.testigo) { $('#ia-salida').innerHTML = '<p class="nota">No hay partida testigo. Simula primero.</p>'; return; }
  ocupadaIA('Contando la partida…');
  try {
    const { narrar } = await cargarIA();
    const texto = await narrar(E.enc, E.testigo);
    $('#ia-salida').innerHTML = `<div class="prosa">${escapar(texto)}</div>`;
    libreIA();
  } catch (err) { fallaIA(err); }
}

async function pedirVariantes() {
  ocupadaIA('Pidiendo variantes…');
  try {
    const { generarVariantes } = await cargarIA();
    const juzgadas = await generarVariantes(E.enc, E.cal, E.armas, E.lote,
      (paso) => { $('#ia-salida').innerHTML = `<p class="nota">${escapar(paso)}</p>`; });
    E.variantes = juzgadas;
    pintarVariantes(juzgadas);
    libreIA();
  } catch (err) { fallaIA(err); }
}

function pintarVariantes(juzgadas) {
  const partes = [`<p class="nota">Ordenadas por lo que dice el simulador, no por
    el orden en que las propuso el modelo.</p>`];

  juzgadas.forEach((v, i) => {
    const p = v.propuesta;
    if (v.fallo) {
      partes.push(`<div class="variante"><h3>${escapar(p.nombre)}</h3>
        <div class="cifras" style="color:var(--fallo)">No se pudo simular: ${escapar(v.fallo)}</div></div>`);
      return;
    }
    const ver = v.lote.veredicto;
    const base = v.lote.porPolitica['cercano'].resumen;
    const vent = v.lote.porPolitica['ventaja'].resumen;
    const errores = v.problemas.filter(x => x.nivel === 'error');

    partes.push(`
      <div class="variante">
        <h3>${escapar(p.nombre)}</h3>
        <div class="semaforo">${ver.puertas.map(g => `<span class="luz ${g.estado}" title="${escapar(g.titulo)}: ${escapar(g.estado)}"></span>`).join('')}</div>
        <div class="cifras">
          espada sola ${(base.tasaVictoria * 100).toFixed(0)}% ·
          con armas ${(vent.tasaVictoria * 100).toFixed(0)}% ·
          ${p.enemigos.length} enemigos
        </div>
        <div class="porque">${escapar(p.queEnsena || '')}</div>
        <div class="porque" style="color:var(--texto-tenue)">${escapar(p.porQueFunciona || '')}</div>
        ${errores.length ? `<div class="problema error" style="margin-top:6px">${errores.map(e => escapar(e.texto)).join('<br>')}</div>` : ''}
        <div style="margin-top:7px;display:flex;gap:5px">
          <button data-cargar-variante="${i}">Cargar en el editor</button>
          <button data-guardar-variante="${i}">Guardar JSON</button>
        </div>
      </div>`);
  });

  $('#ia-salida').innerHTML = partes.join('');

  $$('#ia-salida [data-cargar-variante]').forEach(b => {
    b.onclick = () => cargarVariante(E.variantes[+b.dataset.cargarVariante]);
  });
  $$('#ia-salida [data-guardar-variante]').forEach(b => {
    b.onclick = () => descargar(E.variantes[+b.dataset.guardarVariante].encuentro);
  });
}

function cargarVariante(v) {
  if (!v?.encuentro) return;
  E.enc = v.encuentro;
  E.seleccion = null; E.lote = v.lote; E.testigo = v.lote?.testigo || null;
  E.fotograma = null; E.extra = {};
  editor.invalidarPresion();
  editor.encajar();
  if (vista3d) vista3d.reconstruir();
  refrescarPaneles();
  prepararReproductor();
  pintarVeredicto($('#hoja-veredicto'), E.lote);
  $$('.pestanas button')[0].click();
}

// -------------------------------------------------------------- puente Unreal

let ue = null;

async function cargarUE() {
  if (!ue) ue = await import('./unreal.js');
  return ue;
}

const offsetUE = () => ({
  x: +$('#ue-off-x').value || 0,
  y: +$('#ue-off-y').value || 0,
  z: +$('#ue-off-z').value || 0
});

async function comprobarUnreal() {
  const nodo = $('#ue-estado');
  const { estadoUnreal } = await cargarUE();
  const s = await estadoUnreal();
  nodo.className = 'titular ' + (s.conectado ? 'ok' : 'aviso');
  nodo.innerHTML = s.conectado
    ? `Editor conectado. Nivel abierto: <strong>${escapar(s.nivel)}</strong>`
    : `Editor no conectado — ${escapar(s.motivo)}`;
  $$('#ue-botones button').forEach(b => { b.disabled = !s.conectado; });
}

function ocupadaUE(t) {
  $$('#ue-botones button').forEach(b => { b.disabled = true; });
  $('#ue-salida').innerHTML = `<p class="nota">${escapar(t)}</p>`;
}
function libreUE() { $$('#ue-botones button').forEach(b => { b.disabled = false; }); }
function fallaUE(err) {
  $('#ue-salida').innerHTML = `<div class="titular fallo">${escapar(err.message)}</div>`;
  libreUE();
}

async function exportarAUnreal() {
  ocupadaUE('Colocando el encuentro en el editor…');
  try {
    const { exportar } = await cargarUE();
    const r = await exportar(E.enc, offsetUE(), $('#ue-confirmar').checked);
    const partes = [
      `<div class="titular ${r.resumen.desviados ? 'aviso' : 'ok'}">
         ${r.resumen.enemigos} enemigos, ${r.resumen.sello} muros de sello y
         ${r.resumen.marcas} marcas en <strong>${escapar(r.nivel)}</strong>.
         ${r.borrados ? `Se limpiaron ${r.borrados} de la exportacion anterior.` : ''}
       </div>`,
      `<p class="nota">${escapar(r.nota)}</p>`
    ];
    if (r.resumen.desviados) {
      partes.push(`<h2>No cuadran</h2>`);
      for (const d of r.desviados) {
        partes.push(`<div class="problema error">${escapar(d.etiqueta)}: pedido
          ${d.pedido.join(', ')} · el editor dice ${d.real.join(', ')}</div>`);
      }
    } else {
      partes.push(`<p class="nota">Releido del editor uno a uno: <strong>todo en su
        sitio</strong>. Si algo se hubiera colocado mal, saldria aqui.</p>`);
    }
    for (const a of r.avisos || []) partes.push(`<div class="problema">${escapar(a)}</div>`);
    $('#ue-salida').innerHTML = partes.join('');
    libreUE();
    comprobarUnreal();
  } catch (err) { fallaUE(err); }
}

async function importarDeUnreal() {
  ocupadaUE('Leyendo el editor…');
  try {
    const { importar, comparar, aplicarCambios } = await cargarUE();
    const leido = await importar(offsetUE());
    const filas = comparar(E.enc, leido);
    const movidos = filas.filter(f => f.estado === 'movido');

    const marca = { igual: 'ok', movido: 'aviso', falta: 'fallo', sobra: 'aviso' };
    const partes = [
      `<div class="titular ${movidos.length ? 'aviso' : 'ok'}">
        ${leido.total} actores de la Forja en <strong>${escapar(leido.nivel)}</strong>.
        ${movidos.length ? `${movidos.length} se han movido desde la ultima exportacion.` : 'Nada ha cambiado.'}
      </div>`,
      '<table class="datos"><tr><th>enemigo</th><th>estado</th></tr>'
    ];
    for (const f of filas) {
      partes.push(`<tr class="${f.estado === 'igual' ? '' : 'destacada'}">
        <td>${escapar(f.etiqueta)}</td><td style="text-align:left">${escapar(f.texto)}</td></tr>`);
    }
    partes.push('</table>');
    if (movidos.length) {
      partes.push(`<button id="btn-aplicar-ue" class="principal" style="margin-top:8px">
        Traer esas ${movidos.length} posiciones al encuentro</button>`);
      partes.push(`<p class="nota">Colocar a ojo en Unreal y volver a simular es el
        bucle que cierra la fase E.</p>`);
    }
    $('#ue-salida').innerHTML = partes.join('');

    const boton = $('#btn-aplicar-ue');
    if (boton) boton.onclick = () => {
      const n = aplicarCambios(E.enc, filas);
      E.lote = null; E.testigo = null; E.fotograma = null;
      editor.invalidarPresion();
      editor.pintar();
      if (vista3d) vista3d.reconstruir();
      refrescarPaneles();
      prepararReproductor();
      pintarVeredicto($('#hoja-veredicto'), null);
      $('#ue-salida').innerHTML = `<div class="titular ok">${n} posiciones traidas del
        editor. Vuelve a simular para ver si el cambio mejora algo.</div>`;
    };
    libreUE();
  } catch (err) { fallaUE(err); }
}

// --------------------------------------------------------------- vista 2D/3D

/**
 * La 3D se carga la primera vez que se pide, no al arrancar: son 720 KB de
 * Three y la mayoria de las sesiones se quedan en la planta.
 */
async function ponerVista(cual) {
  const es3d = cual === '3d';
  $('#btn-2d').classList.toggle('activo', !es3d);
  $('#btn-3d').classList.toggle('activo', es3d);
  $('#lienzo').classList.toggle('oculto', es3d);
  $('#lienzo3d').classList.toggle('oculto', !es3d);
  $('#camara').classList.toggle('oculto', !es3d);
  $('#lbl-lineas').classList.toggle('oculto', !es3d);
  $('#pista').textContent = es3d
    ? 'arrastrar: orbitar · rueda: acercar'
    : 'rueda: zoom · arrastrar fondo: mover · supr: borrar';

  if (!es3d) { vista3d?.parar(); editor.pintar(); return; }

  if (!vista3d) {
    $('#pista').textContent = 'cargando Three.js…';
    try {
      const { Vista3D } = await import('./vista3d.js');
      vista3d = new Vista3D($('#lienzo3d'), () => E);
    } catch (err) {
      $('#pista').textContent = 'No se pudo cargar la vista 3D: ' + err.message;
      console.error(err);
      ponerVista('2d');
      return;
    }
    $('#pista').textContent = 'arrastrar: orbitar · rueda: acercar';
  }

  vista3d.reconstruir();
  vista3d.ponerCamara($('#camara').value);
  vista3d.alternarLineasDeEntrada($('#capa-lineas3d').checked);
  vista3d.mostrar(E.fotograma);
  vista3d.arrancar();
}

/** El editor y la 3D miran el mismo estado; esto los mantiene en fase. */
function refrescarVistas() {
  editor.pintar();
  if (vista3d?.activa) vista3d.mostrar(E.fotograma);
}

// ------------------------------------------------------------------ paneles

function refrescarCabecera() {
  $('#sub-encuentro').textContent = `${E.enc.nombre} · ${E.enc.enemigos.length} enemigos`;
  const pend = Object.values(E.cal.procedencia || {}).filter(t => /^ESTIMADO/i.test(t)).length;
  $('#sub-calibracion').textContent = `calibracion ${E.cal.medidoEl} · ${pend} valores por medir`;
}

function refrescarPaneles() {
  refrescarCabecera();
  pintarPropiedades($('#hoja-propiedades'), E.enc, E.seleccion, E.cal);
  conectarPropiedades();
}

function conectarPropiedades() {
  const hoja = $('#hoja-propiedades');

  hoja.querySelectorAll('[data-campo]').forEach(inp => {
    inp.onchange = () => {
      const campo = inp.dataset.campo;
      const valor = inp.type === 'number' ? +inp.value : inp.value;
      const destino = E.seleccion?.ref;
      if (campo === 'nombre' || campo === 'id') { E.enc[campo] = valor; }
      else if (!destino) return;
      else if (campo === 'pos.x') destino.pos.x = valor;
      else if (campo === 'pos.y') destino.pos.y = valor;
      else destino[campo] = valor;
      // Cambiar la cota de una plataforma deja a sus enemigos flotando o
      // enterrados: el invariante del contrato §2.1 se restablece aqui mismo.
      if (campo === 'cota' && E.seleccion.tipo === 'plataforma') reasentarEnemigos();
      editor.invalidarPresion();
      editor.pintar();
      refrescarPaneles();
    };
  });

  // Las dos casillas del drop, que ya no son una politica sino dos booleanos.
  hoja.querySelectorAll('[data-drop]').forEach(chk => {
    chk.onchange = () => {
      const e = E.seleccion?.ref;
      if (!e) return;
      e.drop = { principal: false, secundaria: false, ...e.drop };
      e.drop[chk.dataset.drop] = chk.checked;
      editor.pintar();
      refrescarPaneles();
    };
  });

  hoja.querySelectorAll('[data-enemigo]').forEach(chip => {
    chip.onclick = (ev) => {
      if (ev.target.tagName === 'BUTTON') return;
      const e = E.enc.enemigos.find(x => x.id === chip.dataset.enemigo);
      E.seleccion = { tipo: 'enemigo', ref: e, id: e.id };
      editor.pintar();
      refrescarPaneles();
    };
  });

  const mover = (id, delta) => {
    const o = E.enc.ordenPrevisto;
    const i = o.indexOf(id);
    if (i < 0) { o.push(id); return; }
    const j = i + delta;
    if (j < 0 || j >= o.length) return;
    [o[i], o[j]] = [o[j], o[i]];
  };
  hoja.querySelectorAll('[data-subir]').forEach(b => {
    b.onclick = () => { mover(b.dataset.subir, -1); editor.pintar(); refrescarPaneles(); };
  });
  hoja.querySelectorAll('[data-bajar]').forEach(b => {
    b.onclick = () => { mover(b.dataset.bajar, 1); editor.pintar(); refrescarPaneles(); };
  });
  hoja.querySelectorAll('[data-borrar], [data-borrar-forma]').forEach(b => {
    b.onclick = () => borrarSeleccion();
  });
}

// ---------------------------------------------------------------- simulacion

async function simular() {
  pararReproduccion();
  const boton = $('#btn-simular');
  boton.disabled = true;
  boton.textContent = 'Simulando…';
  $('#hoja-veredicto').innerHTML = '<p class="nota">Corriendo 5 politicas × 200 partidas…</p>';
  $$('.pestanas button')[0].click();
  await new Promise(r => setTimeout(r, 30));   // dejar pintar

  try {
    E.lote = correrLote(E.enc, E.cal, E.armas, { partidas: 200 });
    E.extra = {};
    if (E.lote.veredicto.puertas.find(p => p.id === 'ganable-espada')?.estado !== 'ok') {
      // Solo cuando hace falta: es lo que mas tarda y lo que mas ayuda.
      boton.textContent = 'Diagnosticando…';
      await new Promise(r => setTimeout(r, 30));
      E.extra.techo = techoDeLaEspada(E.enc, E.cal, E.armas);
      E.extra.dano = danoNecesario(E.enc, E.cal, E.armas);
    }
    E.testigo = E.lote.testigo;
    prepararReproductor();
    pintarVeredicto($('#hoja-veredicto'), E.lote, E.extra);
  } catch (err) {
    $('#hoja-veredicto').innerHTML = `<div class="titular fallo">Se rompio la simulacion: ${err.message}</div>`;
    console.error(err);
  }

  boton.disabled = false;
  boton.textContent = 'Simular (200 partidas)';
}

// ---------------------------------------------------------------- reproductor

function prepararReproductor() {
  pararReproduccion();
  const t = E.testigo;
  const barra = $('#linea-tiempo');
  const play = $('#btn-play');

  if (!t || !t.fotogramas.length) {
    // Sin partida grabada no hay nada que reproducir. Decirlo, en vez de que el
    // boton se quede mudo: un Play que no responde parece roto.
    barra.max = 0;
    barra.value = 0;
    barra.disabled = true;
    play.disabled = true;
    play.title = 'Simula primero: el reproductor muestra la partida testigo';
    $('#leyenda').classList.add('oculto');
    E.fotograma = null;
    $('#reloj').textContent = '—';
    $('#arma-actual').textContent = '—';
    $('#linea-eventos').textContent = 'Pulsa "Simular" para grabar una partida testigo y poder verla aqui.';
    if (editor) editor.pintar();
    return;
  }

  barra.disabled = false;
  play.disabled = false;
  $('#leyenda').classList.remove('oculto');
  play.title = 'Reproducir la partida testigo (espacio)';
  barra.max = t.fotogramas.length - 1;
  barra.value = 0;

  // Los fotogramas no se graban uno por tick: el intervalo real sale de sus
  // propias marcas de tiempo, o la reproduccion iria al doble de velocidad.
  const a = t.fotogramas[0]?.t ?? 0;
  const b = t.fotogramas[1]?.t ?? (a + 1 / 30);
  E.msPorFotograma = Math.max(16, (b - a) * 1000);

  mostrarFotograma(0);
}

function mostrarFotograma(i) {
  const t = E.testigo;
  if (!t || !t.fotogramas.length) return;

  const idx = Math.max(0, Math.min(t.fotogramas.length - 1, Math.round(i)));
  const f = t.fotogramas[idx];
  E.fotograma = f;
  $('#linea-tiempo').value = idx;
  $('#reloj').textContent = `${f.t.toFixed(1)} s`;

  // Que lleva en la mano ahora mismo: es la mitad de lo que se viene a mirar.
  const principal = f.arma ? nombreArma(f.arma) : 'Espada de Malakh';
  const municion = f.municion != null ? ` (${f.municion})` : '';
  const off = f.offHand ? ` + ${nombreArma(f.offHand)}` : '';
  $('#arma-actual').textContent = `${principal}${municion}${off}`;
  $('#arma-actual').style.color = f.arma
    ? (FAMILIAS[f.arma]?.color || 'var(--oro)') : 'var(--texto-tenue)';

  const recientes = t.eventos.filter(e => e.t <= f.t).slice(-3).reverse();
  $('#linea-eventos').textContent = recientes.map(describir).join('   ·   ') || '…';

  refrescarVistas();
}

function nombreArma(familia) {
  return FAMILIAS[familia]?.nombre || familia;
}

function describir(ev) {
  const n = (id) => {
    if (id === 'malakh') return 'Malakh';
    const e = E.enc.enemigos.find(x => x.id === id);
    return e ? (e.etiqueta || e.arquetipo.split('_')[0]) : id;
  };
  switch (ev.tipo) {
    case 'suelta': return `${ev.t}s ${n(ev.agente)} suelta ${nombreArma(ev.arma)}`;
    case 'equipa': return `${ev.t}s Malakh empuña ${nombreArma(ev.arma)}`;
    case 'desmaterializa': return `${ev.t}s se desmaterializa ${nombreArma(ev.arma)} (${ev.motivo})`;
    case 'descarte': return `${ev.t}s ${ev.nombre}`;
    case 'agotada': return `${ev.t}s se agota ${nombreArma(ev.arma)}`;
    case 'sealBreak': return `${ev.t}s SEAL BREAK — purga ${ev.purgado.map(nombreArma).join(', ')}`;
    case 'dropExpirado': return `${ev.t}s expira ${nombreArma(ev.arma)} en el suelo`;
    case 'zona': return `${ev.t}s estandarte clavado`;
    case 'golpe': return `${ev.t}s ${n(ev.de)} → ${n(ev.a)} ${ev.dano}${ev.bloqueado ? ' (bloqueado)' : ''}`;
    case 'baja': return `${ev.t}s cae ${n(ev.agente)}`;
    case 'esquiva': return `${ev.t}s Malakh esquiva`;
    case 'esquivado': return `${ev.t}s esquivado a ${n(ev.de)}`;
    case 'bebe': return `${ev.t}s Malakh bebe (${ev.restantes})`;
    case 'guardiaRota': return `${ev.t}s guardia rota`;
    case 'aturdido': return `${ev.t}s ${n(ev.agente)} aturdido`;
    case 'disparo': return `${ev.t}s ${n(ev.agente)} dispara`;
    case 'victoria': return `${ev.t}s VICTORIA`;
    case 'derrota': return `${ev.t}s derrota — ${ev.motivo}`;
    default: return `${ev.t}s ${ev.tipo}`;
  }
}

let temporizador = null;

function pararReproduccion() {
  clearInterval(temporizador);
  temporizador = null;
  E.reproduciendo = false;
  $('#btn-play').textContent = '▶';
}

function alternarReproduccion() {
  if (!E.testigo || !E.testigo.fotogramas.length) return;

  if (E.reproduciendo) { pararReproduccion(); return; }

  const barra = $('#linea-tiempo');
  // Si se acabo, rebobinar: pulsar Play al final no debe quedarse quieto.
  if (+barra.value >= +barra.max) mostrarFotograma(0);

  E.reproduciendo = true;
  $('#btn-play').textContent = '❚❚';
  const factor = parseFloat($('#velocidad').value) || 1;
  temporizador = setInterval(() => {
    const i = +barra.value + 1;
    if (i > +barra.max) { pararReproduccion(); return; }
    mostrarFotograma(i);
  }, (E.msPorFotograma || 1000 / 30) / factor);
}

// ------------------------------------------------------------------- ficheros

async function cargarDeDisco(id) {
  try {
    E.enc = desdeJSON(await (await fetch(`datos/encuentros/${id}.json`)).text());
  } catch (err) {
    alert(`No se pudo cargar "${id}": ${err.message}`);
    return;
  }
  E.seleccion = null; E.lote = null; E.testigo = null; E.fotograma = null; E.extra = {};
  editor.invalidarPresion();
  editor.encajar();
  refrescarPaneles();
  if (vista3d) vista3d.reconstruir();
  prepararReproductor();
  pintarVeredicto($('#hoja-veredicto'), null);
}

function descargar(enc) {
  const blob = new Blob([aJSON(enc)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${enc.id}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function guardar() { descargar(E.enc); }

function cargar(ev) {
  const f = ev.target.files[0];
  if (!f) return;
  const lector = new FileReader();
  lector.onload = () => {
    try {
      E.enc = desdeJSON(lector.result);
      E.seleccion = null; E.lote = null; E.testigo = null; E.fotograma = null; E.extra = {};
      editor.invalidarPresion();
      editor.encajar();
      refrescarPaneles();
      prepararReproductor();
      pintarVeredicto($('#hoja-veredicto'), null);
    } catch (err) {
      alert('Ese JSON no se pudo leer: ' + err.message);
    }
  };
  lector.readAsText(f);
  ev.target.value = '';
}

// Es una herramienta de dev: el estado, a mano desde la consola del navegador.
// `forja.E.enc` es el encuentro vivo, `forja.lote()` el ultimo veredicto crudo,
// y `forja.vista3d` la escena de Three para hurgar en ella.
window.forja = {
  E,
  get editor() { return editor; },
  get vista3d() { return vista3d; },
  lote: () => E.lote,
  simular,
  ponerVista
};

arrancar();
