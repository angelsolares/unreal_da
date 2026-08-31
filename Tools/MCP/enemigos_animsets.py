# -*- coding: utf-8 -*-
"""Da a los enemigos los animsets nuevos: Espadon al Heraldo, Lanza al Lancero.

    execute_python_code(code=open("Tools/MCP/enemigos_animsets.py").read())

EL PROBLEMA. Los montages nuevos (Two-Handed Sword Pack y Spear Pack) solo los
usaba el JUGADOR, porque el enrutado vive en el `GetMontages` sobrescrito de
`BP_DA_PlayerCharacter`. Los enemigos heredan de `BP_BaseAI`, cuyo `GetMontages`
--que en realidad esta en `BP_CombatCharacter`-- enruta por ESTILO DE COMBATE y
manda todo el mele armado a `DT_AI_1H_Montages`. Medido en PIE: con el Heraldo ya
empunando el espadon, `IsTwoHandedWeaponEquipped` daba True y `GetMontages`
seguia devolviendo `DT_AI_1H_Montages`.

LA SALIDA, y por que esta. Los cuatro enemigos de DA YA tenian un `GetMontages`
propio, pero vacio: llamaba al padre y devolvia su resultado. O sea que el gancho
ya existia y solo habia que darle contenido. No se toca DCS.

LAS TABLAS son COPIAS COMPLETAS de `DT_AI_1H_Montages` con solo dos filas
cambiadas, la 1 (Action.Attack.Light) y la 4 (Action.Attack.Heavy). Las otras
diez --bloqueo, parry, equipar, impacto, especial...-- siguen cayendo en las
animaciones de DCS, que el pack no cubre.

OJO CON EL RITMO. Los montages de IA de DCS llevan `rate_scale` y duran 1,555 s
el ligero y 1,729 el pesado (medido el 24/08, ver calibracion.json). Los del
Espadon duran 0,83-1,33 el ligero y 1,50-2,08 el pesado. **Esto cambia la cadencia
de ataque del Heraldo**, y la calibracion de la Forja se hizo con la vieja.

Ninguna de las dos tablas viaja en el repo: son copia de un asset de pago. Viaja
esta pasada.
"""
import json

import unreal

AI_1H = "/Game/DynamicCombatSystem/DCS/DataTables/Montages/AI/DT_AI_1H_Montages"

#: enemigo -> (tabla nueva, montages del ligero, montages del pesado)
RECETA = {
    "BP_DA_Heraldo": (
        "/Game/DarkAngels/DataTables/DT_DA_AI_2H_Montages",
        ["/Game/DarkAngels/Animations/Espadon/M_DA_Espadon_Ligero_0%d" % i for i in (1, 2, 3, 4)],
        ["/Game/DarkAngels/Animations/Espadon/M_DA_Espadon_Pesado_0%d" % i for i in (1, 2, 3)],
    ),
    "BP_DA_Lancero": (
        "/Game/DarkAngels/DataTables/DT_DA_AI_Lanza_Montages",
        ["/Game/DarkAngels/Animations/Lanza/M_DA_Lanza_AtaqueLigero_0%d" % i for i in (1, 2, 3, 4)],
        ["/Game/DarkAngels/Animations/Lanza/M_DA_Lanza_Pesado_0%d" % i for i in (1, 2, 3)],
    ),
}

FILA_LIGERO = "1"
FILA_PESADO = "4"


def _ref(ruta):
    n = ruta.split("/")[-1]
    return "/Script/Engine.AnimMontage'%s.%s'" % (ruta, n)


def _tabla(destino, ligeros, pesados):
    eal = unreal.EditorAssetLibrary
    for m in ligeros + pesados:
        if not eal.does_asset_exist(m):
            raise RuntimeError("falta el montage %s; pasa antes espadon_montages.py / lanza_montages.py" % m)
    if not eal.does_asset_exist(destino):
        if eal.duplicate_asset(AI_1H, destino) is None:
            raise RuntimeError("no pude duplicar " + AI_1H)
    dt = eal.load_asset(destino)
    datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(dt))
    for f in datos:
        if f["Name"] == FILA_LIGERO:
            f["Montages"] = [_ref(m) for m in ligeros]
        if f["Name"] == FILA_PESADO:
            f["Montages"] = [_ref(m) for m in pesados]
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(datos))
    eal.save_asset(destino)


def tablas():
    for _, (destino, ligeros, pesados) in RECETA.items():
        _tabla(destino, ligeros, pesados)


def verificar_tablas():
    """Se relee del disco: el guardado miente en las dos direcciones."""
    eal = unreal.EditorAssetLibrary
    fallos = []
    for enemigo, (destino, ligeros, pesados) in RECETA.items():
        if not eal.does_asset_exist(destino):
            fallos.append("falta la tabla de %s" % enemigo); continue
        datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(
            eal.load_asset(destino)))
        por = {f["Name"]: [m.split("/")[-1].split(".")[0] for m in f.get("Montages", [])] for f in datos}
        if por.get(FILA_LIGERO) != [m.split("/")[-1] for m in ligeros]:
            fallos.append("%s: la fila del ligero no cuajo: %s" % (enemigo, por.get(FILA_LIGERO)))
        if por.get(FILA_PESADO) != [m.split("/")[-1] for m in pesados]:
            fallos.append("%s: la fila del pesado no cuajo: %s" % (enemigo, por.get(FILA_PESADO)))
        if len(datos) != 12:
            fallos.append("%s: la tabla perdio filas (%d de 12)" % (enemigo, len(datos)))
    return fallos


#: El Heraldo cambia el hacha por el Espadon. Va AQUI y no en el .uasset porque
#: `DA_DA_Espadon` esta en .gitignore --es copia de un asset de pago-- y el
#: blueprint del Heraldo SI viaja: sin esta pasada, un clon recien bajado se
#: encuentra la ranura vacia.
HERALDO_EQ = ("/Game/DarkAngels/Blueprints/Enemies/BP_DA_Heraldo"
              ".BP_DA_Heraldo_C:Equipment_GEN_VARIABLE")
ESPADON = "/Game/DarkAngels/Blueprints/Items/DA_DA_Espadon"


def arma_del_heraldo():
    """Pone el Espadon en la ranura de melé del Heraldo.

    OJO CON LOS STRUCTS: el editor devuelve COPIAS. Mutar `items[0]` en el sitio
    NO escribe nada --probado, se relee igual que estaba--; hay que devolver cada
    copia modificada a su array y reasignar de dentro afuera. Y luego contar los
    elementos, porque el bug conocido de los arrays de structs se come el ultimo.
    """
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(ESPADON):
        raise RuntimeError("falta %s; pasa antes espadon_item.py" % ESPADON)
    eqt = unreal.load_object(None, HERALDO_EQ)
    if eqt is None:
        raise RuntimeError("no encuentro la plantilla de equipo del Heraldo")
    esp = eal.load_asset(ESPADON)

    ms = eqt.get_editor_property("MeleeWeaponSlots")
    slots = list(ms.get_editor_property("Slots"))
    items = list(slots[0].get_editor_property("Items"))
    it0 = items[0]; it0.set_editor_property("Item", esp); items[0] = it0
    s0 = slots[0]; s0.set_editor_property("Items", items); slots[0] = s0
    ms.set_editor_property("Slots", slots)
    eqt.set_editor_property("MeleeWeaponSlots", ms)

    P = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Heraldo"
    unreal.BlueprintEditorLibrary.compile_blueprint(eal.load_asset(P))
    eal.save_asset(P)


def verificar_arma():
    ms = unreal.load_object(None, HERALDO_EQ).get_editor_property("MeleeWeaponSlots")
    items = ms.get_editor_property("Slots")[0].get_editor_property("Items")
    nombres = [i.get_editor_property("Item").get_name() if i.get_editor_property("Item") else None
               for i in items]
    fallos = []
    if nombres[:1] != ["DA_DA_Espadon"]:
        fallos.append("el Heraldo no quedo con el Espadon: %s" % nombres)
    if len(items) != 3:
        fallos.append("la ranura perdio elementos (%d de 3)" % len(items))
    return fallos


def verificar_variables():
    """La tabla se enchufa por una variable `TablaMontages` que lee el GetMontages
    propio de cada enemigo. El grafo SI viaja en el .uasset; esto solo comprueba
    que el default no se ha perdido."""
    fallos = []
    for enemigo, (destino, _, _) in RECETA.items():
        P = "/Game/DarkAngels/Blueprints/Enemies/" + enemigo
        cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_asset(P).generated_class())
        try:
            v = cdo.get_editor_property("TablaMontages")
        except Exception:
            fallos.append("%s: no tiene la variable TablaMontages" % enemigo); continue
        if v is None or v.get_path_name().split(".")[0] != destino:
            fallos.append("%s: TablaMontages apunta a %s" % (enemigo, v))
    return fallos


if __name__ == "__main__":
    tablas()
    arma_del_heraldo()
    f = verificar_tablas() + verificar_arma() + verificar_variables()
    print("[OK] enemigos con sus animsets y el Heraldo con el Espadon"
          if not f else "[FALLO]\n   " + "\n   ".join(f))
