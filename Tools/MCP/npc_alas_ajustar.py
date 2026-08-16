import json
import math

# Ajusta tamano y sitio de las alas de un NPC midiendo, no a ojo.
#
# RECETA COMPLETA, de cero, para el siguiente NPC que tenga alas:
#   1. Exportar de Tripo CON remesh. 45k-80k vertices; con plumas, mejor 80k.
#   2. Importar como SkeletalMesh y arreglar el material con
#      `tripo_arreglar_material.py` —el defecto de Tripo es siempre el mismo—.
#      **Y llamar a `save_assets` despues**: el import los deja sucios y sin
#      escribir, con lo que el .uasset no existe en disco.
#   3. Crear el socket en la malla del NPC: `add_socket` sobre `spine_05`.
#   4. Colocar el actor de las alas en el nivel, con `alas_sariel_colocar.py`
#      como plantilla.
#   5. **Enganchar al socket A MANO**, arrastrando en el Outliner (ver abajo).
#   6. Anadir el NPC a `NPCS` aqui y lanzar este script. Repetir hasta que el
#      informe diga que la orientacion esta bien.
#
# EL ENGANCHE AL SOCKET NO SE PUEDE HACER DESDE AQUI, y tampoco desde el panel
# Details: `AttachSocketName` esta declarada en el motor **sin `EditAnywhere`**,
# asi que no la expone el MCP ni sale en el buscador de propiedades. El socket se
# elige **al enganchar**, arrastrando el actor sobre `NPC_Sariel` en el Outliner:
# como su malla tiene sockets, Unreal abre una lista y ahi se escoge `Alas`.
# Si ya estaba enganchado, primero hay que soltarlo (Attach > Detach).
#
# Al asignar el socket las alas SALTAN a la posicion del hueso, asi que este
# script hay que relanzarlo despues: recoloca en espacio de mundo, con lo que da
# igual lo que herede del padre.
#
# LA ORIENTACION, Y EL ERROR QUE COSTO TRES PASADAS:
# **los personajes de Tripo NO miran a su +X local, miran a su +Y.** Se comprueba
# sin abrir nada, con la caja de Sariel: 71,7 en X frente a 53,1 en Y. Un humano
# es mas ancho de hombros que de pecho a espalda, asi que el eje ANCHO es el de
# los hombros; si el ancho cae en X, el que mira es el Y.
#
# De ahi salen las dos formulas:
#     adelante = (-sin(yaw), cos(yaw))     <- +Y local, no +X
#     los hombros van por (cos(yaw), sin(yaw))
#
# Y como las alas abren por su X local, su yaw es el MISMO que el del personaje
# (`YAW_EXTRA = 0`): asi su envergadura cae sobre el eje de los hombros.
#
# Lo enganioso es que un emblema de cuatro alas es simetrico y parece correcto
# desde casi cualquier angulo. La comprobacion buena no es mirar la captura sino
# **medir la caja**: la envergadura tiene que caer sobre el eje ancho del
# personaje, y el fondo de las alas sobre el estrecho.

NPCS = {
    "sariel": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "npc": "NPC_Sariel",
        "alas": "Sariel_Alas",
        "envergadura": 230.0,    # ancho total buscado, en unidades de mundo
        "altura": 0.74,          # que fraccion de su altura: los omoplatos
        "detras": 36.0,          # el eje de las alas cae justo sobre su espalda
    },
    "cassiel": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "npc": "NPC_Cassiel",
        "alas": "Cassiel_Alas",
        # Las suyas son mas ALTAS que anchas (0,76 x 0,30 x 0,98), al reves que
        # el emblema de Sariel: con 200 de envergadura salen unos 258 de alto,
        # frente a los 194 que mide el. Si quedan pasadas, bajar este numero.
        "envergadura": 200.0,
        "altura": 0.74,
        "detras": 36.0,
    },
}

CUAL = "cassiel"

YAW_EXTRA = 0.0         # ver la nota de arriba: las alas van al mismo yaw que el


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


def caja(a):
    b = at("get_actor_bounds", {"actor": a})
    return {"min": [round(b["min"][k], 1) for k in ("x", "y", "z")],
            "max": [round(b["max"][k], 1) for k in ("x", "y", "z")],
            "tamano": [round(b["max"][k] - b["min"][k], 1) for k in ("x", "y", "z")]}


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    n = NPCS[CUAL]
    ASSET = n["asset"]
    ENVERGADURA, ALTURA_RELATIVA, DETRAS = n["envergadura"], n["altura"], n["detras"]

    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == n["li"]:
                li = a
                break
        if li is None:
            return {"error": "no encontrado " + n["li"]}
        sc("edit_level_instance", {"level_instance": li})

    npc = en_el_asset(n["npc"], ASSET)
    alas = en_el_asset(n["alas"], ASSET)
    if npc is None or alas is None:
        return {"error": "falta " + n["npc"] + " o " + n["alas"]}

    t_s = at("get_actor_transform", {"actor": npc})
    b_s = at("get_actor_bounds", {"actor": npc})
    yaw = t_s["rotation"]["yaw"]
    alto = b_s["max"]["z"] - b_s["min"]["z"]
    centro = [(b_s["min"]["x"] + b_s["max"]["x"]) / 2.0,
              (b_s["min"]["y"] + b_s["max"]["y"]) / 2.0]

    # Su frente es su +Y LOCAL, no su +X. Su espalda, por tanto, al reves.
    adelante = (-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)))
    destino = {"x": round(centro[0] - adelante[0] * DETRAS, 1),
               "y": round(centro[1] - adelante[1] * DETRAS, 1),
               "z": round(b_s["min"]["z"] + alto * ALTURA_RELATIVA, 1)}

    # Comprobacion que no depende de mirar una captura: el eje ancho del
    # personaje es el de sus hombros, y ahi es donde tiene que caer la
    # envergadura. Si esto sale mal, la orientacion esta mal.
    ancho_x = b_s["max"]["x"] - b_s["min"]["x"]
    ancho_y = b_s["max"]["y"] - b_s["min"]["y"]
    eje_hombros = "X" if ancho_x > ancho_y else "Y"

    # Escala: se mide lo que ocupan AHORA y se corrige por regla de tres, que es
    # inmune a como se hereden las escalas del padre.
    antes = at("get_actor_bounds", {"actor": alas})
    t_a = at("get_actor_transform", {"actor": alas})
    ancho_actual = max(antes["max"]["x"] - antes["min"]["x"],
                       antes["max"]["y"] - antes["min"]["y"])
    factor = ENVERGADURA / ancho_actual if ancho_actual > 0.01 else 1.0
    nueva = round(t_a["scale"]["x"] * factor, 2)

    at("set_actor_transform", {"actor": alas,
                               "xform": {"location": t_a["location"],
                                         "rotation": {"pitch": 0.0, "yaw": yaw + YAW_EXTRA, "roll": 0.0},
                                         "scale": {"x": nueva, "y": nueva, "z": nueva}},
                               "worldspace": True})

    # EL PIVOTE DE LA MALLA ESTA EN LA BASE, como en todos los props de Tripo:
    # colocada por su origen, el ala CRECE HACIA ARRIBA y le sale de la cabeza.
    # Asi que se mide otra vez ya escalada, se calcula cuanto se desvia el centro
    # de la caja respecto del origen del actor, y se corrige con esa diferencia.
    ya = at("get_actor_bounds", {"actor": alas})
    t_a2 = at("get_actor_transform", {"actor": alas})
    desvio = {k: (ya["min"][k] + ya["max"][k]) / 2.0 - t_a2["location"][k] for k in ("x", "y", "z")}
    final = {k: round(destino[k] - desvio[k], 1) for k in ("x", "y", "z")}
    at("set_actor_transform", {"actor": alas,
                               "xform": {"location": final,
                                         "rotation": {"pitch": 0.0, "yaw": yaw + YAW_EXTRA, "roll": 0.0},
                                         "scale": {"x": nueva, "y": nueva, "z": nueva}},
                               "worldspace": True})
    destino = final

    c_alas = caja(alas)
    eje_envergadura = "X" if c_alas["tamano"][0] > c_alas["tamano"][1] else "Y"
    out = {"npc": CUAL, n["npc"]: {"yaw": round(yaw, 1), "alto": round(alto, 1),
                      "eje_hombros": eje_hombros, "caja": caja(npc)},
           "alas": {"escala_antes": round(t_a["scale"]["x"], 2), "escala_ahora": nueva,
                    "ancho_antes": round(ancho_actual, 1),
                    "destino": [destino["x"], destino["y"], destino["z"]],
                    "eje_envergadura": eje_envergadura,
                    "caja": c_alas},
           "socket": "Alas, sobre spine_05",
           "ORIENTACION": ("bien: la envergadura cae sobre los hombros"
                           if eje_envergadura == eje_hombros
                           else "MAL: la envergadura va de pecho a espalda, revisar YAW_EXTRA")}

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
