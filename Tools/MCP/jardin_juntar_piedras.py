# -*- coding: utf-8 -*-
import json
import math

# Acerca al centro las piedras del Jardin sin que ninguna acabe encima de un camino.
#
# ### QUE SE MUEVE Y QUE NO
#
# Solo los **23 `Ladera_*`** de `Fondo/Montanas`: las piedras sueltas repartidas
# alrededor del prado, a 400-690 m del centro y de 29 a 54 m de radio. En esa
# carpeta hay 58 cosas mas que **no se tocan**: `Monte_Medio_*` (74-116 km),
# `Monte_Lejos_*` y `Aguja_*` (122-202 km). Esos son el telon del horizonte, y
# acercarlos deshace la linea de montanas, que es de lo poco que da escala al valle.
#
# ### SE PARTE SIEMPRE DE LAS POSICIONES ORIGINALES
#
# La tabla `ORIGEN` de abajo son las coordenadas **antes de la primera pasada**,
# leidas del nivel. El script no lee donde esta cada piedra ahora: recalcula desde
# ahi. Sin eso, relanzarlo con otro `FACTOR` contraeria sobre lo ya contraido y
# cada pasada apretaria mas. Asi `FACTOR` significa siempre lo mismo y se puede
# subir y bajar hasta dar con el numero.
#
# ### EL FALLO QUE ESTO CORRIGE
#
# La primera version protegia **solo la `Senda_*` interna del Jardin**, que es lo
# unico que se ve desde el submapa. Pero la carretera al Claro y el ramal del
# Mirador son actores del **maestro**, dentro de `Conexiones/`, y desde dentro de
# la Level Instance no existen. Resultado: `Ladera_72`, `_79` y `_82` acabaron
# encima de la calzada.
#
# La cura es recoger la red de caminos **con el maestro abierto**, pasarla a
# coordenadas del submapa (restando el offset de la LI) y solo entonces abrir el
# Jardin. Regla general: **si lo que colocas vive en un submapa y lo que tiene que
# respetar vive en el maestro, hay que cruzar los dos sistemas de coordenadas a
# mano; ninguna consulta los ve a la vez.**
#
# ### COMO SE ACERCAN
#
# Contraccion radial hacia el origen del submapa: `r_nuevo = r * FACTOR`, angulo
# intacto. Asi se conserva que piedra esta al norte y cual al sureste, y solo se
# cierra el anillo.
#
# La Z **no se recalcula**: estas mallas estan hundidas a proposito (z de -137 a
# -342 con escalas de 3,5 a 6,8) y lo que asoma es la punta. Reasentarlas contra
# el suelo las sacaria enteras.
#
# ### QUE SE SOLAPEN ENTRE ELLAS ES NORMAL
#
# Antes de tocar nada ya habia **32 pares solapados** de 253, con el peor a -7.680.
# Son rocas kitbasheadas, hechas para interpenetrarse y formar macizos. Al apretar
# el anillo suben a ~50: eso no es un defecto, es lo que significa "juntarlas".

FACTOR = 0.70          # 0,70 = anillo un 30% mas cerrado
MARGEN = 2500.0        # holgura entre el borde de la piedra y el eje del camino
CARPETA = "Fondo/Montanas"

JARDIN = "/Game/DarkAngels/Maps/L_DA_Malkuth_Jardin_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
OFFSET = (-60000.0, -60000.0)      # LI_01_JardinGeometrico
CAMINOS = ("Conexiones/JardinClaro", "Conexiones/JardinMirador")

# Posiciones ORIGINALES en coordenadas del submapa. No tocar salvo que se muevan
# a mano en el editor, en cuyo caso hay que releerlas.
ORIGEN = {
    "Ladera_65": (57334, 14120), "Ladera_66": (63714, -26422),
    "Ladera_67": (24829, -31642), "Ladera_68": (65084, -14454),
    "Ladera_71": (59441, -29084), "Ladera_72": (64939, 13777),
    "Ladera_73": (33659, -38206), "Ladera_74": (59943, 12523),
    "Ladera_75": (66330, 3012), "Ladera_76": (44583, 45398),
    "Ladera_77": (58373, -21298), "Ladera_78": (54284, 8791),
    "Ladera_79": (64839, 4964), "Ladera_80": (40018, -27073),
    "Ladera_81": (58611, 11766), "Ladera_82": (62860, 16021),
    "Ladera_83": (46923, -19964), "Ladera_84": (55897, -25450),
    "Ladera_85": (59368, -15940), "Ladera_87": (34901, -38291),
    "Ladera_88": (36237, -36450), "Ladera_89": (29308, -41362),
    "Ladera_91": (62883, 18535),
}


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def dist_a_segmento(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    largo2 = vx * vx + vy * vy
    if largo2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * vx + (py - ay) * vy) / largo2
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + vx * t), py - (ay + vy * t))


def dist_a_red(px, py, red):
    """Distancia al camino mas cercano. Se mide **al segmento**, no al vertice:
    con piezas cada 600-1600 uu, medir solo a los centros dejaria colarse una
    piedra justo entre dos."""
    d = 1e9
    for linea in red:
        for i in range(len(linea) - 1):
            a, b = linea[i], linea[i + 1]
            d = min(d, dist_a_segmento(px, py, a[0], a[1], b[0], b[1]))
    return d


def run():
    volver = sc("get_current_level", {})
    out = {"volver_a": volver}

    # --- 1. la red de caminos DEL MAESTRO, pasada a coordenadas del submapa ---
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    red = []
    for carpeta in CAMINOS:
        pts = []
        for a in sc("get_actors_in_folder", {"folder_path": carpeta, "recursive": True}):
            t = at("get_actor_transform", {"actor": a})
            pts.append((t["location"]["x"] - OFFSET[0], t["location"]["y"] - OFFSET[1]))
        pts.sort()
        if len(pts) >= 2:
            red.append(pts)
        out.setdefault("red", {})[carpeta] = len(pts)

    # --- 2. las piedras y la senda interna, ya en el Jardin ---
    sc("load_level", {"level_path": JARDIN})
    if "Jardin_Sub" not in sc("get_current_level", {}):
        return dict(out, error="no se abrio el Jardin")

    senda = []
    for a in sc("find_actors", {"name": "Senda", "tag": "", "collision_channels": []}):
        if not at("get_label", {"actor": a}).startswith("Senda"):
            continue
        t = at("get_actor_transform", {"actor": a})
        senda.append((t["location"]["x"], t["location"]["y"]))
    senda.sort()
    if len(senda) >= 2:
        red.append(senda)
    out.setdefault("red", {})["Senda (submapa)"] = len(senda)

    movidas, frenadas, quietas = [], [], []
    for a in sc("get_actors_in_folder", {"folder_path": CARPETA, "recursive": False}):
        et = at("get_label", {"actor": a})
        if et not in ORIGEN:
            continue
        t = at("get_actor_transform", {"actor": a})
        b = at("get_actor_bounds", {"actor": a, "only_colliding": False})
        radio = (max(b["max"]["x"] - b["min"]["x"],
                     b["max"]["y"] - b["min"]["y"]) / 2.0) if b["isValid"] else 3000.0
        x0, y0 = float(ORIGEN[et][0]), float(ORIGEN[et][1])
        r0 = math.hypot(x0, y0)
        ux, uy = x0 / r0, y0 / r0
        libre = radio + MARGEN

        # Contraer, y si toca un camino, devolver hacia fuera de 250 en 250.
        # Nunca mas lejos de donde estaba: si ni en su sitio original despeja,
        # se la deja donde nacio y se avisa.
        r = r0 * FACTOR
        while r < r0 and dist_a_red(ux * r, uy * r, red) < libre:
            r += 250.0
        x1, y1 = ux * r, uy * r
        xf = {"location": {"x": x1, "y": y1, "z": t["location"]["z"]},
              "rotation": t["rotation"], "scale": t["scale"]}
        at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
        ficha = {"n": et, "r": [round(r0), round(r)], "a": [round(x1), round(y1)],
                 "holgura": round(dist_a_red(x1, y1, red) - radio)}
        if r >= r0:
            quietas.append(ficha)
        elif r > r0 * FACTOR + 1.0:
            frenadas.append(ficha)
        else:
            movidas.append(ficha)

    out["movidas"] = movidas
    out["frenadas_por_el_camino"] = frenadas
    out["devueltas_a_su_sitio"] = quietas

    ast("save_assets", {"asset_paths": [JARDIN]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": JARDIN})

    peor = None
    for f in movidas + frenadas + quietas:
        if peor is None or f["holgura"] < peor[1]:
            peor = [f["n"], f["holgura"]]
    out["holgura_minima"] = peor

    if volver != sc("get_current_level", {}):
        sc("load_level", {"level_path": volver})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
