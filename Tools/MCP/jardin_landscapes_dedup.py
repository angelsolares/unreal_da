# -*- coding: utf-8 -*-
import json

# El Jardin tenia CUATRO landscapes apilados. Deja uno.
#
# ### QUE SE ENCONTRO
#
# `L_DA_Malkuth_Jardin_Sub` contenia `Landscape_0..3`, en dos parejas exactamente
# superpuestas:
#
#     Landscape_0 "Landscape"  y  Landscape_1 "Landscape2"   en (-30400, -50400)
#     Landscape_2 "Landscape3" y  Landscape_3 "Landscape4"   en (-26650, -53400)
#
# Los cuatro son REALES e independientes: **513 componentes cada uno**, mismo relieve
# (Z de 638, min -40 / max 497,5, rugosidad 48,3, 1.018.081 vertices = 1009^2). No era
# el tool resolviendo al mismo actor: se comprobo por los bounds de cada actor, que se
# piden por referencia y no por nombre.
#
# O sea **2.052 componentes de landscape y ~4 millones de vertices** donde deberia haber
# 513 y un millon. Cuatro superficies de colision apiladas y z-fighting entre las parejas.
#
# ### POR QUE SE QUEDA `Landscape_0`
#
# Los cuatro tienen el MISMO heightmap, asi que da igual cual sobreviva por datos. Se
# eligio por cobertura del contenido del Jardin (1.490 actores):
#
#     posicion A (Landscape_0 / _1) -> cubre 1433
#     posicion B (Landscape_2 / _3) -> cubre 1434
#
# Empate practico --un actor de diferencia--, asi que manda el nombre original.
#
# ### NO SE USA EL CICLO edit/commit DE LA LEVEL INSTANCE
#
# El `_Sub` se abre como nivel normal. El ciclo de la LI ya descarto trabajo en este
# proyecto; ver la nota de traspaso.

SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Jardin_Sub"
CONSERVAR = "Landscape_0"
BORRAR = ("Landscape_1", "Landscape_2", "Landscape_3")


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def landscapes():
    fuera = {}
    for a in sc("find_actors", {"name": "Landscape", "tag": "",
                                "collision_channels": []}):
        corto = a["refPath"].split(".")[-1]
        if "WaterBrush" in corto:
            continue
        fuera[corto] = a
    return fuera


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE corriendo; parar antes"}
    volver = sc("get_current_level", {})
    if volver != SUB:
        sc("load_level", {"level_path": SUB})
    if "Jardin_Sub" not in str(sc("get_current_level", {})):
        return {"error": "no se abrio el submapa del Jardin"}

    antes = landscapes()
    out = {"antes": sorted(antes.keys())}
    if CONSERVAR not in antes:
        return dict(out, error="no esta el que hay que conservar")

    borrados = []
    for n in BORRAR:
        if n in antes:
            sc("remove_from_scene", {"actor": antes[n]})
            borrados.append(n)
    out["borrados"] = borrados

    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": SUB})

    # --- releer del nivel, que el true de save_assets no prueba nada ---
    despues = landscapes()
    out["despues"] = sorted(despues.keys())
    if CONSERVAR in despues:
        a = despues[CONSERVAR]
        b = at("get_actor_bounds", {"actor": a})
        out["superviviente"] = {
            "actor": CONSERVAR,
            "label": at("get_label", {"actor": a}),
            "comps": len(at("get_components", {"actor": a})),
            "altoZ": round(b["max"]["z"] - b["min"]["z"]),
            "x": [round(b["min"]["x"]), round(b["max"]["x"])],
            "y": [round(b["min"]["y"]), round(b["max"]["y"])]}
    if volver != str(sc("get_current_level", {})):
        sc("load_level", {"level_path": volver})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
