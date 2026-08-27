# Crea el blueprint BP_DA_DestelloDescarte (hijo de Actor) si no existe.
# Idempotente. La logica la escribe descarte_destello.py despues.
#   node ue.mjs py descarte_destello_crear.py
import unreal
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_DestelloDescarte"
if unreal.EditorAssetLibrary.does_asset_exist(RUTA):
    print("ya existia:", RUTA)
else:
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", unreal.Actor)
    a = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BP_DA_DestelloDescarte", "/Game/DarkAngels/Blueprints/Combat",
        unreal.Blueprint, f)
    unreal.EditorAssetLibrary.save_asset(RUTA)
    print("creado:", a)
print("existe ahora:", unreal.EditorAssetLibrary.does_asset_exist(RUTA))
