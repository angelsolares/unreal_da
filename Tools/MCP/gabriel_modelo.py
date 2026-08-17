import json

# Cambia la malla del jefe por el Gabriel de verdad, el de Tripo pasado por
# AccuRig, igual que se hizo con los enemigos y con Malakh.
#
# **CUIDADO CON EL ESQUELETO: NO ES EL DE DCS.** Los enemigos y Malakh van sobre
# `SK_Mannequin` de `DynamicCombatSystem/Demo/`, pero el jefe hereda de `BP_Giant`
# y su `ABP_Giant` apunta al maniqui que vive dentro de `GiantBossProject/`. Son
# dos copias distintas del mismo maniqui de UE5, en dos assets distintos.
# Importar contra el de DCS dejaria a Gabriel sin una sola de las 18 animaciones
# de ataque del jefe. Por eso el esqueleto no se escribe a mano aqui: se le
# pregunta a la malla que el jefe lleva puesta ahora.
#
# LA ESCALA SE CALCULA, no se copia. La malla vieja y la nueva no miden lo mismo
# en crudo, asi que se ajusta para que Gabriel acabe con la MISMA altura en
# pantalla que tenia el Giant: escala_nueva = escala_vieja * alto_viejo/alto_nuevo.
# Asi no se descoloca ni la capsula ni el encuadre de la camara.

JEFE = "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss.BP_DA_GiantBoss"
ORIGEN = "D:/Game Projects/Dark Angels/Bosses/Gabriel/gabriel rigged.fbx"
CARPETA = "/Game/DarkAngels/Characters/Bosses"
NOMBRE = "SK_DA_Gabriel"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def sm(t, a):
    return call("editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools." + t, a)


def alto(malla):
    b = sm("get_bounds", {"mesh": malla})
    return b["boxExtent"]["z"] * 2.0


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    bp = {"refPath": JEFE}
    cdo = bt("get_default_object", {"blueprint": bp})
    comp = None
    for c in at("get_components", {"actor": cdo}):
        if "CharacterMesh0" in c["refPath"]:
            comp = c
    if comp is None:
        return {"error": "el jefe no tiene CharacterMesh0"}

    antes = json.loads(ot("get_properties", {"instance": comp, "properties":
                                             ["skeletalMeshAsset", "relativeScale3D"]}))
    vieja = antes["skeletalMeshAsset"]
    esqueleto = sm("get_skeleton", {"mesh": vieja})
    alto_viejo = alto(vieja)
    escala_vieja = antes["relativeScale3D"]["z"]

    ruta = CARPETA + "/" + NOMBRE
    if not call("editor_toolset.toolsets.asset.AssetTools.exists", {"path": ruta}):
        sm("import_file", {"folder_path": CARPETA, "asset_name": NOMBRE,
                           "source_file": ORIGEN, "skeleton": esqueleto,
                           "import_materials": True, "import_textures": True,
                           "import_animations": False, "create_physics_asset": True})
        estado = "importado"
    else:
        estado = "ya estaba"

    nueva = {"refPath": ruta + "." + NOMBRE}
    alto_nuevo = alto(nueva)
    escala = escala_vieja * (alto_viejo / alto_nuevo)

    ot("set_properties", {"instance": comp,
                          "values": json.dumps({"skeletalMeshAsset": nueva})})
    # Un eje por llamada: el setter de structs se deja los demas.
    for eje in ("x", "y", "z"):
        ot("set_properties", {"instance": comp,
                              "values": json.dumps({"relativeScale3D": {eje: escala}})})
    bt("compile_blueprint", {"blueprint": bp})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [ruta, JEFE.split(".")[0]]})

    return {"estado": estado,
            "esqueleto": esqueleto,
            "malla_vieja": str(vieja).split("/")[-1].rstrip("'}"),
            "alto_crudo": {"viejo": round(alto_viejo, 1), "nuevo": round(alto_nuevo, 1)},
            "escala": {"vieja": round(escala_vieja, 4), "nueva": round(escala, 4)},
            "huesos": len(sm("get_bone_names", {"mesh": nueva})),
            "vertices": sm("get_vertex_count", {"mesh": nueva, "lod_index": 0}),
            "materiales": sm("get_material_slots", {"mesh": nueva}),
            "puesto": json.loads(ot("get_properties", {"instance": comp, "properties":
                                                       ["skeletalMeshAsset", "relativeScale3D"]}))}
