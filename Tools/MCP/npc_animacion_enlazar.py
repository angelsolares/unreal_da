import json

# Enlaza un interactuable con el NPC al que tiene que animar y con sus dos
# animaciones: la de hablar mientras dura la interaccion, y la de reposo a la
# que vuelve al salir.
#
# Las animaciones son POR ESQUELETO, no compartidas: cada NPC de Tripo trae el
# suyo aunque los dos salgan de la misma jerarquia de AccuRig. `A_DA_Hablar_Sariel`
# apunta a `SK_DA_Sariel_Skeleton` y no vale para Cassiel.
#
# Del FBX de AccuRig salen SIEMPRE dos takes, y hay que quedarse con el gordo:
# el de ~100 KB es el cuerpo, el de ~4 KB es la pista de expresion facial.
# Aqui: `talk_NPC24-wave-out-engage-explain` (97 KB, renombrada a
# `A_DA_Hablar_Sariel`) frente a `talk_NPC0_Open_A_UE5` (4 KB, sin usar).

ANIM = "/Game/DarkAngels/Characters/NPCs/Anim/"

ZONAS = {
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "enlaces": [("Interact_Sariel", "NPC_Sariel",
                     "A_DA_Hablar_Sariel", "A_DA_Idle_Sariel")],
    },
    "santuario": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "enlaces": [("Interact_Cassiel", "NPC_Cassiel",
                     "A_DA_Hablar_Cassiel", "A_DA_Idle_Cassiel")],
    },
}

CUAL = "santuario"


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
    if not z["enlaces"]:
        return {"zona": CUAL, "nada_que_hacer": True}

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
    for interactuable, npc, hablar, reposo in z["enlaces"]:
        i = en_el_asset(interactuable, z["asset"])
        n = en_el_asset(npc, z["asset"])
        if i is None or n is None:
            out["enlaces"].append({interactuable: "falta %s=%s o %s=%s" % (
                interactuable, i is not None, npc, n is not None)})
            continue
        # Un campo por llamada, que el setter de structs ya nos la jugo antes.
        ot("set_properties", {"instance": i, "values": json.dumps({"Animado": {"refPath": n["refPath"]}})})
        ot("set_properties", {"instance": i, "values": json.dumps(
            {"AnimHablar": {"refPath": ANIM + hablar + "." + hablar}})})
        ot("set_properties", {"instance": i, "values": json.dumps(
            {"AnimReposo": {"refPath": ANIM + reposo + "." + reposo}})})
        leido = json.loads(ot("get_properties", {"instance": i,
                                                 "properties": ["Animado", "AnimHablar", "AnimReposo", "Verbo"]}))
        out["enlaces"].append({interactuable: {k: str(leido[k]).split("/")[-1].rstrip("'}")
                                               for k in leido}})

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": z["asset"]})
    return out
