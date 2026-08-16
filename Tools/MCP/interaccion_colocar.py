import json

# Marca props como interactuables colocandoles encima un `BP_DA_Interactuable`.
#
# POR QUE ENCIMA Y NO EN LUGAR DE: el prop sigue siendo el que era —malla,
# material y, en los NPC, la animacion idle en bucle—, y el actor nuevo solo
# aporta la caja con ObjectType `Interactable` y la interfaz `I_IsInteractable`.
# Sustituirlos obligaria a rehacer la escala (el cofre va a 92) y a volver a
# montar el `AnimationSingleNode` de cada NPC, con todo lo que eso puede romper.
# Asi ademas marcar algo nuevo como interactuable es soltarle uno encima.
#
# La caja es el BLANCO al que apunta la traza de capsula de DCS, no un radio de
# proximidad: la distancia la pone el personaje. Por eso se dimensiona para
# envolver al prop, no para "llegar" hasta el jugador.
#
# UN LEVEL INSTANCE POR PASADA: encadenar ciclos edit/commit sobre el mismo LI
# acaba bloqueando su .umap con el Error Code 32.

BPI = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable"

ZONAS = {
    "santuario": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        # nombre nuevo, prop de referencia, verbo, medias-aristas de la caja
        "props": [
            ("Interact_Cofre", "Santuario_Cofre", "Abrir", {"x": 70.0, "y": 70.0, "z": 45.0}),
            ("Interact_Cassiel", "NPC_Cassiel", "Hablar", {"x": 50.0, "y": 50.0, "z": 95.0}),
        ],
    },
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "props": [
            ("Interact_Llave", "Mirador_Llave", "Recoger", {"x": 45.0, "y": 45.0, "z": 45.0}),
            ("Interact_Sariel", "NPC_Sariel", "Hablar", {"x": 50.0, "y": 50.0, "z": 95.0}),
        ],
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


def find(nombre):
    return sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []})


def en_el_asset(nombre, asset):
    """El actor real del sublevel, no la copia instanciada en /Temp."""
    for a in find(nombre):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    z = ZONAS[CUAL]

    # Dos escenarios. Si el editor tiene abierto el propio sublevel, se escribe
    # en el directamente y no hay ciclo edit/commit que valga. Si esta el
    # maestro, hay que abrir el Level Instance.
    actual = sc("get_current_level", {})
    directo = actual.startswith(z["asset"])
    li = None
    if not directo:
        for a in find("LI_"):
            if at("get_label", {"actor": a}) == z["li"]:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + z["li"] + "; nivel actual: " + actual}
        sc("edit_level_instance", {"level_instance": li})

    out = {"zona": CUAL, "modo": "sublevel abierto" if directo else "por Level Instance",
           "puestos": []}
    for nuevo, referencia, verbo, caja in z["props"]:
        if en_el_asset(nuevo, z["asset"]) is not None:
            out["puestos"].append({nuevo: "ya existia, saltado"})
            continue

        prop = en_el_asset(referencia, z["asset"])
        if prop is None:
            out["puestos"].append({nuevo: "no se encontro el prop " + referencia})
            continue

        b = at("get_actor_bounds", {"actor": prop})
        centro = {"x": round((b["min"]["x"] + b["max"]["x"]) / 2.0, 1),
                  "y": round((b["min"]["y"] + b["max"]["y"]) / 2.0, 1),
                  "z": round(b["min"]["z"], 1)}

        actor = sc("add_to_scene_from_asset", {
            "asset_path": BPI, "name": nuevo,
            "xform": {"location": centro,
                      "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                      "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}})
        at("set_label", {"actor": actor, "label": nuevo})
        ot("set_properties", {"instance": actor, "values": json.dumps({"Verbo": verbo})})

        # Se filtra por NOMBRE de componente, no por tipo: en una instancia de
        # blueprint el refPath lleva el nombre (`Zona`), no la clase, asi que un
        # filtro `"BoxComponent" in refPath` no casa nunca y el ajuste se pierde
        # en silencio.
        for c in at("get_components", {"actor": actor}):
            if not c["refPath"].endswith("Zona"):
                continue
            ot("set_properties", {"instance": c, "values": json.dumps({
                "BoxExtent": caja,
                "RelativeLocation": {"x": 0.0, "y": 0.0, "z": caja["z"]}})})

        out["puestos"].append({nuevo: {"verbo": verbo, "sobre": referencia,
                                        "xyz": [centro["x"], centro["y"], centro["z"]],
                                        "alto_prop": round(b["max"]["z"] - b["min"]["z"], 1)}})

    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": z["asset"]})
    return out
