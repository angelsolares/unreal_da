import json

# Ajusta la caja `Zona` de los interactuables ya colocados, y de paso comprueba
# que la instancia conserva el canal `Interactable`.
#
# Existe porque `interaccion_colocar.py` filtraba el componente por tipo
# (`"BoxComponent" in refPath`) y en una INSTANCIA de blueprint el refPath lleva
# el NOMBRE del componente, no la clase. El filtro no casaba y el ajuste se
# perdia sin dar error.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
LI = "LI_06_SantuarioMalkuth"

# La caja del blueprint, sin escalar. Todo lo demas se expresa en relacion a esta.
BASE = {"x": 60.0, "y": 60.0, "z": 90.0}

CAJAS = {
    "Interact_Cofre": {"x": 70.0, "y": 70.0, "z": 45.0},
    "Interact_Cassiel": {"x": 50.0, "y": 50.0, "z": 95.0},
}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    # El editor tan pronto tiene abierto el sublevel como el maestro. Si esta el
    # maestro, los actores viven dentro del Level Instance y no se dejan tocar
    # sin abrirlo: "is inside level instance ... which is not in edit mode".
    sc = lambda t, a: call("editor_toolset.toolsets.scene.SceneTools." + t, a)
    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == LI:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + LI}
        sc("edit_level_instance", {"level_instance": li})

    out = {"modo": "sublevel abierto" if directo else "por Level Instance"}
    for nombre, caja in CAJAS.items():
        for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                      {"name": nombre, "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) != nombre:
                continue
            # `set_properties` sobre un struct Vector solo aplica el PRIMER
            # campo: pedir (70,70,45) deja (70,60,90), con y/z en el valor del
            # CDO. Asi que la caja se dimensiona escalando el ACTOR, que aqui no
            # tiene efectos secundarios porque `Malla` va vacia —estos actores
            # son solo volumen— y `RelativeLocation` escala con el padre, o sea
            # que la caja sigue apoyada donde toca.
            esc = {"x": round(caja["x"] / BASE["x"], 4),
                   "y": round(caja["y"] / BASE["y"], 4),
                   "z": round(caja["z"] / BASE["z"], 4)}
            t = at("get_actor_transform", {"actor": a})
            at("set_actor_transform", {"actor": a,
                                       "xform": {"location": t["location"],
                                                 "rotation": t["rotation"],
                                                 "scale": esc},
                                       "worldspace": True})
            for c in at("get_components", {"actor": a}):
                if not c["refPath"].endswith("Zona"):
                    continue
                p = json.loads(ot("get_properties", {"instance": c,
                                                     "properties": ["BoxExtent", "RelativeLocation", "BodyInstance"]}))
                b = p["BoxExtent"]
                out[nombre] = {"escala": esc,
                               "caja_efectiva": [round(b["x"] * esc["x"], 1),
                                                  round(b["y"] * esc["y"], 1),
                                                  round(b["z"] * esc["z"], 1)],
                               "z_efectiva": round(p["RelativeLocation"]["z"] * esc["z"], 1),
                               "canal": p["BodyInstance"]["objectType"],
                               "colision": p["BodyInstance"]["collisionEnabled"]}
            break

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
