import json

# Navegacion para la camara de Gabriel: sin `NavMeshBoundsVolume` no hay malla de
# navegacion, y sin ella el `MoveTo` de los Behaviour Trees no va a ningun lado.
# Es decir: el Giant se queda plantado en su sitio y no te persigue.
#
# **NO HAY NINGUNA EN TODO EL PROYECTO.** Se comprobo mapa por mapa buscando
# `NavMeshBoundsVolume` en el binario del Master y de los doce `_Sub`: cero. Asi
# que esto vale igual para los enemigos del Claro cuando toque.
#
# EL VOLUMEN VA EN EL MASTER, no dentro del `_Sub` de la camara. La geometria de
# un Level Instance se funde en el mundo, asi que la malla se construye sobre
# ella igual, y de paso nos ahorramos un ciclo de edit/commit de la LI.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
ETIQUETA = "Nav_GabrielC3"
SUELO = "GC3_Piso"

# El volumen por defecto mide 200x200x200, asi que la escala es la medida que se
# quiere entre 200. Se le da aire de sobra por arriba: la malla solo se genera
# donde hay suelo, pero si el volumen no llega al techo no cubre los escalones.
LADO_BASE = 200.0
MARGEN = 600.0     # cuanto se pasa del suelo por cada lado
ALTO = 1500.0


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    # La huella de la camara, medida del suelo que ya esta puesto.
    piso = None
    for a in sc("find_actors", {"name": SUELO, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == SUELO:
            piso = a
            break
    if piso is None:
        return {"error": "no encuentro " + SUELO}
    b = at("get_actor_bounds", {"actor": piso})

    ancho = (b["max"]["x"] - b["min"]["x"]) + MARGEN * 2
    fondo = (b["max"]["y"] - b["min"]["y"]) + MARGEN * 2
    centro = {"x": (b["max"]["x"] + b["min"]["x"]) / 2.0,
              "y": (b["max"]["y"] + b["min"]["y"]) / 2.0,
              "z": b["min"]["z"] + ALTO / 2.0 - 200.0}
    xform = {"location": centro,
             "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
             "scale": {"x": ancho / LADO_BASE, "y": fondo / LADO_BASE,
                       "z": ALTO / LADO_BASE}}

    vol = None
    for a in sc("find_actors", {"name": ETIQUETA, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == ETIQUETA:
            vol = a
            break
    if vol is None:
        vol = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": "/Script/NavigationSystem.NavMeshBoundsVolume"},
            "name": ETIQUETA, "xform": xform, "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": vol, "label": ETIQUETA})
        estado = "creado"
    else:
        estado = "ya estaba"
    # `set_actor_transform` resetea escala y rotacion si no se le pasan las tres.
    at("set_actor_transform", {"actor": vol, "worldspace": True, "xform": xform})

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [MAESTRO]})
    t = at("get_actor_transform", {"actor": vol})
    bv = at("get_actor_bounds", {"actor": vol})
    return {"estado": estado,
            "piso": {"min": [round(b["min"][k]) for k in ("x", "y", "z")],
                     "max": [round(b["max"][k]) for k in ("x", "y", "z")]},
            "volumen": {"pos": [round(t["location"][k]) for k in ("x", "y", "z")],
                        "esc": [round(t["scale"][k], 2) for k in ("x", "y", "z")],
                        "min": [round(bv["min"][k]) for k in ("x", "y", "z")],
                        "max": [round(bv["max"][k]) for k in ("x", "y", "z")]},
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": MAESTRO})}
