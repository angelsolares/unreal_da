import json

# Separa la camara de cada interactuable lo justo para que el objeto quepa
# entero en pantalla.
#
# El tamanio se saca de la caja `Zona`, que ya esta dimensionada con las medidas
# reales del prop. Con FOV 90 la mitad del angulo horizontal es 45 grados, o sea
# tan = 1; en vertical, con 16:9, tan = 1/1,777 = 0,5625. De ahi:
#
#     d_horizontal = ancho / 2
#     d_vertical   = alto * 0,889
#     distancia    = max(de los dos) * MARGEN
#
# Manda casi siempre el vertical, que es el lado corto del encuadre.
#
# `RelativeLocation` se divide por la escala del actor porque el offset se
# multiplica por ella. La altura se deja en 90 —el mismo valor que la caja— que
# escalado cae justo a media altura del objeto.
#
# Se escribe **un campo por llamada**: el setter de structs solo aplica el primero.

BASE = {"x": 60.0, "y": 60.0, "z": 90.0}   # la caja del blueprint sin escalar
MARGEN = 1.25

ZONAS = {
    "santuario": {"li": "LI_06_SantuarioMalkuth",
                  "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"},
    "mirador": {"li": "LI_03_MiradorSariel",
                "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"},
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

    out = {"zona": CUAL, "camaras": []}
    for a in sc("find_actors", {"name": "Interact_", "tag": "", "collision_channels": []}):
        if not a["refPath"].startswith(z["asset"]):
            continue
        etiqueta = at("get_label", {"actor": a})
        if not etiqueta.startswith("Interact_"):
            continue

        esc = at("get_actor_transform", {"actor": a})["scale"]
        ancho = 2.0 * max(BASE["x"] * esc["x"], BASE["y"] * esc["y"])
        alto = 2.0 * BASE["z"] * esc["z"]
        d = max(ancho / 2.0, alto * 0.889) * MARGEN
        relx = round(-d / esc["x"], 1)

        for c in at("get_components", {"actor": a}):
            if not c["refPath"].endswith("Camara"):
                continue
            ot("set_properties", {"instance": c,
                                  "values": json.dumps({"RelativeLocation": {"x": relx}})})
            ot("set_properties", {"instance": c,
                                  "values": json.dumps({"RelativeLocation": {"z": BASE["z"]}})})
            leido = json.loads(ot("get_properties", {"instance": c,
                                                     "properties": ["RelativeLocation"]}))["RelativeLocation"]
            out["camaras"].append({etiqueta: {
                "objeto": [round(ancho, 1), round(alto, 1)],
                "distancia": round(d, 1),
                "rel": [leido["x"], leido["y"], leido["z"]]}})

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": z["asset"]})
    return out
