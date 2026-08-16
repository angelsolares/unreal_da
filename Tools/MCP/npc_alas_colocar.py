import json

# Coloca en el nivel el actor de alas de un NPC, ya escalado a ojo de buen cubero
# y pegado a su `SkeletalMeshComponent`. El enganche fino al SOCKET va aparte, a
# mano en el Outliner, y el encuadre lo afina despues `npc_alas_ajustar.py`.
#
# Es el paso 4 de la receta; los pasos completos estan en la cabecera de
# `npc_alas_ajustar.py` y en las notas del proyecto.
#
# La escala inicial no importa mucho: `npc_alas_ajustar.py` la recalcula midiendo
# la caja de verdad. Aqui solo se busca que no salga microscopica ni gigante.

NPCS = {
    "sariel": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "npc": "NPC_Sariel", "actor": "Sariel_Alas",
        "malla_alas": "/Game/DarkAngels/Characters/NPCs/SK_DA_Alas_Sariel",
        "ancho_malla": 0.98,   # lo que mide en X a escala 1
        "envergadura": 230.0,
    },
    "cassiel": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "npc": "NPC_Cassiel", "actor": "Cassiel_Alas",
        "malla_alas": "/Game/DarkAngels/Characters/NPCs/SK_DA_Alas_Cassiel",
        # Estas son mas ALTAS que anchas (0,76 x 0,30 x 0,98), al reves que el
        # emblema de Sariel. Con 200 de envergadura salen ~258 de alto.
        "ancho_malla": 0.76,
        "envergadura": 200.0,
    },
}

CUAL = "cassiel"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def en_el_asset(nombre, asset):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    n = NPCS[CUAL]
    directo = sc("get_current_level", {}).startswith(n["asset"])
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == n["li"]:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + n["li"]}
        sc("edit_level_instance", {"level_instance": li})

    npc = en_el_asset(n["npc"], n["asset"])
    if npc is None:
        return {"error": "no se encontro " + n["npc"]}
    t = at("get_actor_transform", {"actor": npc})
    escala_padre = t["scale"]["x"]
    # La escala se hereda del padre al colgarlas, asi que se divide entre ella.
    escala = round(n["envergadura"] / n["ancho_malla"] / escala_padre, 2)

    alas = en_el_asset(n["actor"], n["asset"])
    out = {"npc": CUAL, "creado": alas is None}
    if alas is None:
        alas = sc("add_to_scene_from_asset", {
            "asset_path": n["malla_alas"], "name": n["actor"],
            "xform": {"location": t["location"],
                      "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                      "scale": {"x": escala, "y": escala, "z": escala}}})
        at("set_label", {"actor": alas, "label": n["actor"]})

    # Se cuelgan del componente del NPC. El socket, a mano en el Outliner.
    comp = None
    for c in at("get_components", {"actor": npc}):
        if "SkeletalMeshComponent" in c["refPath"]:
            comp = c
    if comp is not None:
        at("set_parent_component", {"component": at("get_root_component", {"actor": alas}),
                                    "parent": comp})

    b = at("get_actor_bounds", {"actor": alas})
    out["escala"] = escala
    out["caja_alas"] = [round(b["max"][k] - b["min"][k], 1) for k in ("x", "y", "z")]
    out["siguiente"] = "enganchar al socket 'Alas' a mano y lanzar npc_alas_ajustar.py"

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [n["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": n["asset"]})
    return out
