# -*- coding: utf-8 -*-
import json

# Devuelve el `SkyDomeMesh` a la panoramica original, la de `M_DA_Panorama360`.
#
# NO basta con poner el material viejo en el override. Antes de tocar nada, el
# material **venia del slot de la malla**, no de un override del componente: el
# panel de Details lo mostraba como "Slot DefaultMaterial". Si se deja un override
# apuntando al mismo material el resultado se ve igual, pero el actor queda con una
# sobreescritura que antes no tenia, y eso es un rastro que confunde a quien lo
# mire dentro de un mes.
#
# Asi que se comprueba cual es el material por defecto de la malla:
#   - si ya es `M_DA_Panorama360`, se **vacia** el override y queda como nacio;
#   - si no lo es, se pone el override explicito, que es lo unico que funcionaria.
#
# Las dos texturas de angeles y el material `M_DA_Panorama360_Angeles` **se quedan
# donde estan**. No estorban a nada --nadie los referencia ya-- y volver a probarlos
# es un desplegable. Borrarlos es una decision aparte.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
ORIGINAL = "/Game/DarkAngels/Materials/Malkuth/M_DA_Panorama360.M_DA_Panorama360"


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


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes"}
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {}

    domo = None
    for a in sc("find_actors", {"name": "SkyDomeMesh", "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == "SkyDomeMesh":
            domo = a
    if domo is None:
        return {"error": "no aparece SkyDomeMesh"}
    comp = at("get_components", {"actor": domo})[0]

    out["antes"] = json.loads(ot("get_properties", {"instance": comp,
                                 "properties": ["OverrideMaterials"]}))["OverrideMaterials"]

    # De donde salia el material: del slot de la malla o del override?
    malla = json.loads(ot("get_properties", {"instance": comp,
                          "properties": ["StaticMesh"]}))["StaticMesh"]
    out["malla"] = str(malla)
    porDefecto = json.loads(ot("get_properties", {"instance": malla,
                               "properties": ["StaticMaterials"]}))["StaticMaterials"]
    out["materiales_de_la_malla"] = str(porDefecto)
    slotEsElOriginal = "M_DA_Panorama360." in str(porDefecto) and \
        "M_DA_Panorama360_Angeles" not in str(porDefecto)

    if slotEsElOriginal:
        ot("set_properties", {"instance": comp,
                              "values": json.dumps({"OverrideMaterials": []})})
        out["via"] = "override vaciado; vuelve a mandar el slot de la malla"
    else:
        ot("set_properties", {"instance": comp, "values": json.dumps(
            {"OverrideMaterials": [{"refPath": ORIGINAL}]})})
        out["via"] = "override explicito al material original"

    ast("save_assets", {"asset_paths": [MAESTRO]})

    # --- releer del actor, que el `true` solo dice "acepte la llamada" ---
    out["despues"] = json.loads(ot("get_properties", {"instance": comp,
                                   "properties": ["OverrideMaterials"]}))["OverrideMaterials"]
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})
    return out
