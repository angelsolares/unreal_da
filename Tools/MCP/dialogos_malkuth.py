import json

# Los dialogos de Malkuth, tal como los fija la Biblia Narrativa.
#
# LO QUE DICE LA BIBLIA, Y POR QUE HAY TAN POCO:
#
# **Sariel**, arco Malkuth-Yesod: *"aparece en el horizonte. No habla. Solo
# mira."* Su unica linea de Malkuth es la reaccion a que te acerques, y esta
# copiada literal:
#   "No. No te acerques. No quiero verte de cerca. Ver de cerca me hace
#    recordar. Y yo no quiero recordar."
#
# **Cassiel**, arco Malkuth-Yesod: *"aparece ocasionalmente en los Altares. No
# hace nada. Solo mira. Si Malakh reza, Cassiel inclina la cabeza."* Y su ficha
# es tajante: **se arranco la boca** para no poder contar el secreto que leyo, y
# *"nunca habla en voz alta"*. Su primer dialogo —y es DE LUZ, no de voz— no
# llega hasta Tiphareth.
#
# Asi que a Cassiel no se le inventa texto: lleva una acotacion entre parentesis
# describiendo lo que hace, que es lo unico fiel. Y su verbo pasa de "Hablar" a
# "Observar", porque "Hablar" con un personaje sin boca contradice su ficha.

ZONAS = {
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "quien": [{
            "actor": "Interact_Sariel",
            "verbo": "Hablar",
            "lineas": ["No. No te acerques.",
                       "No quiero verte de cerca. Ver de cerca me hace recordar.",
                       "Y yo no quiero recordar."],
        }],
    },
    "santuario": {
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "quien": [{
            "actor": "Interact_Cassiel",
            "verbo": "Observar",
            "lineas": ["(Cassiel te mira. No tiene boca.)",
                       "(Inclina la cabeza, muy despacio.)",
                       ""],
        }],
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


def en_el_asset(nombre, asset):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


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

    out = {"zona": CUAL, "puestos": []}
    for q in z["quien"]:
        a = en_el_asset(q["actor"], z["asset"])
        if a is None:
            out["puestos"].append({q["actor"]: "no encontrado"})
            continue
        # Un campo por llamada: el setter deja campos por el camino si van juntos.
        ot("set_properties", {"instance": a, "values": json.dumps({"Verbo": q["verbo"]})})
        for i, linea in enumerate(q["lineas"]):
            ot("set_properties", {"instance": a,
                                  "values": json.dumps({"Dialogo%d" % (i + 1): linea})})
        leido = json.loads(ot("get_properties", {"instance": a,
                                                 "properties": ["Verbo", "Dialogo1", "Dialogo2", "Dialogo3"]}))
        out["puestos"].append({q["actor"]: leido})

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": z["asset"]})
    return out
