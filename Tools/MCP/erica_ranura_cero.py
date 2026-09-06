# Las tres mallas de brezo de Flowering_Shrubs traen la ranura 0 SIN material
# (sale "Material #78" con el WorldGridMaterial del motor), y esa ranura la usa la
# seccion 0 del LOD0: en Malkuth son 75 arbustos con un trozo pintado de cuadros grises.
#
# El pack es de Fab y esta en .gitignore, asi que el arreglo no se puede subir: se
# regenera con este guion, igual que frutales_colision con los cerezos.
#
#   node ue.mjs py Tools/MCP/erica_ranura_cero      (sin extension: un token con forma
#   nombre-punto-py en cualquier parte del fichero hace que el MCP lo rechace sin traza)
#
# La eleccion de MI_Erica_Leaf es criterio, no dato: el pack solo trae cinco materiales
# de Erica y los otros cuatro ya estan puestos (Bark, Leaf, Flower, FlowerCap), asi que
# la seccion huerfana no tiene material propio. La hoja es la superficie mas abundante
# del arbusto y es la que menos canta si la geometria resultara ser ramilla. Cambiar a
# MI_Erica_Bark es una linea.
import unreal

MALLAS = ["/Game/Flowering_Shrubs/Meshes/SM_Erica_Multiflora_01P",
          "/Game/Flowering_Shrubs/Meshes/SM_Erica_Multiflora_01W",
          "/Game/Flowering_Shrubs/Meshes/SM_Erica_Multiflora_02"]
RELLENO = "/Game/Flowering_Shrubs/Materials/MI_Erica_Leaf"


def run():
    relleno = unreal.load_asset(RELLENO)
    if relleno is None:
        print("!! no encuentro", RELLENO)
        return
    for ruta in MALLAS:
        m = unreal.load_asset(ruta)
        if m is None:
            print("  no existe", ruta)
            continue
        mats = m.get_editor_property("static_materials")
        s0 = mats[0]
        act = s0.get_editor_property("material_interface")
        if act is not None and "WorldGridMaterial" not in act.get_name():
            print("  %-28s ranura 0 ya es %s" % (m.get_name(), act.get_name()))
            continue
        s0.set_editor_property("material_interface", relleno)
        s0.set_editor_property("material_slot_name", "Leaf_Extra")
        mats[0] = s0
        m.set_editor_property("static_materials", mats)
        ok = unreal.EditorAssetLibrary.save_asset(ruta, only_if_is_dirty=False)
        print("  %-28s ranura 0 -> %s  guardado=%s" % (m.get_name(), relleno.get_name(), ok))
    print("-- releido")
    for ruta in MALLAS:
        m = unreal.load_asset(ruta)
        fila = []
        for i, s in enumerate(m.get_editor_property("static_materials")):
            mi = s.get_editor_property("material_interface")
            fila.append("%d:%s" % (i, mi.get_name() if mi else "None"))
        print("  %-28s %s" % (m.get_name(), " ".join(fila)))


run()
