# Partida seca: recorre la ruta del piloto sobre la geometria real y mide el suelo,
# sin jugar. Se lanza con  node ue.mjs py Tools/MCP/partida_simulada  (sin extension aqui: ver la nota del .PY que mata el MCP)
#
# Criterio de la casa (ver la nota "Medir si se puede andar"): muestrear la cota del
# suelo cada 50 uu y marcar los saltos mayores que MaxStepHeight (Malakh: 45). El
# solape de capsula NO vale, y la traza tiene que bajar desde justo encima del suelo
# anterior o las copas de los arboles hacen de techo.
#
# OJO CON LO QUE **NO** MIDE: solo ve el suelo bajo la linea. No detecta estorbos de
# lado —un tronco junto al camino paro al piloto 794 s en el Gazebo— y en esta casa ya
# quedo demostrado que las trazas de capsula mienten sobre eso. "Cero huecos" no es
# "se puede andar": eso solo lo dice empujar el pawn en PIE.
import unreal, math, json, re
V = unreal.Vector
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ues.get_game_world() or ues.get_editor_world()
print("mundo:", "PIE" if ues.get_game_world() else "editor")

# --- traer BEATS y construir_ruta del propio piloto, sin ejecutar su despachador
import os
_aqui = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.path.join(
    unreal.Paths.project_dir(), "Tools", "MCP")
src = open(os.path.join(_aqui, "piloto" + "." + "py"), encoding="utf-8").read()
corte = src.index('a = open(CARPETA + "/accion.txt")')
mod = {}
exec(compile(src[:corte], "piloto_parcial", "exec"), mod)
BEATS = mod["BEATS"]
print("beats del piloto:", len(BEATS))

FOLLAJE = ("Fern", "Grass", "Ivy", "Clover", "Windflower", "Dandelion", "GroundCover",
           "Pratia", "Crownbeard", "Everlasting", "LilyOfTheValley", "Thatching", "Wheat",
           "Petalo", "Musgo", "Hydrangea", "Viburnum")
IGN = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    cn = a.get_class().get_name()
    if any(k in cn for k in ("ZoneTrigger", "Trigger", "Descenso", "BP_DA_Arena", "CelestialRay", "PicoFila")):
        IGN.append(a); continue
    c = a.static_mesh_component if hasattr(a, "static_mesh_component") else None
    m = c.static_mesh if c else None
    if m and any(k in m.get_name() for k in FOLLAJE):
        IGN.append(a)
print("ignorados (follaje y disparadores):", len(IGN))

def suelo(x, y, desde=6000.0):
    h = unreal.SystemLibrary.line_trace_single(w, V(x, y, desde), V(x, y, -900),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, IGN, unreal.DrawDebugTrace.NONE, False)
    t = h.to_tuple() if h else None
    return (t[4].z, t[9].get_actor_label() if t[9] else "?") if t and t[0] else (None, None)

# --- peligros, para decir en que tramo se cobran
snares = []
picos = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    cn = a.get_class().get_name()
    l = a.get_actor_location()
    if cn == "BP_CelestialRay_C" and a.get_editor_property("Activo"):
        snares.append((a.get_actor_label(), l.x, l.y, float(a.get_editor_property("TriggerRadius"))))
    elif cn == "BP_DA_PicoFila_C":
        picos.append((a.get_actor_label(), l.x, l.y, float(a.get_editor_property("RadioDano"))))
print("snares activos: %d | filas de picos: %d" % (len(snares), len(picos)))

RUTA = mod["construir_ruta"](w)
print("puntos de la ruta real:", len(RUTA))
PASO = 50.0
ESCALON = 45.0
resumen = []
_ult = None
for k in range(len(RUTA) - 1):
    n0, p0, _ = RUTA[k]
    n1, p1, _ = RUTA[k + 1]
    n0 = n0 or _ult or "(via)"
    if RUTA[k][0]: _ult = RUTA[k][0]
    dx, dy = p1.x - p0.x, p1.y - p0.y
    L = math.hypot(dx, dy)
    if L < 1.0:
        continue
    ux, uy = dx / L, dy / L
    zant = None
    huecos = 0; escalones = []; peor = 0.0; culpable = ""
    n = int(L // PASO)
    for i in range(n + 1):
        x, y = p0.x + ux * i * PASO, p0.y + uy * i * PASO
        z, quien = suelo(x, y, 6000.0 if zant is None else zant + 260.0)
        if z is None and zant is not None:
            z, quien = suelo(x, y, 6000.0)      # se subio de golpe: mira desde arriba
        if z is None:
            huecos += 1; zant = None; continue
        if zant is not None:
            d = z - zant
            if d > ESCALON or d < -200.0:
                escalones.append((round(i * PASO), round(d), quien))
                if abs(d) > abs(peor): peor = d; culpable = quien
        zant = z
    pel = []
    for nom, sx, sy, rad in snares:
        for i in range(0, n + 1, 4):
            x, y = p0.x + ux * i * PASO, p0.y + uy * i * PASO
            if math.hypot(sx - x, sy - y) < rad:
                pel.append("rayo:" + nom.replace("Snare_", "")); break
    for nom, sx, sy, rad in picos:
        for i in range(0, n + 1, 2):
            x, y = p0.x + ux * i * PASO, p0.y + uy * i * PASO
            if math.hypot(sx - x, sy - y) < rad + 100.0:
                pel.append("picos:" + nom.replace("Fila_Picos_", "F")); break
    resumen.append({"de": n0 or "(punto %d)" % k, "a": n1 or "(punto %d)" % (k + 1),
                    "largo": round(L), "muestras": n + 1, "huecos": huecos,
                    "escalones": escalones, "peor": round(peor), "culpable": culpable,
                    "peligros": pel})

from collections import OrderedDict
por_beat = OrderedDict()
for r in resumen:
    b = por_beat.setdefault(r["de"], {"largo": 0, "huecos": 0, "muros": [], "caidas": [], "pel": set()})
    b["largo"] += r["largo"]; b["huecos"] += r["huecos"]; b["pel"].update(r["peligros"])
    for m, d, q in r["escalones"]:
        (b["muros"] if d > 0 else b["caidas"]).append((d, q))
print("")
print("%-28s %8s %7s %7s %8s  %s" % ("TRAMO (desde el beat)", "largo", "sin", "muros", "caidas", "peligros"))
print("%-28s %8s %7s %7s %8s" % ("", "(uu)", "suelo", ">45", ">200"))
for b, v in por_beat.items():
    print("%-28s %8d %7d %7d %8d  %s" % (b[:28], v["largo"], v["huecos"], len(v["muros"]), len(v["caidas"]),
        ",".join(sorted(v["pel"])[:5])))
print("")
print("== detalle de lo que bloquea (muro > 45 subiendo)")
for b, v in por_beat.items():
    if not v["muros"] and not v["huecos"]:
        continue
    print("  %s: %d muros, %d sin suelo" % (b, len(v["muros"]), v["huecos"]))
    vistos = {}
    for d, q in v["muros"]:
        vistos[q] = max(vistos.get(q, 0), d)
    for q, d in sorted(vistos.items(), key=lambda x: -x[1])[:8]:
        print("      +%4d  %s" % (d, q))
print("tramos de ruta recorridos:", len(resumen))
