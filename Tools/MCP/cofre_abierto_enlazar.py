import json

# Enlaza cada interactuable con su pareja de mallas: que actor esconder y cual
# ensenar al interactuar. Se hace por instancia, no en el blueprint, porque cada
# cofre tiene sus dos actores.
#
# Las variables `Cerrado` y `Abierto` se quedan vacias en los interactuables que
# no cambian de aspecto (la llave, los NPC): el grafo las salta con un `IsValid`.

ZONAS = {
    "santuario": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "enlaces": [("Interact_Cofre", "Santuario_Cofre", "Santuario_Cofre_Abierto")],
    },
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "enlaces": [("Interact_CofreMirador", "Mirador_Cofre", "Mirador_Cofre_Abierto")],
    },
}

CUAL = "mirador"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def en_el_asset(nombre, asset):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    z = ZONAS[CUAL]
    directo = sc("get_current_level", {}).startswith(z["asset"])
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == z["li"]:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + z["li"]}
        sc("edit_level_instance", {"level_instance": li})

    out = {"zona": CUAL, "enlaces": []}
    for interactuable, cerrado, abierto in z["enlaces"]:
        i = en_el_asset(interactuable, z["asset"])
        c = en_el_asset(cerrado, z["asset"])
        a = en_el_asset(abierto, z["asset"])
        if i is None or c is None or a is None:
            out["enlaces"].append({interactuable: "falta alguno: %s=%s %s=%s %s=%s" % (
                interactuable, i is not None, cerrado, c is not None, abierto, a is not None)})
            continue
        # Un campo por llamada, por si el setter de structs vuelve a hacer de las suyas.
        ot("set_properties", {"instance": i, "values": json.dumps({"Cerrado": {"refPath": c["refPath"]}})})
        ot("set_properties", {"instance": i, "values": json.dumps({"Abierto": {"refPath": a["refPath"]}})})
        leido = json.loads(ot("get_properties", {"instance": i, "properties": ["Cerrado", "Abierto", "Verbo"]}))
        out["enlaces"].append({interactuable: {
            "Cerrado": str(leido["Cerrado"]).split(".")[-1],
            "Abierto": str(leido["Abierto"]).split(".")[-1],
            "Verbo": leido["Verbo"]}})

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": z["asset"]})
    return out
