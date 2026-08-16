import json

# Cuelga las alas de la espalda de Sariel como actor aparte pegado a un socket.
#
# POR QUE UN SOCKET Y NO SOLO COLOCARLAS AL LADO: Sariel se mueve. Tiene su idle
# en bucle y su animacion de hablar, las dos moviendo la columna. Un actor
# suelto en el sitio correcto se quedaria clavado mientras el se balancea. Pegado
# a `spine_05` —el alto de la espalda, entre los omoplatos— las alas van con el.
#
# ESCALAS, QUE AQUI SE MULTIPLICAN: las alas salen de Tripo midiendo ~1 unidad
# (medias 0,49 x 0,22 x 0,48). Y al colgarlas de un socket heredan la escala del
# actor padre, que en Sariel es 1,829. O sea que la escala final es
# `la que se le ponga` x 1,829, y hay que dividir el objetivo entre eso.
#
# No se acierta a la primera: este script COLOCA Y MIDE, y con los numeros que
# devuelve se corrigen `OFRECIDO`, `ALTURA` y `ENVERGADURA` y se relanza.

MALLA_SARIEL = "/Game/DarkAngels/Characters/NPCs/SK_DA_Sariel.SK_DA_Sariel"
MALLA_ALAS = "/Game/DarkAngels/Characters/NPCs/SK_DA_Alas_Sariel"

ETIQUETA = "LI_03_MiradorSariel"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"

HUESO = "spine_05"
SOCKET = "Alas"
ACTOR = "Sariel_Alas"

ENVERGADURA = 230.0     # ancho total que se quiere, en unidades de mundo
ANCHO_MALLA = 0.98      # lo que mide la malla en X a escala 1


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def sm(t, a):
    return call("editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools." + t, a)


def en_el_asset(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(ASSET):
            return a
    return None


def caja(a):
    b = at("get_actor_bounds", {"actor": a})
    return {"centro": [round((b["min"][k] + b["max"][k]) / 2.0, 1) for k in ("x", "y", "z")],
            "tamano": [round(b["max"][k] - b["min"][k], 1) for k in ("x", "y", "z")],
            "z": [round(b["min"]["z"], 1), round(b["max"]["z"], 1)]}


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    out = {}

    # --- el socket, en el asset de malla (no depende del nivel) ---
    if SOCKET not in sm("get_socket_names", {"mesh": {"refPath": MALLA_SARIEL}}):
        sm("add_socket", {"mesh": {"refPath": MALLA_SARIEL}, "socket_name": SOCKET, "bone_name": HUESO})
    out["socket"] = {"nombre": SOCKET,
                     "hueso": sm("get_socket_bone", {"mesh": {"refPath": MALLA_SARIEL}, "socket_name": SOCKET})}
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [MALLA_SARIEL.split(".")[0]]})

    # --- el nivel ---
    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == ETIQUETA:
                li = a
                break
        if li is None:
            return {"error": "no encontrado " + ETIQUETA}
        sc("edit_level_instance", {"level_instance": li})

    sariel = en_el_asset("NPC_Sariel")
    if sariel is None:
        return {"error": "no se encontro NPC_Sariel"}
    t_sariel = at("get_actor_transform", {"actor": sariel})
    escala_padre = t_sariel["scale"]["x"]
    escala = round(ENVERGADURA / ANCHO_MALLA / escala_padre, 2)

    alas = en_el_asset(ACTOR)
    if alas is None:
        alas = sc("add_to_scene_from_asset", {
            "asset_path": MALLA_ALAS, "name": ACTOR,
            "xform": {"location": t_sariel["location"],
                      "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                      "scale": {"x": escala, "y": escala, "z": escala}}})
        at("set_label", {"actor": alas, "label": ACTOR})
        out["creado"] = True
    else:
        out["creado"] = False

    # --- engancharlas al socket ---
    comp_sariel = None
    for c in at("get_components", {"actor": sariel}):
        if "SkeletalMeshComponent" in c["refPath"] or c["refPath"].endswith("SkeletalMeshComponent0"):
            comp_sariel = c
    raiz_alas = at("get_root_component", {"actor": alas})
    out["padre"] = str(comp_sariel["refPath"]).split(":")[-1] if comp_sariel else "no encontrado"
    out["hijo"] = str(raiz_alas["refPath"]).split(":")[-1]

    if comp_sariel is not None:
        at("set_parent_component", {"component": raiz_alas, "parent": comp_sariel})
        ot("set_properties", {"instance": raiz_alas,
                              "values": json.dumps({"AttachSocketName": SOCKET})})

    out["escala_padre"] = escala_padre
    out["escala_alas"] = escala
    out["sariel"] = caja(sariel)
    out["alas"] = caja(alas)
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
