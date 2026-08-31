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
del pack: 653 vertices, UN SOLO LOD, cero colision, y su material `Sword` **no
tiene ninguna textura** -- es color plano (azul). Vale para juzgar si el espadon
convence; no vale para produccion.

Lo que hereda del hacha y NO se ha tocado: stats, dano, peso e icono. Solo cambia
lo que se ve.
"""
import unreal

DEST    = "/Game/DarkAngels/Blueprints/Items"
DI_ORIG = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/DisplayedItems/Instances/BP_DI_GreatAxe"
IT_ORIG = "/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/Instances/DA_GreatAxe"
DI_NEW  = DEST + "/BP_DI_DA_Espadon"
IT_NEW  = DEST + "/DA_DA_Espadon"
MALLA   = "/Game/Two_Handed_Sword/Demo/Mannequin_UE4/Character/Mesh/2Handed_Sword3"


def pasada():
    eal = unreal.EditorAssetLibrary
    if unreal.EditorAssetLibrary.load_asset(MALLA) is None:
        raise RuntimeError("no esta el Two-Handed Sword Pack: " + MALLA)

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
    return fallos


if __name__ == "__main__":
    pasada()
    fallos = verificar()
    print("[OK] espadon provisional montado" if not fallos else "[FALLO]\n   " + "\n   ".join(fallos))
