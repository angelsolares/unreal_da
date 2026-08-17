import json

# Importa el Malakh riggeado de AccuRig y lo pone como malla del jugador.
#
# **SOBRE EL ESQUELETO DE DCS, NO SOBRE UNO NUEVO.** Es lo mismo que se hizo con
# los enemigos: pasandole `skeleton` al importador, la malla entra atada a
# `SK_Mannequin` y **todas las animaciones del pack valen tal cual**, sin
# retargeting. Si se deja el esqueleto vacio, el importador crea uno propio y el
# personaje se queda sin una sola animacion.
#
# El importador de mallas esqueleticas vive en `SkeletalMeshTools.import_file`,
# no en `AssetTools`. (Yo mismo di por hecho que no existia y le pedi a Angel que
# lo hiciera a mano: existe.)

ORIGEN = "D:/Game Projects/Dark Angels/Malakh/Malakh Rigged.fbx"
CARPETA = "/Game/DarkAngels/Characters/Malakh"
NOMBRE = "SK_DA_Malakh"
ESQUELETO = ("/Game/DynamicCombatSystem/Demo/Meshes/Mannequins/Meshes/"
             "SK_Mannequin.SK_Mannequin")


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sm(t, a):
    return call("editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    ruta = CARPETA + "/" + NOMBRE
    if not call("editor_toolset.toolsets.asset.AssetTools.exists", {"path": ruta}):
        sm("import_file", {"folder_path": CARPETA, "asset_name": NOMBRE,
                           "source_file": ORIGEN,
                           "skeleton": {"refPath": ESQUELETO},
                           "import_materials": True, "import_textures": True,
                           "import_animations": False, "create_physics_asset": True})
        estado = "importado"
    else:
        estado = "ya estaba"

    malla = {"refPath": ruta + "." + NOMBRE}
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ruta]})
    return {"estado": estado,
            "esqueleto": sm("get_skeleton", {"mesh": malla}),
            "huesos": len(sm("get_bone_names", {"mesh": malla})),
            "vertices": sm("get_vertex_count", {"mesh": malla, "lod_index": 0}),
            "materiales": sm("get_material_slots", {"mesh": malla}),
            "bounds": sm("get_bounds", {"mesh": malla})}
