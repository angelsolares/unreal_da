// RNG determinista. Sin esto no hay comparacion honesta entre politicas:
// dos politicas solo son comparables si juegan exactamente la misma partida.

export function mulberry32(semilla) {
  let a = semilla >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class Azar {
  constructor(semilla) {
    this.semilla = semilla >>> 0;
    this._r = mulberry32(this.semilla);
  }
  real() { return this._r(); }
  rango(min, max) { return min + this._r() * (max - min); }
  entero(min, max) { return Math.floor(this.rango(min, max + 1)); }
  probabilidad(p) { return this._r() < p; }
  elegir(lista) { return lista[Math.floor(this._r() * lista.length)]; }
  barajar(lista) {
    const c = lista.slice();
    for (let i = c.length - 1; i > 0; i--) {
      const j = Math.floor(this._r() * (i + 1));
      [c[i], c[j]] = [c[j], c[i]];
    }
    return c;
  }
}

// --- estadistica basica para el panel de veredicto ---

export function percentil(valores, p) {
  if (!valores.length) return NaN;
  const v = valores.slice().sort((a, b) => a - b);
  const i = (v.length - 1) * p;
  const lo = Math.floor(i), hi = Math.ceil(i);
  return lo === hi ? v[lo] : v[lo] + (v[hi] - v[lo]) * (i - lo);
}

export function mediana(valores) { return percentil(valores, 0.5); }

export function media(valores) {
  if (!valores.length) return NaN;
  return valores.reduce((a, b) => a + b, 0) / valores.length;
}
