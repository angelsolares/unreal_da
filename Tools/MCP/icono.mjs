// Convierte una foto de un objeto sobre fondo liso en un icono de inventario:
// cuadrado, con transparencia y al tamanio que pide DCS.
//
//   node icono.mjs <origen.png> <destino.png> [lado]
//
// POR QUE A MANO Y NO CON UNA LIBRERIA: el proyecto no tiene dependencias de npm
// y no se va a meter una para esto. PNG de 8 bits sin entrelazar es un formato
// corto: cabecera, zlib y cinco filtros por linea. `node:zlib` pone lo dificil.
//
// EL COLOR DEL FONDO SE MIDE, NO SE SUPONE. La primera version daba por hecho
// que era blanco y salio un icono con el 60% de la imagen pintada: el fondo de
// `llave.png` es **gris 198**, que en pantalla pasa por blanco pero no lo es.
// Ahora se toma la mediana del marco de la imagen, que es fondo por definicion.
//
// LO QUE HACE, EN ORDEN:
//   1. saca el alfa por distancia a ese color de fondo —por umbral, no por
//      relleno desde el borde, que dejaria opaco el hueco del anillo de la
//      llave, que esta cerrado—;
//   2. quita la orla del fondo en los bordes suavizados deshaciendo la mezcla,
//      o el icono queda con un halo claro que canta sobre la UI oscura;
//   3. recorta a la caja del objeto, la cuadra centrada y le deja un margen;
//   4. reduce por promedio de area, ponderando el color por alfa para que los
//      pixeles transparentes no arrastren el color hacia el fondo.

import fs from 'node:fs';
import zlib from 'node:zlib';

const [, , origen, destino, ladoArg] = process.argv;
const LADO = Number(ladoArg) || 256;
// Distancia al color del fondo, por canal. Por debajo de la primera es fondo
// —hay que dar aire al ruido de compresion, que mueve el gris un par de puntos—;
// por encima de la segunda es objeto. En medio, la rampa del borde suavizado.
const RUIDO = 10;
const TINTA = 26;
const MARGEN = 0.06;   // aire alrededor, en fraccion del lado

// ---------------------------------------------------------------- descodificar
function leerPNG(buf) {
  if (buf.toString('latin1', 1, 4) !== 'PNG') throw new Error('no es un PNG');
  let o = 8;
  const trozos = [];
  let ancho, alto, bits, color;
  while (o < buf.length) {
    const n = buf.readUInt32BE(o);
    const tipo = buf.toString('latin1', o + 4, o + 8);
    const datos = buf.subarray(o + 8, o + 8 + n);
    if (tipo === 'IHDR') {
      ancho = datos.readUInt32BE(0);
      alto = datos.readUInt32BE(4);
      bits = datos[8];
      color = datos[9];
      if (datos[12] !== 0) throw new Error('PNG entrelazado, no soportado');
    } else if (tipo === 'IDAT') trozos.push(datos);
    else if (tipo === 'IEND') break;
    o += 12 + n;
  }
  if (bits !== 8) throw new Error(`PNG de ${bits} bits, solo se admiten 8`);
  const canales = { 0: 1, 2: 3, 4: 2, 6: 4 }[color];
  if (!canales) throw new Error(`tipo de color ${color} no soportado (¿paleta?)`);

  const crudo = zlib.inflateSync(Buffer.concat(trozos));
  const bpp = canales;
  const paso = ancho * bpp;
  const pix = Buffer.alloc(alto * paso);
  let p = 0;
  for (let y = 0; y < alto; y++) {
    const filtro = crudo[p++];
    const fila = crudo.subarray(p, p + paso);
    p += paso;
    const dst = y * paso;
    const arriba = (y > 0) ? dst - paso : -1;
    for (let x = 0; x < paso; x++) {
      const a = x >= bpp ? pix[dst + x - bpp] : 0;
      const b = arriba >= 0 ? pix[arriba + x] : 0;
      const c = (arriba >= 0 && x >= bpp) ? pix[arriba + x - bpp] : 0;
      let v = fila[x];
      if (filtro === 1) v += a;
      else if (filtro === 2) v += b;
      else if (filtro === 3) v += (a + b) >> 1;
      else if (filtro === 4) {
        const q = a + b - c, pa = Math.abs(q - a), pb = Math.abs(q - b), pc = Math.abs(q - c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      }
      pix[dst + x] = v & 255;
    }
  }

  // Todo a RGBA, que el resto del programa no quiera saber de tipos de color.
  const rgba = Buffer.alloc(ancho * alto * 4, 255);
  for (let i = 0, n = ancho * alto; i < n; i++) {
    const s = i * bpp, d = i * 4;
    if (canales === 1) { rgba[d] = rgba[d + 1] = rgba[d + 2] = pix[s]; }
    else if (canales === 2) { rgba[d] = rgba[d + 1] = rgba[d + 2] = pix[s]; rgba[d + 3] = pix[s + 1]; }
    else { rgba[d] = pix[s]; rgba[d + 1] = pix[s + 1]; rgba[d + 2] = pix[s + 2]; if (canales === 4) rgba[d + 3] = pix[s + 3]; }
  }
  return { ancho, alto, rgba, teniaAlfa: canales === 2 || canales === 4 };
}

// ------------------------------------------------------------------- codificar
function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xEDB88320 & -(c & 1));
  }
  return ~c >>> 0;
}

function trozo(tipo, datos) {
  const cabecera = Buffer.alloc(8);
  cabecera.writeUInt32BE(datos.length, 0);
  cabecera.write(tipo, 4, 'latin1');
  const cola = Buffer.alloc(4);
  cola.writeUInt32BE(crc32(Buffer.concat([cabecera.subarray(4), datos])), 0);
  return Buffer.concat([cabecera, datos, cola]);
}

function escribirPNG(ancho, alto, rgba) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(ancho, 0);
  ihdr.writeUInt32BE(alto, 4);
  ihdr[8] = 8; ihdr[9] = 6;                    // 8 bits, RGBA
  const paso = ancho * 4;
  const crudo = Buffer.alloc(alto * (paso + 1));
  for (let y = 0; y < alto; y++) {
    crudo[y * (paso + 1)] = 0;                 // filtro None: comprime de sobra
    rgba.copy(crudo, y * (paso + 1) + 1, y * paso, (y + 1) * paso);
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    trozo('IHDR', ihdr),
    trozo('IDAT', zlib.deflateSync(crudo, { level: 9 })),
    trozo('IEND', Buffer.alloc(0)),
  ]);
}

// ----------------------------------------------------------------------- obra
const src = leerPNG(fs.readFileSync(origen));
const { ancho: W, alto: H, rgba } = src;

// 0. El color del fondo: la mediana del marco de la imagen.
function colorDelFondo() {
  const canal = [[], [], []];
  const mete = (x, y) => {
    const d = (y * W + x) * 4;
    for (let k = 0; k < 3; k++) canal[k].push(rgba[d + k]);
  };
  for (let x = 0; x < W; x++) { mete(x, 0); mete(x, H - 1); }
  for (let y = 0; y < H; y++) { mete(0, y); mete(W - 1, y); }
  return canal.map((c) => c.sort((a, b) => a - b)[c.length >> 1]);
}

// 1 y 2. Alfa por distancia al fondo, y sin orla.
const fondo = colorDelFondo();
if (!src.teniaAlfa) {
  for (let i = 0, n = W * H; i < n; i++) {
    const d = i * 4;
    const lejos = Math.max(Math.abs(rgba[d] - fondo[0]),
                           Math.abs(rgba[d + 1] - fondo[1]),
                           Math.abs(rgba[d + 2] - fondo[2]));
    let a = (lejos - RUIDO) / (TINTA - RUIDO);
    a = a < 0 ? 0 : a > 1 ? 1 : a;
    if (a > 0 && a < 1) {
      // El pixel es objeto mezclado con fondo: se despeja el objeto.
      for (let k = 0; k < 3; k++) {
        const v = (rgba[d + k] - fondo[k] * (1 - a)) / a;
        rgba[d + k] = v < 0 ? 0 : v > 255 ? 255 : Math.round(v);
      }
    }
    rgba[d + 3] = Math.round(a * 255);
  }
}

// 3. Caja del objeto, cuadrada y centrada, con margen.
let x0 = W, y0 = H, x1 = -1, y1 = -1;
for (let y = 0; y < H; y++) {
  for (let x = 0; x < W; x++) {
    if (rgba[(y * W + x) * 4 + 3] > 8) {
      if (x < x0) x0 = x;
      if (x > x1) x1 = x;
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
    }
  }
}
if (x1 < 0) throw new Error('la imagen sale entera transparente: revisa los umbrales');
const lado = Math.max(x1 - x0 + 1, y1 - y0 + 1) * (1 + 2 * MARGEN);
const cx = (x0 + x1 + 1) / 2, cy = (y0 + y1 + 1) / 2;
const ox = cx - lado / 2, oy = cy - lado / 2;

// 4. Reduccion por promedio de area. El color va ponderado por alfa: si no, los
//    pixeles vacios —que no tienen color de verdad— tirarian del resultado.
const dst = Buffer.alloc(LADO * LADO * 4);
const escala = lado / LADO;
for (let j = 0; j < LADO; j++) {
  for (let i = 0; i < LADO; i++) {
    const ax = Math.floor(ox + i * escala), bx = Math.ceil(ox + (i + 1) * escala);
    const ay = Math.floor(oy + j * escala), by = Math.ceil(oy + (j + 1) * escala);
    let sr = 0, sg = 0, sb = 0, sa = 0, n = 0;
    for (let y = ay; y < by; y++) {
      for (let x = ax; x < bx; x++) {
        n++;
        if (x < 0 || y < 0 || x >= W || y >= H) continue;   // fuera: transparente
        const d = (y * W + x) * 4, a = rgba[d + 3] / 255;
        sr += rgba[d] * a; sg += rgba[d + 1] * a; sb += rgba[d + 2] * a; sa += a;
      }
    }
    const d = (j * LADO + i) * 4;
    if (sa > 0) {
      dst[d] = Math.round(sr / sa);
      dst[d + 1] = Math.round(sg / sa);
      dst[d + 2] = Math.round(sb / sa);
    }
    dst[d + 3] = Math.round(255 * sa / (n || 1));
  }
}

fs.writeFileSync(destino, escribirPNG(LADO, LADO, dst));
let opacos = 0;
for (let i = 0; i < LADO * LADO; i++) if (dst[i * 4 + 3] > 8) opacos++;
console.log(`OK ${destino}  ${LADO}x${LADO}  fondo rgb(${fondo})  ` +
            `origen ${W}x${H} -> caja ${x1 - x0 + 1}x${y1 - y0 + 1}  ` +
            `${(100 * opacos / (LADO * LADO)).toFixed(1)}% con tinta`);
