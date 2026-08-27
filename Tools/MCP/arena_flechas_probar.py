# -*- coding: utf-8 -*-
#
# PRUEBA EN PIE DE LAS FLECHAS EN LA INSTANTANEA (lo que monta `arena_flechas.py`).
#
#   node ue.mjs py arena_flechas_probar.py     <- CON PIE YA ARRANCADO
#
# No arranca PIE por su cuenta a proposito: arrancarlo pide el sandbox
# (`EditorAppToolset.StartPIE`) y esto necesita la API `unreal` entera, y son dos
# modos distintos de `ue.mjs`. La secuencia completa son tres llamadas:
#
#   1. `node ue.mjs script <arrancar PIE>`   (StartPIE, warmupSeconds 8)
#   2. `node ue.mjs py arena_flechas_probar.py`
#   3. `node ue.mjs script <parar PIE>`      (StopPIE)
#
# ### QUE MIDE
#
# Que morir y reintentar NO te quita flechas: pone 17, toma la instantanea, las
# gasta a 3, reinicia y cuenta. Tiene que devolver 17.
#
# Corrido el 2026-08-26 sobre `L_Forja_romper-la-linea`:
#
#     pawn BP_Malakh_DCS_C, DbgEstadoArma -> ('', '', '143.400123', 'SEAL BREAK')
#     flechas de partida: 30
#     puestas a 17     -> 17
#     FlechasAlSellar  -> 17
#     gastadas a 3     -> 3
#     tras reiniciar   -> 17
#     VEREDICTO: BIEN, devuelve las 17
#
# ### LAS FIRMAS QUE NO SON LAS QUE PARECEN
#
#   - `RemoveItem` pide TRES argumentos —`(item, bRemoveAll, amount)`— aunque el
#     DSL del grafo solo enseñe dos. Con dos revienta con un TypeError.
#   - El `Amount` del `FStoredItem` NO se lee como `.amount` de python: hay que
#     pedirlo con `get_editor_property("amount")`.
#   - El item de las flechas NO sale con `EditorAssetLibrary.load_asset` (devuelve
#     None, sin avisar): es un Object Item, y se coge con `unreal.load_object`.
#     Si te lo comes, `FindItem` recibe None y contesta `(False, -1)` — o sea,
#     "no tienes flechas", que parece un fallo del codigo y no lo es.
#
# ### Y UNA COMPROBACION QUE NO ES DE FLECHAS
#
# La primera linea mira si el pawn responde a `DbgEstadoArma`. Si NO responde, el
# nivel esta spawneando un pawn que no es el nuestro y no estas probando nada de
# Dark Angels — ni la espada base, ni el ciclo de arma temporal. En los niveles de
# la Forja el pawn es `BP_Malakh_DCS_C` y si responde.

import unreal

FLECHA = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
          "Instances/DA_ElvenArrow.DA_ElvenArrow")
ARENA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena_C"
ESPERADO = 17
GASTADAS = 3

out = []
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
inv = next(c for c in pawn.get_components_by_class(unreal.ActorComponent)
           if c.get_class().get_name() == "BP_InventoryComponent_C")
arenas = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, ARENA))
item = unreal.load_object(None, FLECHA)

try:
    out.append("pawn %s, DbgEstadoArma -> %r"
               % (pawn.get_class().get_name(), pawn.call_method("DbgEstadoArma", ())))
except Exception as e:
    out.append("AVISO: el pawn %s NO tiene DbgEstadoArma (%s). No es el de Dark Angels."
               % (pawn.get_class().get_name(), e))


def cuantas():
    encontrada, i = inv.call_method("FindItem", (item,))
    if not encontrada:
        return 0
    return inv.call_method("GetItemAtIndex", (i,)).get_editor_property("amount")


def poner(n):
    inv.call_method("RemoveItem", (item, True, 0))
    if n > 0:
        inv.call_method("AddItem", (item, n))
    return cuantas()


if not arenas:
    out.append("NO HAY NINGUNA BP_DA_Arena en el nivel: esta prueba no aplica aqui.")
else:
    arena = arenas[0]
    out.append("flechas de partida: %d" % cuantas())
    out.append("puestas a %-2d     -> %d" % (ESPERADO, poner(ESPERADO)))
    arena.call_method("TomarInstantanea", ())
    out.append("FlechasAlSellar  -> %s" % arena.get_editor_property("FlechasAlSellar"))
    out.append("gastadas a %-2d    -> %d" % (GASTADAS, poner(GASTADAS)))
    arena.call_method("ReiniciarEncuentro", ())
    tras = cuantas()
    out.append("tras reiniciar   -> %d" % tras)
    out.append("VEREDICTO: %s" % ("BIEN, devuelve las %d" % ESPERADO if tras == ESPERADO
                                  else "MAL, esperaba %d y hay %d" % (ESPERADO, tras)))
print("\n".join(out))
