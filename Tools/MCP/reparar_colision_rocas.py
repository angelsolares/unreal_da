"""Devuelve la colision a las rocas de Megascans.

    import reparar_colision_rocas as r; r.reparar()

**Por que existe este fichero.** Varias mallas de Megascans vienen con la colision
"activada" pero **sin una sola primitiva simple**, y con `CollisionTraceFlag` en
`CTF_USE_DEFAULT`. La consulta de la capsula del jugador usa la colision SIMPLE, asi que
no encuentra nada: **el jugador atraviesa la roca**. En el editor todo parece correcto
--el actor dice QueryAndPhysics-- y por eso el defecto sobrevive a una inspeccion visual.

Se arregla poniendo la malla en `CTF_USE_COMPLEX_AS_SIMPLE`, que hace que las consultas
usen la malla de triangulos.

**Y por que hay que re-aplicarlo.** `Content/Megascans/` esta en el `.gitignore` --son
assets que cada uno descarga con su cuenta--, asi que el arreglo NO viaja en el repo. En
un clon nuevo, o si se reinstala el pack, hay que volver a ejecutar esto.

Descubierto el 2026-08-29 arreglando El Claro: la entrada y la salida estaban tapadas por
rocas y no se notaba porque se cruzaban andando.
"""
import unreal

MALLAS = [
    "/Game/Megascans/3D_Assets/QuarryCliff/SM_QuarryCliff_01",
    "/Game/Megascans/3D_Assets/QuarryCliff/SM_QuarryCliff_02",
    "/Game/Megascans/3D_Assets/QuarryCliff/SM_QuarryCliff_05",
    "/Game/Megascans/3D_Assets/AngkorWatTempleStones/SM_AngkorWatTempleStones",
    "/Game/Megascans/3D_Assets/MossyRocksA/SM_MossyRocksA",
]


def diagnostico():
    """Lista que mallas de la lista siguen sin colision util."""
    malas = []
    for ruta in MALLAS:
        sm = unreal.load_asset(ruta)
        if sm is None:
            print("FALTA  %s" % ruta)
            continue
        bs = sm.get_editor_property("BodySetup")
        ag = bs.get_editor_property("AggGeom")
        prims = (len(ag.get_editor_property("ConvexElems"))
                 + len(ag.get_editor_property("BoxElems"))
                 + len(ag.get_editor_property("SphereElems"))
                 + len(ag.get_editor_property("SphylElems")))
        flag = bs.get_editor_property("CollisionTraceFlag")
        ok = (flag == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE) or prims > 0
        print("%-6s %-34s primitivas=%d  %s" % ("OK" if ok else "MAL",
              ruta.rsplit("/", 1)[-1], prims, str(flag).split(".")[-1].rstrip(">")))
        if not ok:
            malas.append(ruta)
    return malas


def reparar():
    tocadas = []
    with unreal.ScopedEditorTransaction("Colision de rocas"):
        for ruta in MALLAS:
            sm = unreal.load_asset(ruta)
            if sm is None:
                continue
            bs = sm.get_editor_property("BodySetup")
            if bs.get_editor_property("CollisionTraceFlag") == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
                continue
            bs.set_editor_property("CollisionTraceFlag",
                                   unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            sm.modify(True)
            tocadas.append(ruta)
    # save_loaded_assets miente aqui; hay que guardar uno a uno y mirar la fecha del fichero
    import os
    raiz = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
    for ruta in tocadas:
        unreal.EditorAssetLibrary.save_asset(ruta, only_if_is_dirty=False)
        f = raiz + ruta.replace("/Game/", "") + ".uasset"
        print("guardada %-34s  existe en disco: %s" % (ruta.rsplit("/", 1)[-1], os.path.exists(f)))
    print("reparadas %d de %d" % (len(tocadas), len(MALLAS)))
    return tocadas


if __name__ == "__main__":
    reparar()
    diagnostico()
