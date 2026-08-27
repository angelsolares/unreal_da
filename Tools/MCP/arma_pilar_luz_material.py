import unreal
#
# Crea/actualiza `MI_DA_PilarArma`, el material instance del pilar de luz de las
# armas en el suelo (§9). Lo usa `arma_pilar_luz.py`. Idempotente: si ya existe,
# solo reescribe los parametros. Relee los tres al final, que aqui el true miente.
#
# EL BRILLO EMPEZO EN 3 Y SALIO BLANCO. `M_DA_HazLuz` es ADITIVO: brillo x color
# por encima de 1 satura los tres canales y el "azul celeste" acaba siendo un
# tubo de neon blanco — se vio en la primera foto en juego. Con 1.1 el azul
# sobrevive y el pilar sigue leyendose a 25 m.
#   node ue.mjs py arma_pilar_luz_material.py
PADRE = "/Game/DarkAngels/Materials/M_DA_HazLuz.M_DA_HazLuz"
RUTA = "/Game/DarkAngels/Materials"
NOMBRE = "MI_DA_PilarArma"
COLOR = unreal.LinearColor(0.20, 0.50, 1.0, 1.0)
BRILLO, OPACIDAD = 1.1, 0.20

full = RUTA + "/" + NOMBRE
if unreal.EditorAssetLibrary.does_asset_exist(full):
    mi = unreal.load_object(None, full + "." + NOMBRE)
    print("ya existia:", full)
else:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(NOMBRE, RUTA, unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_object(None, PADRE))
    print("creado:", full)

unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "Color", COLOR)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Brillo", BRILLO)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Opacidad", OPACIDAD)
unreal.MaterialEditingLibrary.update_material_instance(mi)
unreal.EditorAssetLibrary.save_asset(full)

# RELEER, que aqui el true miente.
print("padre  :", mi.get_editor_property("parent").get_name())
print("Color  :", unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(mi, "Color"))
print("Brillo :", unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Brillo"))
print("Opacid.:", unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "Opacidad"))
