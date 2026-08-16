import json

# Pone la animacion idle en bucle a los dos NPC de Malkuth.
#
# La IMPORTACION de la animacion hay que hacerla a mano: el `import_file` del
# toolset siempre entra por el factory de **StaticMesh** —se ve en el log,
# `FactoryCreateFile: StaticMesh with FbxFactory`— y con un FBX de animacion eso
# acaba en "produced no assets". Da igual pasarle `skeleton` y
# `import_animations`, y da igual que el FBX este dentro o fuera del proyecto.
#
# Hay que importarla a mano una vez POR ESQUELETO: cada malla tiene el suyo,
# aunque los dos compartan la misma jerarquia AccuRig de 118 huesos.
#
# El FBX trae DOS takes y salen dos AnimSequence:
#   `Idle_NPCidle-random-01`  -> el idle de cuerpo, **el que se usa**
#   `Idle_NPC0_Open_A_UE5`    -> pista de expresion facial de AccuRig, no se usa
#
# Una vez existan, este script las engancha. Los NPC son `SkeletalMeshActor`, no
# Characters, asi que la reproduccion va por `AnimationSingleNode`:
# se apunta `AnimToPlay` y se marcan `bSavedLooping` y `bSavedPlaying`.

NPCS = [
    {
        "actor": "NPC_Sariel",
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "anim": "/Game/DarkAngels/Characters/NPCs/Anim/A_DA_Idle_Sariel.A_DA_Idle_Sariel",
    },
    {
        "actor": "NPC_Cassiel",
        "li": "LI_06_SantuarioMalkuth",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub",
        "anim": "/Game/DarkAngels/Characters/NPCs/Anim/A_DA_Idle_Cassiel.A_DA_Idle_Cassiel",
    },
]

# Cual de los dos hacer en esta pasada: un solo ciclo edit/commit por Level
# Instance y por lanzamiento, que encadenarlos bloquea el .umap.
INDICE = 0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    n = NPCS[INDICE]
    if not call("editor_toolset.toolsets.asset.AssetTools.exists", {"path": n["anim"].split(".")[0]}):
        return {"error": "falta la animacion " + n["anim"].split(".")[0] + " (hay que importarla a mano)"}

    li = None
    for a in find("LI_"):
        if label(a) == n["li"]:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + n["li"]}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    # El actor REAL, no la copia instanciada en /Temp.
    actor = None
    for a in find(n["actor"]):
        if label(a) == n["actor"] and a["refPath"].startswith(n["asset"]):
            actor = a
            break
    if actor is None:
        return {"error": "no se encontro " + n["actor"] + " en el asset"}

    hecho = None
    for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": actor}):
        if "MeshComponent" not in c["refPath"]:
            continue
        call("editor_toolset.toolsets.object.ObjectTools.set_properties", {
            "instance": c,
            "values": json.dumps({
                "AnimationMode": "AnimationSingleNode",
                "AnimationData": {"AnimToPlay": {"refPath": n["anim"]},
                                   "bSavedLooping": True,
                                   "bSavedPlaying": True},
            })})
        hecho = call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                     {"instance": c, "properties": ["AnimationMode", "AnimationData"]})

    return {"npc": n["actor"], "leido": hecho,
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": n["asset"]})}
