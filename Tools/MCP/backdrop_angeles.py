# -*- coding: utf-8 -*-
import json

# Importa la panoramica nueva del cielo (montanas, cascadas y coro de angeles) y
# la deja lista para colgarla del `SkyDomeMesh`.
#
# ### NADA DE LO QUE YA HAY SE TOCA
#
# El backdrop actual es una cadena de tres piezas:
#   SkyDomeMesh -> M_DA_Panorama360 -> T_DA_Malkuth_Panorama360
# y `M_DA_Panorama360` **solo lo usa el maestro** (comprobado buscando referencias
# por todo `Content`). Aun asi no se reimporta encima ni se reapunta el material
# viejo: se crean una textura y un material NUEVOS. Volver atras es devolverle al
# `SkyDomeMesh` el material de antes, un clic, sin haber perdido nada.
#
# **Por que no vale un Material Instance**, que seria lo natural: el material
# original lleva un `MaterialExpressionTextureSample` **normal, no un parametro**,
# asi que no hay nada que sobreescribir desde una instancia. Comprobado leyendo el
# .uasset: un solo nodo TextureSample, `MSM_Unlit`, `BLEND_Opaque`.
#
# ### LOS AJUSTES SE COPIAN DEL ORIGINAL, NO SE INVENTAN
#
# Salen del binario de `T_DA_Malkuth_Panorama360`: **sRGB, TC_Default,
# TEXTUREGROUP_World y TA_Wrap en las dos direcciones**. El `TA_Wrap` es el que
# hace que el borde izquierdo de la panoramica empalme con el derecho al envolver
# el domo -- y por eso la costura importa tanto.
#
# ### AVISO DE RESOLUCION
#
# El fichero se llama "8k" pero mide **1774 x 887**, no 8192 x 4096 como la que
# sustituye. La proporcion 2:1 es correcta, pero sobre un domo de 360 grados eso
# es **medio pixel por grado** frente a los ~2,3 de la actual. Sirve para juzgar
# composicion y color; para nitidez, no. Se importa a peticion de Angel, para ver.

CARPETA_TEX = "/Game/DarkAngels/Textures/Backdrops"
NOMBRE_TEX = "T_DA_Malkuth_Panorama360_Angeles2"
TEX = CARPETA_TEX + "/" + NOMBRE_TEX
ORIGEN = ("D:/Game Projects/Dark Angels/World Assets/Malkuth/backdrops/"
          "montanias cascadas angeles2.png")

# Copiados del original.
CARPETA_MAT = "/Game/DarkAngels/Materials/Malkuth"
NOMBRE_MAT = "M_DA_Panorama360_Angeles"
MAT = CARPETA_MAT + "/" + NOMBRE_MAT

AJUSTES = {"SRGB": True, "CompressionSettings": "TC_Default",
           "LODGroup": "TEXTUREGROUP_World",
           "AddressX": "TA_Wrap", "AddressY": "TA_Wrap"}


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def tx(t, a):
    return call("editor_toolset.toolsets.texture.TextureTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def mt(t, a):
    return call("editor_toolset.toolsets.material.MaterialTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes"}
    out = {}

    if ast("exists", {"path": TEX}):
        out["textura"] = "ya estaba"
    else:
        r = tx("import_file", {"folder_path": CARPETA_TEX,
                               "asset_name": NOMBRE_TEX,
                               "source_file": ORIGEN})
        out["textura"] = "importada " + str(r)

    inst = {"refPath": TEX + "." + NOMBRE_TEX}
    # Un campo por llamada: el setter aplica el primero y aqui se mezclan bool y enums.
    for k in AJUSTES:
        ot("set_properties", {"instance": inst, "values": json.dumps({k: AJUSTES[k]})})

    ast("save_assets", {"asset_paths": [TEX]})

    # --- releer del asset, que el `true` de estas APIs solo dice "acepte la llamada" ---
    out["tamano"] = str(tx("get_size", {"texture": inst}))
    out["ajustes"] = json.loads(ot("get_properties",
                                   {"instance": inst,
                                    "properties": sorted(AJUSTES.keys())}))
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": TEX})

    # --- el material, unlit y opaco como el original ---
    if ast("exists", {"path": MAT}):
        out["material"] = "ya estaba"
    else:
        mt("create_material", {"folder_path": CARPETA_MAT, "asset_name": NOMBRE_MAT})
        out["material"] = "creado"
    mref = {"refPath": MAT + "." + NOMBRE_MAT}
    # `TwoSided` NO es un adorno: el domo es una esfera que se mira DESDE DENTRO,
    # y sin el Unreal descarta las caras interiores y el cielo sale **negro**. Es la
    # unica propiedad en la que el material nuevo se diferenciaba del viejo, y bastaba
    # para romperlo. Comparar el original campo a campo lo canto en un segundo.
    for k, v in (("ShadingModel", "MSM_Unlit"), ("BlendMode", "BLEND_Opaque"),
                 ("TwoSided", True)):
        ot("set_properties", {"instance": mref, "values": json.dumps({k: v})})

    # Un solo TextureSample, como el material viejo. Si ya hay uno, se reutiliza:
    # anadir otro dejaria el grafo con dos nodos y el segundo sin conectar.
    muestra = None
    for e in mt("get_expressions", {"material_or_function": mref}):
        if "TextureSample" in e["refPath"]:
            muestra = e
    if muestra is None:
        muestra = mt("add_expression", {
            "material_or_function": mref,
            "expression_class": {"refPath": "/Script/Engine.MaterialExpressionTextureSample"},
            "x": -400, "y": 0})
    ot("set_properties", {"instance": muestra,
                          "values": json.dumps({"Texture": {"refPath": TEX + "." + NOMBRE_TEX}})})

    # El nombre de la salida se PREGUNTA, no se supone.
    salidas = [str(x) for x in mt("get_expression_output_names", {"expression": muestra})]
    out["salidas"] = salidas
    salida = "RGB" if "RGB" in salidas else salidas[0]
    # Unlit: la imagen va al Emissive, que es lo unico que dibuja.
    mt("connect_to_output", {"expression": muestra, "output_name": salida,
                             "material_property": "MP_EmissiveColor"})
    mt("recompile", {"material_or_function": mref})
    ast("save_assets", {"asset_paths": [MAT]})

    # --- colgarlo del domo ---
    domo = None
    for a in sc("find_actors", {"name": "SkyDomeMesh", "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == "SkyDomeMesh":
            domo = a
    if domo is None:
        return dict(out, error="no aparece SkyDomeMesh")
    comp = at("get_components", {"actor": domo})[0]
    ot("set_properties", {"instance": comp, "values": json.dumps(
        {"OverrideMaterials": [{"refPath": MAT + "." + NOMBRE_MAT}]})})
    ast("save_assets", {"asset_paths": ["/Game/DarkAngels/Maps/L_DA_Malkuth_Master"]})

    # --- releer del actor, no del script ---
    out["domo_material"] = str(json.loads(ot("get_properties",
        {"instance": comp, "properties": ["OverrideMaterials"]}))["OverrideMaterials"])
    out["expresiones"] = [str(e["refPath"].split(".")[-1])
                          for e in mt("get_expressions", {"material_or_function": mref})]
    return out
