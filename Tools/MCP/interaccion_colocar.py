import json

# Marca props como interactuables colocandoles encima un `BP_DA_Interactuable`.
#
# POR QUE ENCIMA Y NO EN LUGAR DE: el prop sigue siendo el que era —malla,
# material y, en los NPC, la animacion idle en bucle—, y el actor nuevo solo
# aporta la caja con ObjectType `Interactable` y la interfaz `I_IsInteractable`.
# Sustituirlos obligaria a rehacer la escala (los cofres van a 92) y a volver a
# montar el `AnimationSingleNode` de cada NPC. Asi ademas marcar algo nuevo como
# interactuable es soltarle uno encima.
#
# La caja es el BLANCO al que apunta la traza de capsula de DCS, no un radio de
# proximidad: la distancia la pone el personaje. Por eso se dimensiona a partir
# de las medidas del prop, con un minimo para que no quede un blanco imposible.
#
# DOS TRAMPAS DEL MCP QUE COSTARON UNA PASADA EN EL SANTUARIO:
#   - `set_properties` sobre un struct Vector **solo aplica el primer campo**:
#     pedir BoxExtent (70,70,45) deja (70,60,90), con y/z en el valor del CDO y
#     sin dar error. Por eso la caja se dimensiona **escalando el actor**, que
#     aqui no tiene efectos secundarios porque `Malla` va vacia.
#   - En una INSTANCIA de blueprint el `refPath` del componente lleva su NOMBRE,
#     no su clase: filtrar por `"BoxComponent" in refPath` no casa nunca.
#
# UN LEVEL INSTANCE POR PASADA: encadenar ciclos edit/commit sobre el mismo LI
# acaba bloqueando su .umap con el Error Code 32.

BPI = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable"

# La caja del blueprint sin escalar. Todo se expresa en relacion a ella.
BASE = {"x": 60.0, "y": 60.0, "z": 90.0}
MINIMO = {"x": 40.0, "y": 40.0, "z": 35.0}
HOLGURA = 1.2

ZONAS = {
    "santuario": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "props": [("Interact_Cofre", "Santuario_Cofre", "Abrir"),
                  ("Interact_Cassiel", "NPC_Cassiel", "Hablar")],
    },
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "props": [("Interact_Llave", "Mirador_Llave", "Recoger"),
                  ("Interact_CofreMirador", "Mirador_Cofre", "Abrir"),
                  ("Interact_Sariel", "NPC_Sariel", "Hablar")],
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
    # en el directamente. Si esta el maestro, hay que abrir el Level Instance o
    # los actores no se dejan tocar.
    directo = sc("get_current_level", {}).startswith(z["asset"])
    li = None
    if not directo:
        for a in find("LI_"):
            if at("get_label", {"actor": a}) == z["li"]:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + z["li"]}
        sc("edit_level_instance", {"level_instance": li})

    out = {"zona": CUAL, "modo": "sublevel abierto" if directo else "por Level Instance",
           "puestos": []}

    for nuevo, referencia, verbo in z["props"]:
        if en_el_asset(nuevo, z["asset"]) is not None:
            out["puestos"].append({nuevo: "ya existia, saltado"})
            continue

        prop = en_el_asset(referencia, z["asset"])
        if prop is None:
            out["puestos"].append({nuevo: "no se encontro el prop " + referencia})
            continue

        b = at("get_actor_bounds", {"actor": prop})
        medio = {"x": max(MINIMO["x"], (b["max"]["x"] - b["min"]["x"]) / 2.0 * HOLGURA),
                 "y": max(MINIMO["y"], (b["max"]["y"] - b["min"]["y"]) / 2.0 * HOLGURA),
                 "z": max(MINIMO["z"], (b["max"]["z"] - b["min"]["z"]) / 2.0)}
        base = {"x": round((b["min"]["x"] + b["max"]["x"]) / 2.0, 1),
                "y": round((b["min"]["y"] + b["max"]["y"]) / 2.0, 1),
                "z": round(b["min"]["z"], 1)}
        esc = {"x": round(medio["x"] / BASE["x"], 4),
               "y": round(medio["y"] / BASE["y"], 4),
               "z": round(medio["z"] / BASE["z"], 4)}

        actor = sc("add_to_scene_from_asset", {
            "asset_path": BPI, "name": nuevo,
            "xform": {"location": base,
                      "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                      "scale": esc}})
        at("set_label", {"actor": actor, "label": nuevo})
        ot("set_properties", {"instance": actor, "values": json.dumps({"Verbo": verbo})})

        out["puestos"].append({nuevo: {
            "verbo": verbo, "sobre": referencia,
            "xyz": [base["x"], base["y"], base["z"]],
            "caja": [round(medio["x"], 1), round(medio["y"], 1), round(medio["z"], 1)],
            "alto_prop": round(b["max"]["z"] - b["min"]["z"], 1)}})

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": z["asset"]})
    return out
