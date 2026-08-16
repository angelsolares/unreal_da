import json

# Le pone alas al BLUEPRINT de un enemigo, no a sus instancias: asi las heredan
# todas las que haya puestas en el nivel y las que se pongan despues.
#
# POR QUE ESTAS ALAS SIRVEN PARA CUALQUIER PERSONAJE: `SKM_Wings5` trae **su
# propio esqueleto** (`SK_Wings5_Skeleton`, 27 huesos) y sus propias
# animaciones. No es un anadido al rig del personaje, es una malla aparte que se
# cuelga de un socket y se anima sola, asi que da igual el esqueleto que use
# quien las lleve.
#
# POR QUE NO SE USA `ABP_Wings5`, EL ANIMBP DEL PACK: su padre `ABP_WingsBase`
# hace **cast a `BP_ThirdPersonCharacter`**, el personaje de la demo, para leerle
# el estado de vuelo. Nuestros enemigos heredan de `BP_BaseAI` de DCS, asi que
# ese cast falla y el AnimBP se queda en su estado por defecto: no aporta nada y
# arrastraria toda la demo al proyecto. Se usa `AnimationSingleNode` con
# `idle_ground` en bucle, que es la misma receta de los NPC. Si algun dia se
# quiere que las alas reaccionen al combate, hay que reescribir ese cast a
# `BP_BaseAI`; entonces si valdria la pena traerse el AnimBP.
#
# LA ESCALA SE CONTRARRESTA: las alas vienen a tamanio real —215 de envergadura,
# hechas para un Manny de 180— pero el componente cuelga de `CharacterMesh0`,
# que en nuestros enemigos va a 1,8273. Sin corregir saldrian a 393. Por eso la
# escala relativa es 1/1,8273.
#
# EL SOCKET HAY QUE ASIGNARLO A MANO, una vez por blueprint: `AttachSocketName`
# esta declarada en el motor sin `EditAnywhere` y el MCP no la expone. En el
# editor de Blueprints si sale: se selecciona el componente `Alas` y en Details
# aparece **Parent Socket**. Ahi se elige `Alas`. (En actores de nivel ese
# desplegable no existe; hay que arrastrar en el Outliner. Aqui es mas facil.)

PACK = "/Game/Angel_wings_pack/"
MALLA_ALAS = PACK + "Meshes/SKM_Wings5.SKM_Wings5"
ANIM = PACK + "Animations/5/Animations/AS__AS_W5_idle_ground.AS__AS_W5_idle_ground"

HUESO = "spine_05"
SOCKET = "Alas"
COMPONENTE = "Alas"

# Cada enemigo: su blueprint y su malla. Anadir aqui los que vengan.
ENEMIGOS = [
    {"bp": "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Vigilante",
     "malla": "/Game/DarkAngels/Characters/Enemigos/SK_DA_Vigilante"},
    {"bp": "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Lancero",
     "malla": "/Game/DarkAngels/Characters/Enemigos/SK_DA_Lancero"},
    {"bp": "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Arquero",
     "malla": "/Game/DarkAngels/Characters/Enemigos/SK_DA_Arquero"},
]

ESCALA_MALLA = 1.8273    # la de `CharacterMesh0`, que el componente hereda
ALTURA = -10.0           # ajuste fino sobre el hueso, en unidades del hueso

# LA ROTACION NO ES CERO, Y NO ES CAPRICHO. Los huesos de la columna del
# Mannequin llevan su **X a lo largo del hueso**, o sea apuntando hacia la
# cabeza. Colgadas sin rotar, las alas salen de canto: su eje de envergadura
# —que es su X local, 215 de los 215x46x61 que miden— apunta hacia ARRIBA, y
# queda una lamina vertical atravesando al personaje de delante atras.
#
# Hace falta la permutacion ciclica de ejes  X->Y, Y->Z, Z->X, que en matriz es
#     [0 0 1]
#     [1 0 0]
#     [0 1 0]
# Resolviendo esa matriz para el orden de Unreal —R = Rz(yaw)·Ry(pitch)·Rx(roll)—
# salen pitch 0, yaw 90, roll 90.
ROTACION = {"pitch": 0.0, "yaw": 90.0, "roll": 0.0}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def sm(t, a):
    return call("editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    escala = round(1.0 / ESCALA_MALLA, 4)
    out = {"escala_relativa": escala, "hechos": []}
    guardar = []

    for e in ENEMIGOS:
        nombre = e["bp"].split("/")[-1]
        d = {"enemigo": nombre}

        if not call("editor_toolset.toolsets.asset.AssetTools.exists", {"path": e["bp"]}):
            d["error"] = "no existe el blueprint"
            out["hechos"].append(d)
            continue

        # 1. El socket en la espalda, sobre el asset de malla.
        malla = {"refPath": e["malla"] + "." + e["malla"].split("/")[-1]}
        if SOCKET not in sm("get_socket_names", {"mesh": malla}):
            sm("add_socket", {"mesh": malla, "socket_name": SOCKET, "bone_name": HUESO})
        d["socket"] = sm("get_socket_bone", {"mesh": malla, "socket_name": SOCKET})
        guardar.append(e["malla"])

        # 2. El componente en el blueprint.
        bp = {"refPath": e["bp"] + "." + e["bp"].split("/")[-1]}
        cdo = bt("get_default_object", {"blueprint": bp})
        tenia = {}
        for c in at("get_components", {"actor": cdo}):
            tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c

        if COMPONENTE in tenia:
            comp = tenia[COMPONENTE]
            d["componente"] = "ya estaba"
        else:
            comp = at("add_component", {"owner": bp, "name": COMPONENTE,
                                        "component_type": {"refPath": "/Script/Engine.SkeletalMeshComponent"}})
            d["componente"] = "creado"
        # SOLO SE EMPARENTA SI HACE FALTA. `set_parent_component` **borra el
        # socket**: reengancha el componente a la raiz del padre y deja
        # `AttachSocketName` vacio. Como el socket lo pone Angel a mano y este
        # script se relanza para afinar rotacion y escala, llamarlo siempre le
        # pisaba el trabajo en cada pasada —y encima sin avisar: las alas se
        # iban a los pies y parecia un problema de rotacion.
        padre_actual = at("get_parent_component", {"component": comp})
        ya_colgado = (padre_actual is not None
                      and str(padre_actual).endswith("CharacterMesh0'}"))
        if "CharacterMesh0" in tenia and not ya_colgado:
            at("set_parent_component", {"component": comp, "parent": tenia["CharacterMesh0"]})
            d["emparentado"] = "SI (ojo: hay que volver a poner el Parent Socket)"
        else:
            d["emparentado"] = "ya lo estaba, no se toca"

        # 3. Malla, animacion en bucle y escala. Un campo por llamada en los
        #    structs: el setter se deja campos por el camino si van juntos.
        ot("set_properties", {"instance": comp, "values": json.dumps({
            "SkeletalMeshAsset": {"refPath": MALLA_ALAS},
            "AnimationMode": "AnimationSingleNode",
            "AnimationData": {"AnimToPlay": {"refPath": ANIM},
                               "bSavedLooping": True, "bSavedPlaying": True},
        })})
        for eje in ("x", "y", "z"):
            ot("set_properties", {"instance": comp,
                                  "values": json.dumps({"RelativeScale3D": {eje: escala}})})
        ot("set_properties", {"instance": comp,
                              "values": json.dumps({"RelativeLocation": {"z": ALTURA}})})
        for eje in ROTACION:
            ot("set_properties", {"instance": comp,
                                  "values": json.dumps({"RelativeRotation": {eje: ROTACION[eje]}})})

        bt("compile_blueprint", {"blueprint": bp})
        guardar.append(e["bp"])

        leido = json.loads(ot("get_properties", {"instance": comp, "properties": [
            "SkeletalMeshAsset", "AnimationMode", "RelativeScale3D"]}))
        d["malla_alas"] = str(leido["SkeletalMeshAsset"]).split("/")[-1].rstrip("'}")
        d["modo"] = leido["AnimationMode"]
        d["escala"] = [round(leido["RelativeScale3D"][k], 4) for k in ("x", "y", "z")]
        out["hechos"].append(d)

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": guardar})
    out["sucios"] = [a for a in guardar
                     if call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": a})]
    out["falta"] = ("asignar Parent Socket = 'Alas' al componente Alas, "
                    "una vez por blueprint, en el editor de Blueprints")
    return out
