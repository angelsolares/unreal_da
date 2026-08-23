// Geometria en centimetros y con las convenciones de Unreal:
// X hacia el "norte" del plano, Y hacia el este, yaw en grados creciendo de X hacia Y.
// El editor pinta X hacia arriba e Y hacia la derecha para que la planta coincida
// con lo que se ve en el viewport cenital del editor.

export const GRADOS = Math.PI / 180;

export const v = (x, y) => ({ x, y });
export const suma = (a, b) => ({ x: a.x + b.x, y: a.y + b.y });
export const resta = (a, b) => ({ x: a.x - b.x, y: a.y - b.y });
export const escala = (a, k) => ({ x: a.x * k, y: a.y * k });
export const punto = (a, b) => a.x * b.x + a.y * b.y;
export const cruz = (a, b) => a.x * b.y - a.y * b.x;
export const largo = (a) => Math.hypot(a.x, a.y);
export const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
export const dist2 = (a, b) => (a.x - b.x) ** 2 + (a.y - b.y) ** 2;

export function normaliza(a) {
  const l = Math.hypot(a.x, a.y);
  return l < 1e-6 ? { x: 0, y: 0 } : { x: a.x / l, y: a.y / l };
}

export function desdeYaw(yawGrados) {
  const r = yawGrados * GRADOS;
  return { x: Math.cos(r), y: Math.sin(r) };
}

export function yawDe(a) {
  return Math.atan2(a.y, a.x) / GRADOS;
}

/** Diferencia angular con signo, siempre en (-180, 180]. */
export function deltaAngulo(desde, hasta) {
  let d = (hasta - desde) % 360;
  if (d > 180) d -= 360;
  if (d <= -180) d += 360;
  return d;
}

/** Gira `desde` hacia `hasta` como mucho `maxGrados`. */
export function giraHacia(desde, hasta, maxGrados) {
  const d = deltaAngulo(desde, hasta);
  if (Math.abs(d) <= maxGrados) return hasta;
  return desde + Math.sign(d) * maxGrados;
}

// ---------------------------------------------------------------- poligonos

export function dentroDePoligono(p, poli) {
  let dentro = false;
  for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
    const a = poli[i], b = poli[j];
    if ((a.y > p.y) !== (b.y > p.y) &&
        p.x < ((b.x - a.x) * (p.y - a.y)) / (b.y - a.y) + a.x) {
      dentro = !dentro;
    }
  }
  return dentro;
}

export function centroide(poli) {
  if (!poli.length) return { x: 0, y: 0 };
  let x = 0, y = 0;
  for (const p of poli) { x += p.x; y += p.y; }
  return { x: x / poli.length, y: y / poli.length };
}

export function cajaDe(poli) {
  const xs = poli.map(p => p.x), ys = poli.map(p => p.y);
  return { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
}

export function rectangulo(cx, cy, ancho, alto) {
  const hx = ancho / 2, hy = alto / 2;
  return [v(cx - hx, cy - hy), v(cx + hx, cy - hy), v(cx + hx, cy + hy), v(cx - hx, cy + hy)];
}

/** Interseccion de segmentos AB y CD. Devuelve el parametro t sobre AB o null. */
export function cruceSegmentos(a, b, c, d) {
  const r = resta(b, a), s = resta(d, c);
  const den = cruz(r, s);
  if (Math.abs(den) < 1e-9) return null;
  const t = cruz(resta(c, a), s) / den;
  const u = cruz(resta(c, a), r) / den;
  if (t < 0 || t > 1 || u < 0 || u > 1) return null;
  return t;
}

export function segmentoCortaPoligono(a, b, poli) {
  for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
    if (cruceSegmentos(a, b, poli[j], poli[i]) !== null) return true;
  }
  return false;
}

/** Distancia de un punto al segmento AB (para separar agentes de la cobertura). */
export function distAlSegmento(p, a, b) {
  const ab = resta(b, a);
  const l2 = ab.x * ab.x + ab.y * ab.y;
  if (l2 < 1e-9) return dist(p, a);
  let t = punto(resta(p, a), ab) / l2;
  t = Math.max(0, Math.min(1, t));
  return dist(p, { x: a.x + ab.x * t, y: a.y + ab.y * t });
}

export function distAlPoligono(p, poli) {
  let m = Infinity;
  for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
    m = Math.min(m, distAlSegmento(p, poli[j], poli[i]));
  }
  return m;
}

/**
 * Empuja un punto fuera de un poligono, dejandolo a `margen` del borde mas cercano.
 *
 * OJO con el signo: si el punto ya esta DENTRO, la direccion de salida es
 * (borde - punto), no (punto - borde). Tenerlo al reves empujaba hacia el interior
 * y dejaba a los agentes clavados dentro de un muro para siempre.
 */
export function empujaFuera(p, poli, margen) {
  const dentro = dentroDePoligono(p, poli);
  if (!dentro && distAlPoligono(p, poli) >= margen) return p;

  let mejor = null, mejorD = Infinity;
  for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
    const a = poli[j], b = poli[i];
    const ab = resta(b, a);
    const l2 = ab.x * ab.x + ab.y * ab.y;
    let t = l2 < 1e-9 ? 0 : punto(resta(p, a), ab) / l2;
    t = Math.max(0, Math.min(1, t));
    const q = { x: a.x + ab.x * t, y: a.y + ab.y * t };
    const d = dist(p, q);
    if (d < mejorD) { mejorD = d; mejor = q; }
  }

  let dir = dentro ? resta(mejor, p) : resta(p, mejor);
  if (largo(dir) < 1e-6) dir = resta(mejor, centroide(poli));   // justo en un vertice
  if (largo(dir) < 1e-6) dir = { x: 1, y: 0 };
  const u = normaliza(dir);
  return { x: mejor.x + u.x * margen, y: mejor.y + u.y * margen };
}

// ------------------------------------------------------------ linea de vision

/**
 * Linea de vision entre dos puntos con cota.
 * Una cobertura corta la vision solo si su cima queda por encima de los ojos
 * del mas alto de los dos. Asi el arquero del balcon dispara por encima del muro,
 * que es justo la señal de "Posicion" del PDF (§5.1).
 */
export function hayVision(a, cotaA, b, cotaB, coberturas, alturaOjos = 160) {
  const ojosA = cotaA + alturaOjos;
  const ojosB = cotaB + alturaOjos;
  const ojosAlto = Math.max(ojosA, ojosB);
  for (const c of coberturas) {
    if (!c.bloqueaVision) continue;
    const cima = (c.cota || 0) + (c.altura || 0);
    if (cima <= ojosAlto - 10) continue;   // se ve por encima
    if (segmentoCortaPoligono(a, b, c.poli)) return false;
  }
  return true;
}

/** ¿El punto `objetivo` cae dentro del cono de vision de `origen` mirando a `yaw`? */
export function enCono(origen, yaw, objetivo, aperturaGrados, alcance) {
  const d = resta(objetivo, origen);
  const l = largo(d);
  if (l > alcance) return false;
  if (l < 1e-3) return true;
  return Math.abs(deltaAngulo(yaw, yawDe(d))) <= aperturaGrados / 2;
}
