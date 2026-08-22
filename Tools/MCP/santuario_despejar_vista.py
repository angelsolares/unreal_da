# -*- coding: utf-8 -*-
import json

# `SM_Arbol_0` tapaba el Santuario desde LOS 31 puntos del pasillo `Conn_CS_Path`.
# Un solo actor de 2.197 uu clavado en la linea de vision. Lo aparta y **mide** el
# resultado.
#
# ### POR QUE 2.500 uu BASTAN
#
# Todas las visuales convergen en el Santuario, asi que cerca del destino el haz es
# estrechisimo: el pasillo abarca ~1.100 uu a 50.000 de distancia, o sea ~33 uu de haz
# a los 1.500 uu donde esta el arbol. Lo que obliga a moverlo no es el haz sino el radio
# del propio arbol (~950 uu).
#
# ### DOS TRAMPAS QUE COSTARON TIEMPO
#
# 1. **El arbol vive dentro de `LI_06_SantuarioMalkuth`.** Desde el maestro,
#    `set_actor_transform` falla con "not in edit mode". Se edita abriendo
#    `L_DA_Malkuth_Santuario_Sub` como nivel normal --nunca por el ciclo edit/commit de
#    la LI, que ya descarto trabajo aqui--. El delta es una traslacion pura, asi que el
#    mismo numero vale en submapa y en mundo.
#
# 2. **`find_actors` filtra por ETIQUETA, pero el refPath lleva el nombre de OBJETO.**
#    Estas piezas se llaman `StaticMeshActor_203` y se etiquetan `Conn_CS_Path_0`.
#    Comparar el refPath contra la etiqueta devuelve cero. Y barrer los 6.464 actores
#    pidiendo `get_label` tarda mas de 10 minutos: hay que filtrar por nombre primero.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
ARBOL = "SM_Arbol_0"
SANTUARIO = (44000.0, 48000.0)
OJO, ALTURA = 180.0, 1000.0
DELTA = (-2500.0, 0.0)


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def buscar(prefijo, exacto=None, paquete=None):
    """find_actors filtra por etiqueta; devuelve {etiqueta: actor}."""
    fuera = {}
    for a in sc("find_actors", {"name": prefijo, "tag": "", "collision_channels": []}):
        rp = a["refPath"]
        if "UEDPIE" in rp:
            continue
        if paquete is not None and paquete not in rp:
            continue
        try:
            e = at("get_label", {"actor": a})
        except Exception:
            continue
        if exacto is None or e == exacto:
            fuera[e] = a
    return fuera


def camino():
    piezas = buscar("Conn_CS_Path_", paquete="L_DA_Malkuth_Master")
    orden = sorted((e for e in piezas if e.startswith("Conn_CS_Path_")),
                   key=lambda e: int(e.rsplit("_", 1)[1]))
    pts = []
    for e in orden:
        L = at("get_actor_transform", {"actor": piezas[e]})["location"]
        pts.append((L["x"], L["y"], L["z"]))
    return pts


def mide(pts):
    res = call("VibeUE.LandscapeService.BatchLineTrace", {
        "startLocations": [{"x": p[0], "y": p[1], "z": p[2] + OJO} for p in pts],
        "endLocations": [{"x": SANTUARIO[0], "y": SANTUARIO[1], "z": ALTURA}
                         for _ in pts]})
    libres, culpables = 0, {}
    for r in res:
        d = dict(r)
        if not d["bHit"]:
            libres += 1
        else:
            n = str(d["actorName"])
            culpables[n] = culpables.get(n, 0) + 1
    return libres, sorted(culpables.items(), key=lambda x: -x[1])[:4]


def run():
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {}
    pts = camino()
    out["puntos"] = len(pts)
    if not pts:
        return dict(out, error="no aparece Conn_CS_Path_*")
    libres, culp = mide(pts)
    out["antes"] = {"ve": libres, "de": len(pts), "tapan": culp}

    sc("load_level", {"level_path": SUB})
    if "Santuario_Sub" not in str(sc("get_current_level", {})):
        return dict(out, error="no se abrio el submapa")
    d = buscar("SM_Arbol", exacto=ARBOL, paquete="Santuario_Sub")
    if ARBOL not in d:
        sc("load_level", {"level_path": MAESTRO})
        return dict(out, error="no aparece " + ARBOL)
    a = d[ARBOL]
    t0 = at("get_actor_transform", {"actor": a})
    out["arbol_antes"] = [round(t0["location"][k]) for k in ("x", "y", "z")]
    at("set_actor_transform", {"actor": a, "worldspace": True, "xform": {
        "location": {"x": t0["location"]["x"] + DELTA[0],
                     "y": t0["location"]["y"] + DELTA[1],
                     "z": t0["location"]["z"]},
        "rotation": t0["rotation"], "scale": t0["scale"]}})
    ast("save_assets", {"asset_paths": [SUB]})
    out["sub_sucio"] = ast("is_dirty", {"asset_path": SUB})
    t1 = at("get_actor_transform", {"actor": buscar("SM_Arbol", exacto=ARBOL, paquete="Santuario_Sub")[ARBOL]})
    out["arbol_despues"] = [round(t1["location"][k]) for k in ("x", "y", "z")]
    out["escala"] = [round(t1["scale"][k], 2) for k in ("x", "y", "z")]

    sc("load_level", {"level_path": MAESTRO})
    libres2, culp2 = mide(camino())
    out["despues"] = {"ve": libres2, "de": len(pts), "tapan": culp2}
    return out
