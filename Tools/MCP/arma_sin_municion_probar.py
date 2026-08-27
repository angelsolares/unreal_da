# -*- coding: utf-8 -*-
#
# PRUEBA EN PIE DE «AGOTAR EL RECURSO NATURAL DEVUELVE LA ESPADA»
# (lo que monta `arma_sin_municion.py` — §3 y §12, criterio 1).
#
#   node ue.mjs py arma_sin_municion_probar.py    <- CON PIE YA ARRANCADO
#
# Igual que `arena_flechas_probar.py`, no arranca PIE por su cuenta: arrancarlo
# pide el sandbox y esto pide la API `unreal` entera, y son dos modos distintos
# de `ue.mjs`.
#
# ### POR QUE SON CUATRO LLAMADAS Y NO UNA
#
# **Porque hay que dejar pasar el tiempo, y aqui no se puede dormir.** El
# vigilante corre cada 0,5 s dentro del juego; un `sleep` en el script bloquea el
# hilo del editor y el temporizador no avanza. Lo que sí avanza es el juego entre
# una llamada MCP y la siguiente (100 ms a varios segundos), asi que la espera es
# **cortar el script y volver a entrar**. De ahi los PASOS: cada uno se lanza por
# separado, y el de despues comprueba lo que el de antes puso en marcha.
#
# ### LOS TRES CASOS, Y POR QUE LOS TRES
#
#   1. **Con flechas, el arco SE QUEDA.** Es el caso que demuestra que el
#      vigilante no dispara de mas. Medido a los 11,7 s con 12 flechas.
#   2. **A cero flechas, vuelve la espada** con motivo `AMMO OUT`. El caso.
#   3. **Con MUNICION INFINITA puesta NO te desarma**, y **el vigilante se rearma**
#      en la siguiente arma temporal. Los dos son decisiones escritas en la
#      cabecera de `arma_sin_municion.py`, asi que se prueban.
#
# Corrido entero el 2026-08-26 sobre `L_Forja_romper-la-linea`:
#
#     PASO 1  flechas a 12, arco dado    -> ('DA_ElvenBow', 'BP_DA_Item_RangeWeapon_C', '-0.0', 'SWAP')
#     PASO 2  a los 11,7 s con 12        -> sigue 'DA_ElvenBow'          <- no dispara de mas
#     PASO 3  con las flechas a 0        -> arma='' motivo='AMMO OUT'
#             en la mano                 -> ['BP_DI_Potion_C', 'BP_DI_SteelSword_C']
#     PASO 4  con municion infinita      -> sigue 'DA_ElvenBow', flechas 99
#     PASO 5  segundo arco, flechas a 0  -> arma='' motivo='AMMO OUT'    <- se rearma
#
# Las firmas raras del inventario (`RemoveItem` con tres argumentos, el `amount`
# por `get_editor_property`, el item por `load_object` y no `load_asset`) estan
# explicadas en la cabecera de `arena_flechas_probar.py`.

import unreal

FLECHA = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
          "Instances/DA_ElvenArrow.DA_ElvenArrow")
ARCO = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
        "Instances/DA_ElvenBow.DA_ElvenBow")

# CUAL de los cinco pasos se corre. Se edita esta linea y se relanza.
PASO = 1

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
inv = next(c for c in pawn.get_components_by_class(unreal.ActorComponent)
           if c.get_class().get_name() == "BP_InventoryComponent_C")
item = unreal.load_object(None, FLECHA)
out = []


def cuantas():
    hay, i = inv.call_method("FindItem", (item,))
    return inv.call_method("GetItemAtIndex", (i,)).get_editor_property("amount") if hay else 0


def poner(n):
    inv.call_method("RemoveItem", (item, True, 0))
    if n > 0:
        inv.call_method("AddItem", (item, n))
    return cuantas()


def estado():
    return pawn.call_method("DbgEstadoArma", ())


def en_la_mano():
    return [a.get_class().get_name() for a in pawn.get_attached_actors()]


if PASO == 1:
    out.append("flechas puestas a 12 -> %d" % poner(12))
    pawn.call_method("DarArmaTemporal", (ARCO,))
    out.append("arco dado -> %r" % (estado(),))
    out.append("AHORA: pon PASO = 2 y vuelve a lanzar.")

elif PASO == 2:
    a = estado()
    out.append("con %d flechas, %s s despues -> arma=%r" % (cuantas(), a[2], a[0]))
    out.append("  %s" % ("BIEN, el vigilante no dispara de mas" if a[0] == "DA_ElvenBow"
                         else "MAL, el arco se ha caido teniendo flechas"))
    out.append("flechas a 0 -> %d" % poner(0))
    out.append("AHORA: pon PASO = 3 y vuelve a lanzar.")

elif PASO == 3:
    arma, tipo, seg, motivo = estado()
    out.append("tras quedarse a cero -> arma=%r motivo=%r" % (arma, motivo))
    out.append("en la mano: %s" % en_la_mano())
    out.append("  %s" % ("BIEN, vuelve la espada y el motivo es AMMO OUT"
                         if arma == "" and motivo == "AMMO OUT"
                         else "MAL, arma=%r motivo=%r" % (arma, motivo)))
    pawn.call_method("AlternarMunicionInfinita", ())
    pawn.call_method("DarArmaTemporal", (ARCO,))
    out.append("municion infinita -> %s, y arco dado otra vez"
               % pawn.get_editor_property("MunicionInfinita"))
    out.append("AHORA: pon PASO = 4 y vuelve a lanzar.")

elif PASO == 4:
    a = estado()
    out.append("con municion infinita -> arma=%r flechas=%d" % (a[0], cuantas()))
    out.append("  %s" % ("BIEN, el debug no te desarma" if a[0] == "DA_ElvenBow"
                         else "MAL, el arco se cayo con la municion infinita puesta"))
    pawn.call_method("AlternarMunicionInfinita", ())
    poner(0)
    out.append("municion infinita -> %s, flechas a 0"
               % pawn.get_editor_property("MunicionInfinita"))
    out.append("AHORA: pon PASO = 5 y vuelve a lanzar.")

elif PASO == 5:
    arma, tipo, seg, motivo = estado()
    out.append("segundo arco, a cero -> arma=%r motivo=%r" % (arma, motivo))
    out.append("en la mano: %s" % en_la_mano())
    out.append("  %s" % ("BIEN, el vigilante se rearma con cada arma nueva"
                         if arma == "" and motivo == "AMMO OUT"
                         else "MAL, el vigilante no se rearmo"))
    out.append("Hecho. Puedes parar PIE.")

print("\n".join(out))
