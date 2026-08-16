import json

# Pone el cofre ABIERTO justo encima del cerrado, oculto de salida. Al
# interactuar se esconde uno y se ensena el otro.
#
# Son dos actores y no una animacion de tapa porque Tripo genero dos modelos
# distintos: `SK_DA_Baul` cerrado y `SK_DA_Baul_Abierto`. Los dos tienen 1 hueso,
# asi que no hay nada que animar.
#
# Comparte transform EXACTO con el cerrado —misma posicion, mismo yaw, misma
# escala 92—, que es lo unico que hace que el cambiazo no se note. Al final
# compara las cajas de los dos: si el pivote del abierto no cae en el mismo
# sitio, se ve aqui en numeros antes que en pantalla.
#
# El abierto es mas alto (la tapa levantada), asi que la caja NO tiene por que
# coincidir en z_max. Lo que tiene que coincidir es la BASE.

BPI = "/Game/DarkAngels/Environment/Props/SK_DA_Baul_Abierto"

ZONAS = {
    "santuario": {"li": "LI_06_SantuarioMalkuth",
                  "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
                  "cerrado": "Santuario_Cofre", "nuevo": "Santuario_Cofre_Abierto"},
    "mirador": {"li": "LI_03_MiradorSariel",
                "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
                "cerrado": "Mirador_Cofre", "nuevo": "Mirador_Cofre_Abierto"},
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
    for a in find(nombre):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


def caja(a):
    b = at("get_actor_bounds", {"actor": a})
    return {"base_z": round(b["min"]["z"], 1), "alto": round(b["max"]["z"] - b["min"]["z"], 1),
            "centro": [round((b["min"]["x"] + b["max"]["x"]) / 2.0, 1),
                       round((b["min"]["y"] + b["max"]["y"]) / 2.0, 1)],
            "ancho": [round(b["max"]["x"] - b["min"]["x"], 1),
                      round(b["max"]["y"] - b["min"]["y"], 1)]}


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    z = ZONAS[CUAL]
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

    out = {"zona": CUAL, "modo": "sublevel abierto" if directo else "por Level Instance"}

    cerrado = en_el_asset(z["cerrado"], z["asset"])
    if cerrado is None:
        return {"error": "no se encontro " + z["cerrado"]}
    t = at("get_actor_transform", {"actor": cerrado})

    nuevo = en_el_asset(z["nuevo"], z["asset"])
    if nuevo is None:
        nuevo = sc("add_to_scene_from_asset", {
            "asset_path": BPI, "name": z["nuevo"],
            "xform": {"location": t["location"], "rotation": t["rotation"], "scale": t["scale"]}})
        at("set_label", {"actor": nuevo, "label": z["nuevo"]})
        out["creado"] = True
    else:
        # set_actor_transform resetea escala y rotacion si no se le pasan las tres.
        at("set_actor_transform", {"actor": nuevo, "xform": t, "worldspace": True})
        out["creado"] = False

    # Arranca invisible: solo aparece al abrir.
    ot("set_properties", {"instance": nuevo, "values": json.dumps({"bHidden": True})})

    out["cerrado"] = caja(cerrado)
    out["abierto"] = caja(nuevo)
    out["desfase_base"] = round(out["abierto"]["base_z"] - out["cerrado"]["base_z"], 1)
    out["oculto"] = json.loads(ot("get_properties", {"instance": nuevo, "properties": ["bHidden"]}))["bHidden"]

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": z["asset"]})
    return out
