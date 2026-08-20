# -*- coding: utf-8 -*-
import json
import math

# Dibuja los dos tramos que le faltan al ramal del Mirador.
#
# `Conexiones/JardinMirador` son 12 piezas que **no tocan nada por ninguno de sus
# dos extremos**: mueren a ~2.400 uu de la carretera `JardinClaro` por el sur y a
# ~2.200 de la escalinata del promontorio por el norte. `probe_camino.py` dice que
# los dos huecos se andan --terreno llano--, pero el jugador no tiene ninguna
# pista de que ahi se gira: son tierra pelada. De ahi el "no veo camino".
#
# ### LA RECETA SALE DE LEER UNA PIEZA, NO DE LAS NOTAS
#
# Todas las piezas de los nueve corredores son iguales:
# `SM_MGK_Path_Straight_600`, escala **(1.3, 3, 1)**, sin materiales sobreescritos.
# Lo unico que cambia es el yaw, y la regla no es obvia: **yaw = atan2(dy,dx) + 90**,
# porque la malla es larga en su Y local (por eso la escala 3 va en Y). Comprobado
# en los dos corredores: `JardinMirador` va a 93,2 grados y sus piezas a −176,8;
# `JardinClaro` a 32,8 y las suyas a 122,8.
#
# ### LA Z ES FIJA A −38, COMO LAS OTRAS 139
#
# Intente que siguiera el terreno y fue un error que costo dos pasadas. El terreno
# de los dos huecos es **plano a −40**, medido con trazas desplazadas 700 uu a
# ambos lados de la ruta; las piezas existentes estan a −38, o sea 2 por encima.
# No hay nada que seguir.
#
# **Por que salio mal**: trazar el suelo EN la ruta no mide el terreno, mide lo que
# haya encima. En los extremos chocaba con las piezas de senda que ya estaban
# (superficie a −26) y en el norte con la escalinata del promontorio; y como las
# piezas nuevas miden 1800 y van cada 1100, cada una tapaba a la siguiente y
# salieron las seis escalonadas, +24 uu cada una, flotando. Para medir terreno hay
# que apartarse de lo construido.
#
# El tramo N **para antes de la escalinata**: a partir de y ≈ −24830 el suelo ya
# sube (18, y 157 a −24400). Termina en −25100, que sigue siendo plano.
#
# ### POR QUE SE DIBUJA IGUAL QUE LA CARRETERA PRINCIPAL
#
# Misma pieza y misma escala, no un sendero mas humilde. El Mirador **dejo de ser
# opcional** en cuanto la llave dejo de ser un atajo: las tres salidas de Sariel
# son ahora la unica forma de pasar de El Claro. Un ramal que se lea como desvio
# menor contaria una mentira. Si se quiere lo contrario, es bajar `ESCALA`.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
MALLA = "/Game/Blender/SM_MGK_Path_Straight_600.SM_MGK_Path_Straight_600"
CARPETA = "Conexiones/JardinMirador"
ESCALA = {"x": 1.3, "y": 3.0, "z": 1.0}
Z_SENDA = -38.0        # la misma que las otras 139 piezas de `Conexiones`
SEPARACION = 1600.0    # la pieza mide 600 x 3 = 1800, asi que se solapan un poco

# (prefijo, desde, hasta)
#   S: de la carretera `JardinClaro` --pieza `Conn_JC_Path` real-- al arranque del ramal
#   N: del final del ramal al pie de `Mirador_Escalera_0`
TRAMOS = [
    ("S", (-13193.0, -51867.0), (-14700.0, -50000.0)),
    ("N", (-16000.0, -27000.0), (-16000.0, -25100.0)),
]


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


def suelo(x, y):
    """Desde 600 y no desde mas arriba: asi no caza salientes por encima."""
    d = sc("trace_world", {"start": {"x": x, "y": y, "z": 600.0},
                           "end": {"x": x, "y": y, "z": -800.0}})
    return None if d is None else 600.0 - d


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {"tramos": {}}

    # --- 0. borrar lo de pasadas anteriores ANTES de medir ---
    #
    # No es limpieza cosmetica: si las piezas siguen puestas, la traza de suelo
    # **choca con ellas** y devuelve su superficie en vez del terreno. Y como cada
    # pieza mide 1800 y van a 1100-1200, cada una tapa a la siguiente: la primera
    # pasada salio con las seis escalonadas, +24 uu cada una, flotando sobre la
    # anterior. Es la misma trampa que ya enterro a los angeles de El Claro.
    borradas = 0
    for prefijo, _, _ in TRAMOS:
        for i in range(40):
            a = busca("Conn_JardinMirador_%s%d" % (prefijo, i))
            if a is None:
                continue
            sc("remove_from_scene", {"actor": a})
            borradas += 1
    out["borradas_antes_de_medir"] = borradas

    # --- 1. colocar ---
    for prefijo, (x0, y0), (x1, y1) in TRAMOS:
        dx, dy = x1 - x0, y1 - y0
        largo = math.hypot(dx, dy)
        yaw = math.degrees(math.atan2(dy, dx)) + 90.0
        n = max(1, int(math.ceil(largo / SEPARACION)))
        detalle = []
        for i in range(n + 1):
            t = float(i) / n
            x, y = x0 + dx * t, y0 + dy * t
            z = Z_SENDA
            etiqueta = "Conn_JardinMirador_%s%d" % (prefijo, i)
            xf = {"location": {"x": x, "y": y, "z": z},
                  "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
                  "scale": ESCALA}
            a = busca(etiqueta)
            if a is None:
                a = sc("add_to_scene_from_class", {
                    "actor_type": {"refPath": "/Script/Engine.StaticMeshActor"},
                    "name": etiqueta, "xform": xf, "parent": None,
                    "snap_to_ground": False})
                at("set_label", {"actor": a, "label": etiqueta})
            # `set_actor_transform` RESETEA escala y rotacion si no se las pasas.
            at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
            sc("set_actor_folder", {"actor": a, "folder_path": CARPETA})
            comp = at("get_components", {"actor": a})[0]
            ot("set_properties", {"instance": comp,
                                  "values": json.dumps({"StaticMesh": {"refPath": MALLA}})})
            detalle.append({"i": i, "loc": [round(x), round(y), z]})
        out["tramos"][prefijo] = {"largo": round(largo), "yaw": round(yaw, 1),
                                  "piezas": n + 1, "detalle": detalle}

    ast("save_assets", {"asset_paths": [MAESTRO]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})

    # --- releer del actor, no del script ---
    comprobado = []
    for prefijo, _, _ in TRAMOS:
        for i in range(20):
            a = busca("Conn_JardinMirador_%s%d" % (prefijo, i))
            if a is None:
                break
            t = at("get_actor_transform", {"actor": a})
            comp = at("get_components", {"actor": a})[0]
            m = json.loads(ot("get_properties", {"instance": comp,
                                                 "properties": ["StaticMesh"]}))
            comprobado.append({
                "n": "%s%d" % (prefijo, i),
                "loc": [round(t["location"][k]) for k in ("x", "y", "z")],
                "yaw": round(t["rotation"]["yaw"], 1),
                "esc": [round(t["scale"][k], 2) for k in ("x", "y", "z")],
                "malla_ok": "SM_MGK_Path_Straight_600" in str(m["StaticMesh"])})
    out["comprobado"] = comprobado
    return out
