# -*- coding: utf-8 -*-
import json
import math

# Cierra el hueco entre la senda del Jardin y el arranque de la carretera al Claro.
#
# ### EL HUECO, MEDIDO
#
# Los 32 actores `Senda_*` del Jardin llegan hasta **(−40380, −60649)**, y la
# carretera `Conexiones/JardinClaro` no empieza hasta **`Conn_JC_Path_0` en
# (−24776, −59333)**. Entre medias hay **15.659 uu sin nada**: es el tramo que
# Angel marco en rojo sobre la vista cenital. El terreno es **plano a −40** de
# punta a punta --comprobado en 13 puntos con trazas desplazadas 900 uu a los dos
# lados-- asi que la recta vale y no hace falta seguir el relieve.
#
# Las dos unicas lecturas raras del perfil eran las de los extremos (18 y −26,7):
# ahi la traza choca con las piezas que ya estan, no con el suelo. Ver
# `mirador_senda.py`, que explica esa trampa con detalle.
#
# ### MISMA RECETA QUE LAS OTRAS 139 PIEZAS
#
# `SM_MGK_Path_Straight_600`, escala (1.3, 3, 1) y **yaw = atan2(dy,dx) + 90**
# porque la malla es larga en su Y local.
#
# La senda del Jardin usa **la misma malla**, pero con escala **(1.15, 1.02, 1)**:
# piezas de 612 en vez de 1800, que es por lo que puede curvar, y cada una con su
# yaw. Aqui se mantiene la escala de la CARRETERA, que es a donde va este tramo;
# la anchura casi no cambia (1.15 frente a 1.3), lo que cambia es el largo.
#
# ### LO QUE ESTO **NO** PONE: LOS SETOS
#
# La carretera `JardinClaro` lleva `Conn_JC_HedgeL_*` y `Conn_JC_HedgeR_*` a los
# lados, y el Jardin tiene los suyos. Este tramo va **solo con la senda**: el
# desfase de los setos existentes no es simetrico ni regular --`HedgeL_0` cae a
# (−386, +84) del centro y `HedgeR_0` a (−83, −387)--, o sea que no salen de una
# formula sino de una colocacion a ojo. Reproducir eso a ciegas quedaria peor que
# no ponerlos. Si se quieren, es una segunda pasada mirando como estan puestos de
# verdad.
#
# ### Y SOBRE HACERLO CON SPLINES DE LANDSCAPE
#
# Se veria mejor --el camino deformaria el terreno en vez de flotar sobre el--
# pero **el MCP no expone ningun toolset de landscape**, asi que crear control
# points y segmentos es trabajo a mano en el editor. Ademas mezclaria dos
# lenguajes: los otros 139 tramos son piezas. Pasar a splines tiene sentido como
# decision para **toda la red**, no para un hueco.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
MALLA = "/Game/Blender/SM_MGK_Path_Straight_600.SM_MGK_Path_Straight_600"
CARPETA = "Conexiones/JardinClaro"
ESCALA = {"x": 1.3, "y": 3.0, "z": 1.0}
SEPARACION = 1600.0

# LA Z NO ES FIJA AQUI, Y ESA ES LA GRACIA. Los dos extremos **no estan a la misma
# cota**: la senda del Jardin va a **z = 6** y la carretera del Claro a **-38**.
# Con una z fija quedaba un escalon de 44 uu justo en la union -- por debajo de
# los 45 que sube un Character, o sea transitable, pero un peldaño feo en mitad
# del camino--. Se interpola: 44 uu de caida repartidos en 15.659, un 0,28% de
# pendiente que no se ve y que borra los dos escalones de golpe.
Z_DESDE = 6.0      # `Senda_39`, la ultima del Jardin
Z_HASTA = -38.0    # `Conn_JC_Path_0` y el resto de la red

DESDE = (-40380.0, -60649.0)   # ultima `Senda_` del Jardin
HASTA = (-24776.0, -59333.0)   # `Conn_JC_Path_0`
PREFIJO = "Conn_JC_Enlace"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {}

    # Borrar antes de colocar: hace el script relanzable y, sobre todo, evita que
    # una pieza vieja quede huerfana si se cambia el trazado.
    borradas = 0
    for i in range(60):
        a = busca("%s_%d" % (PREFIJO, i))
        if a is not None:
            sc("remove_from_scene", {"actor": a})
            borradas += 1
    out["borradas"] = borradas

    dx, dy = HASTA[0] - DESDE[0], HASTA[1] - DESDE[1]
    largo = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx)) + 90.0
    n = max(1, int(math.ceil(largo / SEPARACION)))
    out["largo"] = round(largo)
    out["yaw"] = round(yaw, 1)
    out["piezas"] = n + 1

    for i in range(n + 1):
        t = float(i) / n
        x, y = DESDE[0] + dx * t, DESDE[1] + dy * t
        etiqueta = "%s_%d" % (PREFIJO, i)
        z = Z_DESDE + (Z_HASTA - Z_DESDE) * t
        xf = {"location": {"x": x, "y": y, "z": round(z, 1)},
              "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
              "scale": ESCALA}
        a = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": "/Script/Engine.StaticMeshActor"},
            "name": etiqueta, "xform": xf, "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": a, "label": etiqueta})
        # `set_actor_transform` RESETEA escala y rotacion si no se las pasas.
        at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
        sc("set_actor_folder", {"actor": a, "folder_path": CARPETA})
        comp = at("get_components", {"actor": a})[0]
        ot("set_properties", {"instance": comp,
                              "values": json.dumps({"StaticMesh": {"refPath": MALLA}})})

    ast("save_assets", {"asset_paths": [MAESTRO]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})

    # --- releer del actor, no del script ---
    comprobado = []
    for i in range(n + 1):
        a = busca("%s_%d" % (PREFIJO, i))
        if a is None:
            comprobado.append({"i": i, "falta": True})
            continue
        tr = at("get_actor_transform", {"actor": a})
        comp = at("get_components", {"actor": a})[0]
        m = json.loads(ot("get_properties", {"instance": comp,
                                             "properties": ["StaticMesh"]}))
        comprobado.append({
            "i": i,
            "loc": [round(tr["location"][k]) for k in ("x", "y", "z")],
            "yaw": round(tr["rotation"]["yaw"], 1),
            "esc": [round(tr["scale"][k], 2) for k in ("x", "y", "z")],
            "malla_ok": "SM_MGK_Path_Straight_600" in str(m["StaticMesh"])})
    out["comprobado"] = comprobado
    return out
