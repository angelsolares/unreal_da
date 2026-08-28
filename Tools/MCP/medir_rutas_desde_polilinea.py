# -*- coding: utf-8 -*-
# Mide los NUEVE corredores desde la polilinea pegada en guia_rutas_colocar.py,
# sin abrir el editor. Responde dos preguntas:
#   1) cuanto se anda de verdad por cada uno (metros y segundos a trote)
#   2) cuanta CURVA tiene -> si la sinuosidad es ~1.00 la carretera YA es recta
#      y no se puede acortar retrazandola: habria que mover la zona.
import json, math, re, sys

SRC = r"D:\Game Projects\Unreal DA\DarkAngelsPOC 5.8\Tools\MCP\guia_rutas_colocar.py"
JOG = 400.0  # uu/s, DefaultMovementState = Jog

txt = open(SRC, encoding='utf-8').read()
m = re.search(r'PUNTOS\s*=\s*json\.loads\(r"""(.*?)"""\)', txt, re.S)
P = json.loads(m.group(1))

ORDEN = ["JC", "CS", "SantuarioPuente", "PuenteAnfiteatro", "AnfiteatroElevador",
         "ElevadorGabrielC1", "GabrielC1C2", "GabrielC2C3", "GabrielC3Yesod"]
RAMAL = ["JardinMirador", "ClaroGazebo"]

NOMBRE = {
    "JC": "Jardin -> Claro", "CS": "Claro -> Santuario",
    "SantuarioPuente": "Santuario -> Puente", "PuenteAnfiteatro": "Puente -> Anfiteatro",
    "AnfiteatroElevador": "Anfiteatro -> Elevador", "ElevadorGabrielC1": "Elevador -> Gabriel I",
    "GabrielC1C2": "Gabriel I -> II", "GabrielC2C3": "Gabriel II -> III",
    "GabrielC3Yesod": "Gabriel III -> Yesod",
    "JardinMirador": "ramal: Mirador", "ClaroGazebo": "ramal: Gazebo",
}

def d3(a, b):
    return math.dist(a, b)

def medir(pts):
    largo = sum(d3(pts[i], pts[i+1]) for i in range(len(pts)-1))
    recto = d3(pts[0], pts[-1])
    salto = max((d3(pts[i], pts[i+1]) for i in range(len(pts)-1)), default=0)
    return largo, recto, salto

def mmss(seg):
    return "%d:%02d" % (int(seg) // 60, int(seg) % 60)

def fila(k, pts):
    largo, recto, salto = medir(pts)
    sin_ = largo / recto if recto else float('nan')
    t = largo / JOG
    piernas = largo / 18000.0  # 180 m = 45 s a trote
    return (NOMBRE[k], len(pts), largo/100, t, mmss(t), sin_, piernas, salto)

print("%-26s %4s %8s %8s %7s %9s %7s" %
      ("corredor", "pts", "metros", "a trote", "sinuos.", "piernas45s", "saltoMax"))
print("-" * 82)

tot_m = tot_t = 0.0
for k in ORDEN:
    n, pts, mts, t, ts, s, pi, sal = fila(k, P[k])
    tot_m += mts; tot_t += t
    print("%-26s %4d %8.1f %8s %7.3f %9.1f %8.0f" % (n, pts, mts, ts, s, pi, sal))

print("-" * 82)
print("%-26s %4s %8.1f %8s %7s %9.1f" %
      ("TOTAL espinazo", "", tot_m, mmss(tot_t), "", tot_m*100/18000.0))
print()
for k in RAMAL:
    n, pts, mts, t, ts, s, pi, sal = fila(k, P[k])
    print("%-26s %4d %8.1f %8s %7.3f %9.1f %8.0f" % (n, pts, mts, ts, s, pi, sal))

print()
print("=== JC y CS: que pasaria al recortar ===")
for k, objetivo in (("JC", 54000.0), ("CS", 36000.0)):
    pts = P[k]
    largo, recto, _ = medir(pts)
    print("%-20s largo=%.0f uu  recto=%.0f uu  sinuosidad=%.4f" % (k, largo, recto, largo/recto))
    print("%-20s objetivo=%.0f uu -> hay que QUITAR %.0f uu de separacion entre zonas"
          % ("", objetivo, largo - objetivo))
    dx = pts[-1][0] - pts[0][0]; dy = pts[-1][1] - pts[0][1]
    n = math.hypot(dx, dy)
    f = (largo - objetivo) / largo
    print("%-20s vector de acercamiento = (%.0f, %.0f) uu  (%.0f%% del trazado)"
          % ("", -dx/n * (largo-objetivo), -dy/n * (largo-objetivo), f*100))
    print()
