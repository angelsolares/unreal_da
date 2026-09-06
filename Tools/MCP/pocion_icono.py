# El icono de la pocion salia con un cuadro negro detras: T_HealthPotion (DCS, 159x159)
# no tiene canal alfa y el fondo esta pintado de negro dentro de la propia textura.
#
# Nuestra copia con transparencia es /Game/DarkAngels/UI/T_DA_Icono_Pocion y SI viaja en
# el repo. Lo que no viaja es el puntero: DA_HealthPotion es del pack de pago y esta en
# .gitignore, asi que en un clon limpio hay que volver a apuntarlo con este guion.
#
#   node ue.mjs py Tools/MCP/pocion_icono      (sin extension: un token con forma
#   nombre-punto-py en cualquier sitio hace que el MCP rechace el fichero sin traza)
#
# Como se hizo la textura, por si hay que rehacerla: se exporta la de DCS a TGA con
# TextureExporterTGA, se marca como fondo todo lo que se alcanza por inundacion 4-conexa
# DESDE EL BORDE pasando solo por pixeles de luminancia < 24, y se pone alfa 0 ahi. La
# inundacion importa: keyear por luminancia a secas se come los contornos oscuros del
# dibujo, que no tocan el borde. Un pixel de suavizado en la frontera.
import unreal

ITEM = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/Instances/DA_HealthPotion"
ICONO = "/Game/DarkAngels/UI/T_DA_Icono_Pocion"

it = unreal.load_asset(ITEM)
tex = unreal.load_asset(ICONO)
if it is None:
    print("!! no esta el item de DCS:", ITEM)
elif tex is None:
    print("!! no esta nuestro icono:", ICONO)
else:
    st = it.get_editor_property("Item")
    antes = st.get_editor_property("Image")
    if antes is not None and antes.get_path_name().startswith(ICONO):
        print("ya apuntaba a", antes.get_name())
    else:
        st.set_editor_property("Image", tex)
        it.set_editor_property("Item", st)
        print("guardado:", unreal.EditorAssetLibrary.save_asset(ITEM, only_if_is_dirty=False))
    # releer: los structs por MCP se escriben a medias sin dar error
    st2 = unreal.load_asset(ITEM).get_editor_property("Item")
    print("releido: Image =", st2.get_editor_property("Image").get_path_name())
    print("         Name  =", st2.get_editor_property("Name"))
