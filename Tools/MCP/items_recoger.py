import json

# Crea los items de DarkAngels para el inventario de DCS y engancha cada uno a
# su interactuable del nivel. Anadir aqui lo que se pueda recoger.
#
# COMO FUNCIONA EL INVENTARIO DE DCS
# Un item **no es un blueprint**: es un asset de datos (`PrimaryDataAsset`) de
# clase `BP_DA_Item_Base`, con un unico campo `Item` de tipo `F_Item`:
#     name, description, type (E_ItemType), isStackable, isDroppable,
#     isConsumable, image (Texture2D)
# El componente `BP_InventoryComponent` del personaje guarda pares
# (asset, cantidad) y su funcion `AddItem(ItemToAdd, Amount)` es todo lo que hay
# que llamar. `BP_PickupActor` del pack no se usa: abre su propia ventana de
# botin (`WB_Pickup`) encima de la pantalla, que chocaria con el modo inspeccion.
# Nosotros recogemos directo desde `BP_DA_Interactuable`.
#
# EL ICONO ES UNA TEXTURA DE VERDAD, y no se puede sacar del editor:
#   - la miniatura del asset (`CaptureAssetImage`) sale casi vacia: la llave mide
#     menos de una unidad y en el nivel va escalada x71, asi que en la escena de
#     previsualizacion es una mota;
#   - la captura del viewport trae los adornos del editor —cajas de seleccion,
#     rejilla, el widget de ejes— y lo que haya delante.
# Sale de la foto de referencia, pasada por `icono.mjs`, que le recorta el fondo
# y la deja cuadrada con transparencia. Los ajustes de textura que usa DCS los
# pone `AJUSTES_ICONO` aqui abajo. Con `icono` a None el item funciona igual,
# solo que su hueco sale en blanco.

ITEMS = "/Game/DarkAngels/Items"
ICONOS = ITEMS + "/Iconos"
CLASE = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/BP_DA_Item_Base.BP_DA_Item_Base_C"

# Los mismos que trae `T_GoldenRing` y compania: sin mipmaps, sin streaming y
# con la compresion de iconos de UI.
AJUSTES_ICONO = {
    "CompressionSettings": "TC_EditorIcon",
    "LODGroup": "TEXTUREGROUP_Pixels2D",
    "MipGenSettings": "TMGS_NoMipmaps",
    "NeverStream": True,
    "SRGB": True,
}

CATALOGO = [
    {
        "asset": "DA_Llave_Mirador",
        "campos": {
            "name": "Llave del Mirador",
            "description": "Una llave sin cerradura conocida. Pesa mas de lo que deberia.",
            # `Tool` es el cajon de los objetos que no se equipan, el mismo que
            # usa la pocion. No hay un tipo "llave" en `E_ItemType`.
            "type": "Tool",
            "isStackable": False,
            "isDroppable": False,   # es de historia: que no se pueda soltar
            "isConsumable": False,
        },
        "icono": "T_DA_Icono_Llave",
        # Ruta absoluta: el importador del editor no sabe del directorio del
        # proyecto. El PNG lo genera:
        #   node Tools/MCP/icono.mjs <foto.png> ArtSource/Iconos/T_DA_Icono_Llave.png 256
        "icono_png": ("D:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/"
                      "ArtSource/Iconos/T_DA_Icono_Llave.png"),
    },
    {
        "asset": "DA_Fragmento_Malkuth",
        "campos": {
            "name": "Fragmento de Corruptio",
            "description": "Un trozo de algo que estuvo entero. Late cuando no lo miras.",
            "type": "Tool",
            "isStackable": False,
            "isDroppable": False,   # es de historia: que no se pueda soltar
            "isConsumable": False,
        },
        "icono": "T_DA_Icono_Fragmento",
        "icono_png": ("D:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/"
                      "ArtSource/Iconos/T_DA_Icono_Fragmento.png"),
    },
]

# Que interactuable entrega que item, y que actor hay que borrar del mundo al
# recogerlo. `Interact_Llave` no tiene malla propia: la llave que se ve es el
# actor `Mirador_Llave`, un SkeletalMeshActor al lado.
ZONAS = {
    "mirador": {
        "li": "LI_03_MiradorSariel",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
        "enlaces": [("Interact_Llave", "DA_Llave_Mirador", "Mirador_Llave", 1)],
    },
    "gazebo": {
        "li": "LI_05_RuinasGazebo",
        "asset": "/Game/DarkAngels/Maps/L_DA_Malkuth_Gazebo_Sub",
        "enlaces": [("Interact_Fragmento", "DA_Fragmento_Malkuth", "Gazebo_Fragmento", 1)],
    },
}

CUAL = "gazebo"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def en_el_asset(nombre, asset):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(asset):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    out = {"items": [], "enlaces": []}
    guardar = []

    # --- 1. los iconos ---
    for it in CATALOGO:
        if not it["icono"]:
            continue
        ruta = ICONOS + "/" + it["icono"]
        if not ast("exists", {"path": ruta}):
            call("editor_toolset.toolsets.texture.TextureTools.import_file",
                 {"folder_path": ICONOS, "asset_name": it["icono"],
                  "source_file": it["icono_png"]})
        tex = {"refPath": ruta + "." + it["icono"]}
        # Un ajuste por llamada, como con todo lo demas.
        for k in AJUSTES_ICONO:
            ot("set_properties", {"instance": tex, "values": json.dumps({k: AJUSTES_ICONO[k]})})
        out.setdefault("iconos", []).append({it["icono"]: {
            "tam": call("editor_toolset.toolsets.texture.TextureTools.get_size", {"texture": tex}),
            "ajustes": json.loads(ot("get_properties", {"instance": tex,
                                                        "properties": list(AJUSTES_ICONO)}))}})
        guardar.append(ruta)

    # --- 2. los assets de item ---
    for it in CATALOGO:
        ruta = ITEMS + "/" + it["asset"]
        if not ast("exists", {"path": ruta}):
            call("editor_toolset.toolsets.data_asset.DataAssetTools.create",
                 {"folder_path": ITEMS, "asset_name": it["asset"],
                  "asset_type": {"refPath": CLASE}})
        obj = {"refPath": ruta + "." + it["asset"]}
        # UN CAMPO POR LLAMADA: el setter de structs se deja por el camino todo
        # menos el primero. Aqui ademas el campo esta anidado dentro de `Item`.
        for k in it["campos"]:
            ot("set_properties", {"instance": obj,
                                  "values": json.dumps({"Item": {k: it["campos"][k]}})})
        if it["icono"]:
            ot("set_properties", {"instance": obj, "values": json.dumps(
                {"Item": {"image": {"refPath": ICONOS + "/" + it["icono"] + "." + it["icono"]}}})})
        out["items"].append({it["asset"]: json.loads(
            ot("get_properties", {"instance": obj, "properties": ["Item"]}))})
        guardar.append(ruta)

    ast("save_assets", {"asset_paths": guardar})
    out["sucios"] = [r for r in guardar if ast("is_dirty", {"asset_path": r})]

    # --- 3. los enlaces en el nivel ---
    z = ZONAS[CUAL]
    directo = sc("get_current_level", {}).startswith(z["asset"])
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == z["li"]:
                li = a
                break
        if li is None:
            return {"error": "ni el sublevel abierto ni el LI " + z["li"], "hecho": out}
        sc("edit_level_instance", {"level_instance": li})

    for interactuable, item, malla, cuantos in z["enlaces"]:
        i = en_el_asset(interactuable, z["asset"])
        m = en_el_asset(malla, z["asset"])
        if i is None or m is None:
            out["enlaces"].append({interactuable: "falta %s=%s o %s=%s" % (
                interactuable, i is not None, malla, m is not None)})
            continue
        ot("set_properties", {"instance": i, "values": json.dumps(
            {"ItemAlRecoger": {"refPath": ITEMS + "/" + item + "." + item}})})
        ot("set_properties", {"instance": i, "values": json.dumps(
            {"MallaMundo": {"refPath": m["refPath"]}})})
        ot("set_properties", {"instance": i, "values": json.dumps({"CantidadItem": cuantos})})
        leido = json.loads(ot("get_properties", {"instance": i, "properties": [
            "ItemAlRecoger", "MallaMundo", "CantidadItem", "Verbo"]}))
        out["enlaces"].append({interactuable: {
            k: (str(leido[k]).split("/")[-1].rstrip("'}") if "/" in str(leido[k]) else leido[k])
            for k in leido}})

    if directo:
        ast("save_assets", {"asset_paths": [z["asset"]]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["mapa_sucio"] = ast("is_dirty", {"asset_path": z["asset"]})
    return out
