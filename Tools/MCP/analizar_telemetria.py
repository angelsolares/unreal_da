"""Analiza una sesion de telemetria de Malkuth.

    python analizar_telemetria.py                      # la sesion mas reciente
    python analizar_telemetria.py <ruta al csv>

Lo graba `telemetria.py`. Aguanta los dos formatos:

  viejo (12 col)  reloj;t;x;y;z;vel;vida;aguante;golpes;cerca;vivos;objetivo
  nuevo (13 col)  ...;cerca;vivos;cadaveres;objetivo

**El formato viejo no sirve para medir combate.** Su columna `cerca` contaba los
cadaveres como enemigos vivos, porque el grabador preguntaba "tiene controlador" y
un enemigo abatido lo conserva. Los tramos de combate salen inflados y los huecos
encogidos. Cuando se detecta, se avisa y no se imprime el veredicto de ritmo.

Las zonas van aqui dentro a proposito: son las Level Instances del maestro y
cambian poco. Si mueves una, actualizala aqui.
"""
import math
import os
import sys

UMBRAL_HUECO = 45.0      # s — el estandar de la casa: un beat cada 45 s
QUIETO = 20.0            # uu/s por debajo de lo cual se considera parado
SALTO = 800.0            # uu entre muestras: mas que esto es un teletransporte

ZONAS = {
    # hitos del recorrido a pie: son los que hacen util la atribucion por zona
    "Senda de Setos":     (-15297, -31618),   # disparador Zone_Jardin, donde arranca
    "Altar de la Senda":  ( -4000, -30900),
    "Umbral del Custodio":( 10295, -30152),
    "Claro (entrada)":    ( 26212, -22920),   # disparador Zone_Claro
    # origenes de las Level Instances
    "Jardin Geometrico":  (-60000, -60000),
    "Gabriel C3":         (-36240,  -4294),
    "Portal Yesod":       (-36240,  26736),
    "Gabriel C2":         (-23295,  -5412),
    "Elevador del Trono": (-18127,  17184),
    "Anfiteatro":         (-18127,  51184),
    "Gabriel C1":         (-18086,  13644),
    "Mirador de Sariel":  ( 12350,  -5660),
    "Puente Ascendente":  ( 16000,  60000),
    "El Claro":           ( 18212, -19920),
    "Santuario":          ( 44000,  48000),
    "Ruinas del Gazebo":  ( 64000,  16000),
    "Altar de la Senda":  ( -4000, -30900),
}


def hhmm(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def zona(x, y):
    mejor, dmin = "?", 1e18
    for k, (zx, zy) in ZONAS.items():
        d = (x - zx) ** 2 + (y - zy) ** 2
        if d < dmin:
            dmin, mejor = d, k
    return mejor, math.sqrt(dmin)


def ultima_sesion():
    aqui = os.path.dirname(os.path.abspath(__file__))
    carpeta = os.path.join(aqui, "..", "..", "Saved", "Telemetria")
    cs = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".csv")]
    if not cs:
        raise SystemExit("no hay sesiones en " + os.path.abspath(carpeta))
    return max(cs, key=os.path.getmtime)


def leer(ruta):
    filas, viejo = [], False
    with open(ruta, encoding="utf-8") as f:
        cab = f.readline().strip().split(";")
        viejo = "cadaveres" not in cab
        for ln in f:
            p = ln.rstrip("\n").split(";")
            if len(p) < len(cab):
                continue
            r = dict(t=float(p[1]), x=float(p[2]), y=float(p[3]), z=float(p[4]),
                     vel=float(p[5]), vida=float(p[6]), aguante=float(p[7]),
                     golpes=float(p[8]), cerca=int(p[9]), vivos=int(p[10]))
            r["cadaveres"] = 0 if viejo else int(p[11])
            r["obj"] = ";".join(p[11 if viejo else 12:])
            filas.append(r)
    return filas, viejo


def tramos_por(filas, clave):
    """Parte la sesion en tramos segun `clave(fila)` sea verdadero o falso."""
    fuera, act = [], None
    for r in filas:
        en = clave(r)
        if act is None or act[0] != en:
            if act:
                act[2] = r["t"]
                fuera.append(act)
            act = [en, r["t"], r["t"], r["x"], r["y"]]
    if act:
        act[2] = filas[-1]["t"]
        fuera.append(act)
    return fuera


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else ultima_sesion()
    filas, viejo = leer(ruta)
    if not filas:
        raise SystemExit("sin datos en " + ruta)

    t0, t1 = filas[0]["t"], filas[-1]["t"]
    dur = t1 - t0

    dist = 0.0
    for a, b in zip(filas, filas[1:]):
        d = math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))
        if d < SALTO:
            dist += d
    quieto = sum(b["t"] - a["t"] for a, b in zip(filas, filas[1:]) if b["vel"] < QUIETO)
    moviendo = [r["vel"] for r in filas if r["vel"] >= QUIETO]

    print("=" * 78)
    print(os.path.basename(ruta))
    print("SESION: %s  ·  %d muestras (%.1f Hz)" % (hhmm(dur), len(filas), len(filas) / dur))
    print("Recorrido: %.0f m  ·  parado: %s (%.0f%%)  ·  velocidad media al moverse: %.0f uu/s"
          % (dist / 100, hhmm(quieto), 100 * quieto / dur,
             sum(moviendo) / max(1, len(moviendo))))

    g1 = max(r["golpes"] for r in filas) - filas[0]["golpes"]
    print("Golpes recibidos: %d  ·  vida minima: %.0f  ·  cadaveres a la vista al final: %d"
          % (g1, min(r["vida"] for r in filas), filas[-1]["cadaveres"]))

    print()
    print("-" * 78)
    print("OBJETIVO EN PANTALLA")
    ant, ini, pos = None, t0, (0, 0)
    for r in filas + [None]:
        o = r["obj"] if r else "\x00"
        if o != ant:
            if ant is not None:
                zn, _ = zona(pos[0], pos[1])
                print("  t+%-6s %6s  %-20s %s"
                      % (hhmm(ini - t0), "%.0f s" % ((r["t"] if r else t1) - ini), zn, ant[:44]))
            ant, ini, pos = o, (r["t"] if r else t1), ((r["x"], r["y"]) if r else pos)

    if viejo:
        print()
        print("-" * 78)
        print("AVISO: fichero del grabador VIEJO. Su columna `cerca` contaba los cadaveres")
        print("como vivos, asi que el reparto combate/hueco no es fiable y no se imprime.")
        print("Lo unico firme aqui arriba es el recorrido y la traza de objetivos.")
        return

    print()
    print("-" * 78)
    combates = [tr for tr in tramos_por(filas, lambda r: r["cerca"] > 0) if tr[0]]
    huecos = [tr for tr in tramos_por(filas, lambda r: r["cerca"] > 0)
              if not tr[0] and tr[2] - tr[1] >= UMBRAL_HUECO]
    t_comb = sum(tr[2] - tr[1] for tr in combates)
    print("CON ENEMIGO VIVO A MENOS DE 20 m: %s (%.0f%%), en %d tramos"
          % (hhmm(t_comb), 100 * t_comb / dur, len(combates)))
    print("HUECOS DE MAS DE %.0f s: %d" % (UMBRAL_HUECO, len(huecos)))
    print()
    for tr in sorted(huecos, key=lambda h: -(h[2] - h[1])):
        zn, d = zona(tr[3], tr[4])
        print("  %-8s -> %-8s  %5s   empieza en %s (a %.0f m)"
              % (hhmm(tr[1] - t0), hhmm(tr[2] - t0), "%.0f s" % (tr[2] - tr[1]), zn, d / 100))

    print()
    print("-" * 78)
    print("TIEMPO POR ZONA")
    porz = {}
    for a, b in zip(filas, filas[1:]):
        zn, _ = zona(a["x"], a["y"])
        porz[zn] = porz.get(zn, 0.0) + (b["t"] - a["t"])
    for zn, s in sorted(porz.items(), key=lambda kv: -kv[1]):
        if s >= 2:
            print("  %-22s %-7s %.0f%%" % (zn, hhmm(s), 100 * s / dur))


if __name__ == "__main__":
    main()
