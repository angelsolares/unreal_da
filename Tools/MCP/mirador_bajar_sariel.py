import json

# Baja a Sariel de su pedestal, quita el pedestal y lo pone junto a la llave.
#
# Lo que habia: `Mirador_EstatuaBase` (200 x 200 x 150, de z=318 a 468) con
# `NPC_Sariel` encima, a 468. Por eso parecia mucho mas alto que el jugador:
# eran los 150 uu del pedestal, no la escala. Medido, Sariel son 180 y el
# jugador 170.
#
# La silueta vieja `Mirador_Estatua_Sariel` esta en el mismo punto pero ya
# estaba oculta, asi que al quitar la base no queda nada flotando. No se toca.
#
# El suelo del mirador esta a z=318 en toda esa zona (trazas en cinco puntos).
#
# DOS PRECAUCIONES QUE COSTARON UN PASE DE TRABAJO:
#   - **Con PIE corriendo no se toca nada.** find_actors devuelve entonces los
#     actores del mundo de PIE y todo se pierde al parar.
#   - **Se filtra por la ruta del ASSET**, no por el nombre del sublevel: con el
#     LI en edicion conviven la copia instanciada en `/Temp/...` y la real en
#     `/Game/...`, y tocar la de `/Temp` ni siquiera marca el paquete sucio.
# Al final se comprueba `is_dirty`: si sale False, no se ha cambiado nada de
# verdad y no vale la pena commitear.

ETIQUETA = "LI_03_MiradorSariel"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"

# La llave esta en (-16000, -23300) con la cara del plinto en 408. Sariel va al
# lado y un poco detras, de pie en la tarima, mirando por donde llega el jugador.
CAMBIOS = [
    ("NPC_Sariel", {"x": -16150.0, "y": -23180.0, "z": 322.0}),
    ("Mirador_Luz_Estatua", {"x": -16150.0, "y": -23120.0, "z": 560.0}),
]
QUITAR = "Mirador_EstatuaBase"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def en_el_asset(nombre):
    """El actor real, no la copia instanciada en /Temp."""
    for a in find(nombre):
        if label(a) == nombre and a["refPath"].startswith(ASSET):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    li = None
    for a in find("LI_"):
        if label(a) == ETIQUETA:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + ETIQUETA}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    out = {}
    base = en_el_asset(QUITAR)
    out["base_borrada"] = (base is not None and
                            call("editor_toolset.toolsets.scene.SceneTools.remove_from_scene",
                                 {"actor": base}))

    for nombre, destino in CAMBIOS:
        a = en_el_asset(nombre)
        if a is None:
            out[nombre] = "no encontrado en el asset"
            continue
        t = call("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": a})
        # set_actor_transform resetea escala y rotacion si no se le pasan las tres.
        call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
            "actor": a,
            "xform": {"location": destino, "rotation": t["rotation"], "scale": t["scale"]},
            "worldspace": True})
        b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": a})
        out[nombre] = {"xyz": [round(destino["x"]), round(destino["y"]), round(destino["z"])],
                        "base_z": round(b["min"]["z"], 1)}

    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
