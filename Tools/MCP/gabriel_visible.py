import json

# Gabriel no se veia en Play aunque en el editor estuviera perfecto.
#
# LA CAUSA: `BP_DA_GiantBoss` se esconde a si mismo. Su `BeginPlay` llama a
# `HideUntilWaveCleared()`, que hace `SetActorHiddenInGame(true)`, quita la
# colision, para el `BrainComponent` y arranca un timer `CheckWaveCleared`. El
# jefe solo vuelve a aparecer cuando no queda ningun `BP_WarriorAI` vivo **y**
# `EnemiesSpawned >= EnemiesToSpawn`. Eso se escribio para la arena, donde hay
# una oleada de por medio.
#
# En Malkuth no se cumple nunca: no hay ni un `BP_AISpawner` en todo el mapa, asi
# que el `Array.Get(..., 0)` del spawn devuelve null —de ahi el aviso
# "Accessed None ... CallFunc_Array_Get_Item" al arrancar PIE— y el guerrero sale
# en el ORIGEN DEL MUNDO, (0, 0, 48), a 66 km de la sala de los espejos. Como no
# muere, el jefe se queda invisible para siempre.
#
# EL INTERRUPTOR ES `EnemiesToSpawn`, que ya existe y ya es Instance Editable. No
# se anade variable nueva a proposito: una variable nueva no la recogen los
# actores ya colocados, y el jefe de la arena se quedaria sin su oleada. Con
# `EnemiesToSpawn = 0` la comparacion `> 0` que se anadio a `HideUntilWaveCleared`
# falla y se va por la rama nueva: **ni se esconde ni se queda sin colision, solo
# StopLogic**. Visible y quieto, que es lo que se quiere en la sala de los espejos.
#
# > COMPROBAR que el Giant de `L_DA_SeraphArena_POC` sigue con `EnemiesToSpawn = 2`
# > en su INSTANCIA. Ahi la oleada tiene que seguir funcionando igual.
#
# EL SEGUNDO BUG: el placeholder `SM_Gabriel` estaba escondido con `bHidden`, pero
# **`bHidden` no quita la colision**. Su caja llega a z=114,5 y la capsula del jefe
# se apoyaba encima: en PIE subia de z=266 a z=377, 111 unidades de mas. En cuanto
# dejara de estar oculto habria aparecido flotando. Se borra.
#
# EL TERCERO, QUE SALIO SOLO: la correccion de los 186 unidades de "Gabriel estaba
# enterrado" NUNCA LLEGO AL DISCO. Ese commit (8cb5fc3) solo toca
# `L_DA_Malkuth_Master.umap`, y Gabriel no vive ahi: vive dentro del `_Sub`, que no
# se guardo. El valor bueno solo existia en la memoria del editor, y el primer
# `edit_level_instance` lo tiro: el actor volvio a z=80, que es 266-186. Por eso
# este script REPONE LA Z.
#
# ### NO SE TOCA LA LEVEL INSTANCE: se abre el sub-mapa y punto
#
# El ciclo `edit_level_instance` -> cambios -> `commit_level_instance` **descarto
# el trabajo dos veces seguidas**, devolviendo exito y con `is_dirty` en false las
# dos. Los actores que devuelve `find_actors` durante esa sesion viven en un
# duplicado transitorio (`/Temp/Game/...`) y lo que se les hace no vuelve al asset.
# Cargar el `_Sub` como nivel normal da la ruta de verdad
# (`/Game/DarkAngels/Maps/...`), el `is_dirty` se comporta y el `.umap` cambia en
# disco. **Al terminar hay que volver a cargar el maestro**, o los scripts de otras
# zonas no encuentran Level Instances que abrir.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
JEFE = "GC2_Gabriel"
PLACEHOLDER = "SM_Gabriel"

# Capsula de 264 de media altura, malla con desfase -270: con el origen del actor
# en 266 la capsula apoya en z=2 y los pies de la malla quedan en la cota del piso.
Z_BUENA = 266.0


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    sc("load_level", {"level_path": ASSET})
    out = {"nivel": sc("get_current_level", {})}

    jefe = busca(JEFE)
    if jefe is None:
        return {"error": "no esta " + JEFE, "hecho": out}

    t0 = at("get_actor_transform", {"actor": jefe})
    out["antes"] = json.loads(ot("get_properties", {"instance": jefe,
                                                    "properties": ["enemiesToSpawn"]}))
    out["antes"]["z"] = round(t0["location"]["z"], 1)

    ot("set_properties", {"instance": jefe,
                          "values": json.dumps({"enemiesToSpawn": 0})})

    # Las tres componentes, siempre: `set_actor_transform` resetea escala y
    # rotacion si no se las pasas.
    at("set_actor_transform", {"actor": jefe, "worldspace": True, "xform": {
        "location": {"x": t0["location"]["x"], "y": t0["location"]["y"], "z": Z_BUENA},
        "rotation": {"pitch": t0["rotation"]["pitch"], "yaw": t0["rotation"]["yaw"],
                     "roll": t0["rotation"]["roll"]},
        "scale": {"x": t0["scale"]["x"], "y": t0["scale"]["y"], "z": t0["scale"]["z"]}}})

    ph = busca(PLACEHOLDER)
    out["placeholder"] = "no estaba"
    if ph is not None:
        sc("remove_from_scene", {"actor": ph})
        out["placeholder"] = "borrado"

    t = at("get_actor_transform", {"actor": jefe})
    out["despues"] = json.loads(ot("get_properties", {"instance": jefe,
                                                      "properties": ["enemiesToSpawn"]}))
    out["despues"]["z"] = round(t["location"]["z"], 1)
    out["despues"]["esc"] = [round(t["scale"][k], 3) for k in ("x", "y", "z")]
    out["despues"]["yaw"] = round(t["rotation"]["yaw"], 1)

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": ASSET})

    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = sc("get_current_level", {})
    return out
