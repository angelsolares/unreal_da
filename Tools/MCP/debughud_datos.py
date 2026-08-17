import json

# DA Debug HUD (fase 1) — capa de datos de los destinos de teleport.
#
# POR QUE UNA LINEA DE TEXTO POR DESTINO Y NO UN DATA TABLE NI UN STRUCT:
#
#  1. El MCP **no puede crear structs de usuario** (no hay toolset de structs) y
#     `DataTableTools.create` exige un struct hijo de TableRowBase: los unicos
#     que hay son de motor y ninguno sirve. Data Table descartado.
#  2. De los padres de blueprint posibles, `DataAsset` **no** se puede crear por
#     MCP; `PrimaryDataAsset` si. De ahi la clase.
#  3. `ObjectTools.set_properties` **escribe los structs a medias y en silencio**
#     (ver las notas: un BoxExtent quedo con solo el primer campo, y los arrays
#     de structs pierden el ultimo elemento). Un array de Transform escrito por
#     MCP habria quedado corrupto sin avisar. Los arrays de tipos simples si van
#     bien: se comprobo que un array de string se escribe entero.
#
# Asi que cada destino es UNA linea de texto con cinco campos separados por "|":
#
#     Nombre | Categoria | X=.. Y=.. Z=.. | P=.. Y=.. R=.. | Descripcion
#
# El blueprint convierte los campos 3 y 4 con `StringToVector` y
# `StringToRotator`, que son nodos de motor. Anadir un destino = anadir una
# linea al array en el editor: ni un boton nuevo, ni tocar ningun grafo.
#
# Las coordenadas son EXACTAMENTE las que ya usa el salto por NumPad
# (Tools/MCP/hud_orden_zonas.py), medidas con trazas verticales y verificadas en
# juego. No se inventa ninguna ubicacion que no exista.

CARPETA = "/Game/DarkAngels/Debug"
CLASE_NOM = "BP_DA_DebugDestinos"
CLASE = CARPETA + "/" + CLASE_NOM + "." + CLASE_NOM
ASSET_NOM = "DA_DA_DebugDestinos"
ASSET = CARPETA + "/" + ASSET_NOM + "." + ASSET_NOM

VIEJAS = ["Nombres", "Puntos", "Categorias", "Descripciones"]

# (nombre, categoria, x, y, z, yaw, descripcion)
DESTINOS = [
    ("Jardin",     "Recorrido", -59649.0, -60004.0,   138.0,  90.0, "01 Jardin de las Hostias"),
    ("Mirador",    "Ramal",     -16000.0, -23800.0,   438.0,  90.0, "03 Mirador (opcional)"),
    ("El Claro",   "Recorrido",  44000.0, -13650.0,    84.0,  90.0, "04 El Claro"),
    ("Gazebo",     "Ramal",      64000.0,  15400.0,   184.0,  90.0, "05 Gazebo de la rotonda"),
    ("Santuario",  "Recorrido",  43940.0,  47600.0,   118.0, 180.0, "06 Santuario de Malkuth"),
    ("Puente",     "Recorrido",  16000.0,  60000.0,  1532.0, 180.0, "07 Puente"),
    ("Anfiteatro", "Recorrido", -73649.0,  41996.0,   136.0, 270.0, "08 Anfiteatro"),
    ("Elevador",   "Recorrido", -74000.0,   8000.0,    94.0, 270.0, "09 Elevador"),
    ("Gabriel",    "Boss",      -66000.0, -15000.0,   281.0, 270.0, "10-12 Camara de Gabriel (C2)"),
    ("Yesod",      "Final",     -92000.0,  15200.0,   184.0,   0.0, "13 Portal a Yesod"),
]


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ast(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t,
                        json.dumps(a))["returnValue"]


def dat(t, a):
    return execute_tool("editor_toolset.toolsets.data_asset.DataAssetTools." + t,
                        json.dumps(a))["returnValue"]


def obj(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t,
                        json.dumps(a))["returnValue"]


def linea(d):
    nombre, cat, x, y, z, yaw, desc = d
    return "%s | %s | X=%.1f Y=%.1f Z=%.1f | P=0 Y=%.1f R=0 | %s" % (
        nombre, cat, x, y, z, yaw, desc)


def run():
    out = {}
    ast("create_folder", {"path": CARPETA})

    # --- 1. La clase de datos ---
    if not ast("exists", {"path": CARPETA + "/" + CLASE_NOM}):
        bp("create", {"folder_path": CARPETA, "asset_name": CLASE_NOM,
                      "asset_type": {"refPath": "/Script/Engine.PrimaryDataAsset"}})
    ya = bp("list_variables", {"blueprint": {"refPath": CLASE}})
    for v in VIEJAS:
        if v in ya:
            bp("remove_variable", {"blueprint": {"refPath": CLASE}, "name": v})
    if "Destinos" not in ya:
        bp("add_variable", {"blueprint": {"refPath": CLASE}, "name": "Destinos",
                            "type_name": "string", "container_type": "ARRAY"})
    bp("set_variable_instance_editable", {"blueprint": {"refPath": CLASE},
                                          "variable_name": "Destinos",
                                          "instance_editable": True})
    bp("set_variable_category", {"blueprint": {"refPath": CLASE},
                                 "variable_name": "Destinos", "category": "DA Debug"})
    bp("compile_blueprint", {"blueprint": {"refPath": CLASE}})
    out["variables"] = bp("list_variables", {"blueprint": {"refPath": CLASE}})

    # --- 2. El asset con los datos ---
    if not ast("exists", {"path": CARPETA + "/" + ASSET_NOM}):
        dat("create", {"folder_path": CARPETA, "asset_name": ASSET_NOM,
                       "asset_type": {"refPath": CLASE + "_C"}})
    inst = {"refPath": ASSET}
    obj("set_properties", {"instance": inst,
                           "values": json.dumps({"Destinos": [linea(d) for d in DESTINOS]})})

    # --- 3. Verificar lo que quedo escrito, no lo que se mando ---
    leido = json.loads(obj("get_properties", {"instance": inst,
                                              "properties": ["Destinos"]}))["Destinos"]
    out["escritos"] = len(leido)
    out["primero"] = leido[0] if leido else None
    out["ultimo"] = leido[-1] if leido else None
    out["completo"] = (len(leido) == len(DESTINOS)
                       and leido[-1] == linea(DESTINOS[-1]))

    ast("save_assets", {"asset_paths": [CARPETA + "/" + CLASE_NOM,
                                        CARPETA + "/" + ASSET_NOM]})
    return out
