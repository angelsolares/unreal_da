import json

# Deja un material recien importado de Tripo como el de la puerta del Claro,
# que es el patron bueno. Es idempotente: se puede relanzar sin duplicar nodos.
#
# El importador de Tripo SIEMPRE saca lo mismo mal:
#   - cablea el mapa de RUGOSIDAD a `Metallic` y deja `Roughness` vacio
#   - declara `SamplerType = Color` en un mapa de datos **y** deja la textura en
#     sRGB / TC_Default. Hay que corregir LAS DOS COSAS: con solo una, el
#     material no compila ("Sampler type is Masks, should be Color")
#   - no importa el mapa metallic aunque venga dentro del .fbm
#
# Con el material sin compilar la miniatura sale como una bola gris lisa, que es
# el material por defecto. Esa es la senal para detectarlo de un vistazo.

PROPS = "/Game/DarkAngels/Environment/Props"
RAIZ = "D:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/ArtSource/Downloaded/Tripo/"

PIEZAS = [
    {
        "material": "tripo_mat_2b6fd363",
        "metallic_nombre": "puerta_yesod_metallic",
        "metallic_fichero": RAIZ + "puerta_yesod/tripo_convert_2b6fd363-fe95-4074-8e12-8aa287128a8c.fbm/gothic_cathedral_3d_model_metallic.JPEG",
        # Piedra de templo, nada de metal. A 2048 porque es un landmark que se
        # mira de lejos y de cerca.
        "atenuacion": 0.15,
        "max_textura": 2048,
    },
]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def leer(inst, prop):
    return json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                           {"instance": inst, "properties": [prop]}))[prop]


def poner(inst, valores):
    call("editor_toolset.toolsets.object.ObjectTools.set_properties",
         {"instance": inst, "values": json.dumps(valores)})


def entrada(mat, prop):
    r = call("editor_toolset.toolsets.material.MaterialTools.get_property_input",
             {"material": mat, "material_property": prop})
    e = r["expression"]
    return None if str(e) == "None" else e["refPath"].split(":")[-1]


def run():
    salida = {}
    for p in PIEZAS:
        mat = {"refPath": PROPS + "/" + p["material"] + "." + p["material"]}
        nodo = lambda n: {"refPath": mat["refPath"] + ":" + n}
        pasos = []

        rug = nodo("MaterialExpressionTextureSample_1")
        rug_tex = {"refPath": leer(rug, "Texture")["refPath"]}

        # 1. La textura de datos y el nodo tienen que ir de la mano.
        poner(rug_tex, {"SRGB": False, "CompressionSettings": "TC_Masks",
                        "MaxTextureSize": p["max_textura"]})
        poner(rug, {"SamplerType": "SAMPLERTYPE_Masks"})
        pasos.append("rugosidad: textura a TC_Masks/sRGB off y nodo a Masks")

        # 2. La rugosidad a su sitio, por el canal R (es escala de grises).
        if entrada(mat, "MP_Roughness") is None:
            call("editor_toolset.toolsets.material.MaterialTools.disconnect_from_output",
                 {"material": mat, "material_property": "MP_Metallic"})
            call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
                 {"expression": rug, "output_name": "R", "material_property": "MP_Roughness"})
            pasos.append("rugosidad -> MP_Roughness (canal R)")

        # 3. El metallic de verdad, atenuado. Solo si no se hizo ya.
        if entrada(mat, "MP_Metallic") is None or "Multiply" not in str(entrada(mat, "MP_Metallic")):
            existentes = call("editor_toolset.toolsets.asset.AssetTools.find_assets",
                              {"folder_path": PROPS, "name": p["metallic_nombre"], "recursive": False})
            if existentes:
                tex = {"refPath": existentes[0] + "." + p["metallic_nombre"]}
            else:
                tex = call("editor_toolset.toolsets.texture.TextureTools.import_file",
                           {"folder_path": PROPS, "asset_name": p["metallic_nombre"],
                            "source_file": p["metallic_fichero"]})[0]
            poner({"refPath": tex["refPath"]}, {"SRGB": False, "CompressionSettings": "TC_Masks",
                                                "MaxTextureSize": p["max_textura"]})

            met = call("editor_toolset.toolsets.material.MaterialTools.add_expression",
                       {"material_or_function": mat,
                        "expression_class": {"refPath": "/Script/Engine.MaterialExpressionTextureSample"},
                        "x": -900, "y": 300})
            poner(met, {"Texture": {"refPath": tex["refPath"]}, "SamplerType": "SAMPLERTYPE_Masks"})

            mul = call("editor_toolset.toolsets.material.MaterialTools.add_expression",
                       {"material_or_function": mat,
                        "expression_class": {"refPath": "/Script/Engine.MaterialExpressionMultiply"},
                        "x": -500, "y": 300})
            poner(mul, {"ConstB": p["atenuacion"]})
            call("editor_toolset.toolsets.material.MaterialTools.connect_expressions",
                 {"from_expression": met, "from_output_name": "R",
                  "to_expression": mul, "to_input_name": "A"})
            call("editor_toolset.toolsets.material.MaterialTools.connect_to_output",
                 {"expression": mul, "output_name": "", "material_property": "MP_Metallic"})
            pasos.append("metallic -> Multiply x" + str(p["atenuacion"]) + " -> MP_Metallic")

        # 4. Acotar el peso: la VRAM ya va muy pasada.
        for n in ("MaterialExpressionTextureSample_0", "MaterialExpressionTextureSample_2"):
            t = leer(nodo(n), "Texture")
            poner({"refPath": t["refPath"]}, {"MaxTextureSize": p["max_textura"]})
        pasos.append("MaxTextureSize " + str(p["max_textura"]))

        call("editor_toolset.toolsets.material.MaterialTools.recompile",
             {"material_or_function": mat})
        pasos.append("recompilado sin error")

        salida[p["material"]] = {
            "pasos": pasos,
            "salidas": {k: entrada(mat, k) for k in
                        ["MP_BaseColor", "MP_Metallic", "MP_Roughness", "MP_Normal"]},
        }

    return salida
