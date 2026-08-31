# -*- coding: utf-8 -*-
"""Crea el arma provisional del Espadon: item + arma visible.

    execute_python_code(code=open("Tools/MCP/espadon_item.py").read())

POR QUE UN GUION: los dos assets son COPIAS de assets de DCS (de pago), asi que
no viajan en el repo. Misma regla que BT_DA_Guerrero y DT_DA_2H_Montages.

EN DCS UN ARMA SON DOS PIEZAS:
  - el ITEM (`DA_*`, un BP_DA_Item_MeleeWeapon): stats y la clase del arma visible
  - el ARMA VISIBLE (`BP_DI_*`): el actor con la malla que se engancha a la mano

Antes de esto el Espadon equipaba `DA_GreatAxe`, o sea peleaba con un HACHA
mientras sonaban animaciones de espadon. Ahora equipa una espada de verdad.

ES PROVISIONAL, Y SE NOTA. La malla `2Handed_Sword3` sale de la carpeta *Demo*
del pack: 653 vertices, UN SOLO LOD y cero colision. Vale para juzgar si el
espadon convence; no vale para produccion.

Lo que hereda del hacha y NO se ha tocado: stats, dano, peso e icono. Solo cambia
lo que se ve.

EL MATERIAL, Y POR QUE NO SE PUDO REUTILIZAR EL DE LAS OTRAS ARMAS
------------------------------------------------------------------
El pack **no trae ninguna textura de espada**: su material `Sword` es color plano
(azul) y lo unico texturizado que incluye son maniquies. Habia que vestirla.

Las armas de la casa usan `M_DA_ArmaDivina` con instancias que llevan los ATLAS
de DCS (`MI_DA_ArmaSet1` = T_Weapon_Set1, `MI_DA_ArmaSet2` = T_Weapon_Set2).
**Probado y descartado:** esos atlas estan pintados para las UV de SM_SteelSword
y SM_GreatAxe; sobre el espadon la hoja sale a parches naranjas y negros.

Asi que `MI_DA_ArmaEspadon` usa un BaseColor LISO y deja que el maestro ponga el
metal y la veta. Los tres valores salieron de mirarlo en juego contra el hacha,
que es el liston:

    BaseColor        /Engine/EngineMaterials/DefaultDiffuse   gris medio
    RugosidadLimpia  0,38   (el defecto 0,32 espejeaba de mas)
    el resto         por defecto del maestro

Descartados por medida, no por gusto: `WhiteSquareTexture` deja una hoja blanca
que canta al lado del hacha, y `/Engine/EngineResources/Black` la vuelve invisible
contra el personaje.

OJO: el material se escribe **sobre la malla del pack**, que es la unica forma de
que se vea tambien cuando el arma la lleva un ENEMIGO --el override en
`BP_DI_DA_Espadon` solo cubre a quien instancie ese blueprint--. Si se reinstala
el pack desde Fab se pierde, igual que el `enable_root_motion` de
`espadon_montages.py`, y hay que volver a pasar esto.
"""
import unreal

DEST    = "/Game/DarkAngels/Blueprints/Items"
DI_ORIG = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/DisplayedItems/Instances/BP_DI_GreatAxe"
IT_ORIG = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/Instances/DA_GreatAxe"
DI_NEW  = DEST + "/BP_DI_DA_Espadon"
IT_NEW  = DEST + "/DA_DA_Espadon"
MALLA   = "/Game/Two_Handed_Sword/Demo/Mannequin_UE4/Character/Mesh/2Handed_Sword3"

MI_BASE = "/Game/DarkAngels/Weapons/Materials/MI_DA_ArmaSet1"
MI_ESP  = "/Game/DarkAngels/Weapons/Materials/MI_DA_ArmaEspadon"
TEXTURA = "/Engine/EngineMaterials/DefaultDiffuse"
RUGOSID = 0.38


def _material():
    """Crea `MI_DA_ArmaEspadon` si falta y se lo pone a la malla del pack.

    El asset SI viaja en el repo (`/Game/DarkAngels/Weapons/` no esta ignorado);
    lo que no viaja es la asignacion sobre la malla, que es de pago. Por eso se
    rehace aqui aunque la instancia ya exista.
    """
    eal = unreal.EditorAssetLibrary
    ml  = unreal.MaterialEditingLibrary
    if not eal.does_asset_exist(MI_ESP):
        if eal.duplicate_asset(MI_BASE, MI_ESP) is None:
            raise RuntimeError("no pude crear " + MI_ESP)
    mi = eal.load_asset(MI_ESP)
    tex = eal.load_asset(TEXTURA)
    if tex is None:
        raise RuntimeError("no encuentro la textura lisa: " + TEXTURA)
    ml.set_material_instance_texture_parameter_value(mi, "BaseColor", tex)
    ml.set_material_instance_scalar_parameter_value(mi, "RugosidadLimpia", RUGOSID)
    eal.save_asset(MI_ESP)

    malla = eal.load_asset(MALLA)
    malla.set_material(0, eal.load_asset(MI_ESP))
    eal.save_asset(MALLA)


def pasada():
    eal = unreal.EditorAssetLibrary
    if unreal.EditorAssetLibrary.load_asset(MALLA) is None:
        raise RuntimeError("no esta el Two-Handed Sword Pack: " + MALLA)
    _material()

    for origen, nuevo in ((DI_ORIG, DI_NEW), (IT_ORIG, IT_NEW)):
        if not eal.does_asset_exist(nuevo):
            if eal.duplicate_asset(origen, nuevo) is None:
                raise RuntimeError("no pude duplicar " + origen)

    # la malla va en la PLANTILLA del componente del SCS, no en el CDO: el CDO no
    # instancia los componentes del SCS y leerlo ahi da cero.
    if not unreal.BlueprintService.set_component_property(DI_NEW, "StaticMesh", "StaticMesh", MALLA):
        raise RuntimeError("no entro la malla en BP_DI_DA_Espadon")
    unreal.BlueprintEditorLibrary.compile_blueprint(eal.load_asset(DI_NEW))

    item = eal.load_asset(IT_NEW)
    item.set_editor_property("DisplayedItem", eal.load_asset(DI_NEW).generated_class())
    eal.save_asset(DI_NEW)
    eal.save_asset(IT_NEW)


def verificar():
    """Se relee del disco: el guardado miente en las dos direcciones."""
    eal = unreal.EditorAssetLibrary
    fallos = []
    v = unreal.BlueprintService.get_component_property(DI_NEW, "StaticMesh", "StaticMesh")
    if "2Handed_Sword3" not in str(v):
        fallos.append("el arma visible no lleva la malla del espadon: %s" % v)
    d = eal.load_asset(IT_NEW).get_editor_property("DisplayedItem")
    if d is None or d.get_name() != "BP_DI_DA_Espadon_C":
        fallos.append("el item no apunta al arma visible nueva: %s" % d)
    if not eal.load_asset(IT_NEW).get_editor_property("TwoHanded"):
        fallos.append("el item perdio TwoHanded, y de eso depende el enrutado de GetMontages")

    mats = [m.material_interface.get_name() if m.material_interface else "-"
            for m in eal.load_asset(MALLA).get_editor_property("static_materials")]
    if mats != ["MI_DA_ArmaEspadon"]:
        fallos.append("la malla del pack se quedo sin el material de la casa: %s" % mats)
    mi = eal.load_asset(MI_ESP)
    tex = [t.parameter_value.get_name() if t.parameter_value else "-"
           for t in mi.get_editor_property("texture_parameter_values")]
    if "DefaultDiffuse" not in tex:
        fallos.append("MI_DA_ArmaEspadon no quedo con el BaseColor liso: %s" % tex)
    rug = {str(s.parameter_info.name): s.parameter_value
           for s in mi.get_editor_property("scalar_parameter_values")}
    if abs(rug.get("RugosidadLimpia", -1) - RUGOSID) > 0.001:
        fallos.append("MI_DA_ArmaEspadon no quedo con la rugosidad medida: %s" % rug)
    return fallos


if __name__ == "__main__":
    pasada()
    fallos = verificar()
    print("[OK] espadon provisional montado" if not fallos else "[FALLO]\n   " + "\n   ".join(fallos))
