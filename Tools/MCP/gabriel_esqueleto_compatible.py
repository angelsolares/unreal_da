# -*- coding: utf-8 -*-
"""Gabriel deja de esperar en cuclillas: le abre el catalogo de animaciones de DCS.

    execute_python_code(code=open("Tools/MCP/gabriel_esqueleto_compatible.py").read())

EL PROBLEMA. `SK_DA_Gabriel` usa el esqueleto del GiantBoss
(`/Game/GiantBossProject/Demo/.../SK_Mannequin`), y ese pack **solo trae
animaciones de combate**: idle, andar, correr, ataques y muerte. Su "reposo" es
una CUCLILLA DE PELEA, que para un heraldo que te para en el Elevador a
preguntarte quien eres esta mal. Las de hablar de Cassiel y Sariel no valen:
estan en `SK_DA_Cassiel_Skeleton` y `SK_DA_Sariel_Skeleton`.

LA SALIDA ES LA DE LA CASA, Y YA ESTABA INVENTADA. El esqueleto de DCS ya lista
como COMPATIBLES los del Spear Pack y el Throwing Pack -- asi es como las
animaciones de la Lanza suenan sobre Malakh sin retargetear nada. Se hace lo
mismo al reves: se le anade a Gabriel el de DCS como compatible, y con eso puede
reproducir cualquier animacion del juego.

Los dos son el mismo rig de mannequin de UE5: 208 huesos contra 211 y **los
mismos cinco perfiles de mezcla** (UpperBodyMask, LowerBodyMask, FastFeet,
LeftFingersMask, UpperBodyLowerBodySplit). Comprobado en juego: con
`Anim_U_Idle` Gabriel pasa a medir 278 cm en vez de 260 -- esta DE PIE, no
agachado.

POR QUE ESTO ES UN GUION Y NO UN ASSET DEL REPO: la marca de compatibilidad se
escribe sobre el ESQUELETO DEL GIANTBOSS, que es de pago y esta en .gitignore.
Si se reinstala el pack, se pierde, y Gabriel vuelve a las cuclillas.

Lo que SI viaja en git y no hace falta rehacer: `BP_DA_GabrielHeraldo` y los dos
sub-mapas con los actores colocados. Lo unico que se pierde al reinstalar es esta
marca -- y de rebote las referencias a `Anim_U_Idle`, que vive en DCS.
"""
import unreal

GABRIEL = "/Game/GiantBossProject/Demo/Characters/Mannequins/Meshes/SK_Mannequin"
DCS     = "/Game/DynamicCombatSystem/Demo/Meshes/Mannequins/Meshes/SK_Mannequin"
IDLE    = "/Game/DynamicCombatSystem/DCS/Animations/Unarmed/Locomotion/Anim_U_Idle"


def pasada():
    eal = unreal.EditorAssetLibrary
    for p in (GABRIEL, DCS, IDLE):
        if not eal.does_asset_exist(p):
            raise RuntimeError("falta " + p)
    if DCS + ".SK_Mannequin" not in [str(c) for c in unreal.SkeletonService.get_compatible_skeletons(GABRIEL)]:
        if not unreal.SkeletonService.add_compatible_skeleton(GABRIEL, DCS):
            raise RuntimeError("no pude marcar el esqueleto como compatible")
        eal.save_asset(GABRIEL)


def verificar():
    """Se relee del disco: el `True` de add_compatible_skeleton no es prueba."""
    fallos = []
    comp = [str(c) for c in unreal.SkeletonService.get_compatible_skeletons(GABRIEL)]
    if not any("DynamicCombatSystem" in c for c in comp):
        fallos.append("el esqueleto de Gabriel no quedo compatible con el de DCS: %s" % comp)

    info = unreal.SkeletonService.get_skeleton_info(GABRIEL)
    if info.compatible_skeleton_count < 1:
        fallos.append("compatible_skeleton_count sigue en %d" % info.compatible_skeleton_count)

    # y que los dos actores colocados sigan apuntando al idle de pie
    eal = unreal.EditorAssetLibrary
    idle = eal.load_asset(IDLE)
    for mapa, etiqueta in (("Elevador", "Elev_Gabriel"), ("Yesod", "Yesod_Gabriel")):
        pass  # los actores viven en los _Sub; se comprueban abriendo el mapa, no aqui
    return fallos


if __name__ == "__main__":
    pasada()
    f = verificar()
    print("[OK] Gabriel puede usar las animaciones de DCS" if not f else "[FALLO]\n   " + "\n   ".join(f))
