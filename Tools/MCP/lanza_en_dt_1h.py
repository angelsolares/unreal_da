# -*- coding: utf-8 -*-
"""La Lanza: saca su montage de la tabla compartida de DCS y le da tabla propia.

    execute_python_code(code=open("Tools/MCP/lanza_en_dt_1h.py").read())

EL NOMBRE DEL FICHERO ES HISTORICO. Hasta el 2026-08-31 este guion METIA
`M_DA_Lanza_AtaqueLigero_01` en la fila 1 de `DT_Player_1H_Montages`, la tabla
compartida de DCS. Ahora hace lo contrario, y por un motivo medido:

    con el HACHA equipada, el tercer golpe del combo ligero era la LANZA.

Es el defecto que se anoto el 25/08 como "sale con cualquier arma" y que
`GetMontages` --sobrescrito en BP_DA_PlayerCharacter, ver espadon_montages.py--
por fin permite cerrar: se enruta por ARMA, no por estilo.

QUE HACE AHORA
  1. Devuelve la fila 1 de `DT_Player_1H_Montages` a su contenido original
     (M_1H_LightAttack_02 + M_1H_LightAttack_01). Fuera la lanza.
  2. Crea `DT_DA_Lanza_Montages`: copia de la de una mano con la fila 1 puesta a
     la animacion de la lanza y SOLO a ella, de modo que todos los golpes del
     combo ligero sean lanza. Las demas acciones caen en las de DCS.

OJO: hoy solo hay UN montage de lanza, asi que los tres golpes del combo repiten
la misma animacion. El pack tiene cinco combos; construir los otros es la misma
receta que `espadon_montages.py`, midiendo el pico de velocidad de la punta.

POR QUE LA LANZA NO CAE EN LA RAMA DE DOS MANOS: `DA_DA_Lanza` es
`twoHanded=True`, asi que sin este desvio le saldrian las animaciones del
ESPADON. El override la distingue por NOMBRE DE OBJETO, porque comparar dos
referencias con `==` no compila en el DSL.

Ninguna de las dos tablas viaja en el repo: la de DCS es de pago y la nuestra es
copia suya. Viaja esta pasada.
"""
import json

import unreal

T1H   = "/Game/DynamicCombatSystem/DCS/DataTables/Montages/Player/DT_Player_1H_Montages"
LANZA = "/Game/DarkAngels/DataTables/DT_DA_Lanza_Montages"
M_LANZA = ("/Script/Engine.AnimMontage'/Game/DarkAngels/Animations/Lanza/"
           "M_DA_Lanza_AtaqueLigero_01.M_DA_Lanza_AtaqueLigero_01'")
ORIGINAL_1H = [
    "/Script/Engine.AnimMontage'/Game/DynamicCombatSystem/DCS/Animations/"
    "OneHandShield/Montages/Player/M_1H_LightAttack_02.M_1H_LightAttack_02'",
    "/Script/Engine.AnimMontage'/Game/DynamicCombatSystem/DCS/Animations/"
    "OneHandShield/Montages/Player/M_1H_LightAttack_01.M_1H_LightAttack_01'",
]


def _filas(ruta):
    dt = unreal.EditorAssetLibrary.load_asset(ruta)
    return dt, json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(dt))


def _escribir(dt, datos, ruta):
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(datos))
    unreal.EditorAssetLibrary.save_asset(ruta)


def pasada():
    eal = unreal.EditorAssetLibrary

    # 1. la tabla de DCS, limpia
    dt, datos = _filas(T1H)
    for f in datos:
        if f["Name"] == "1":
            f["Montages"] = ORIGINAL_1H
    _escribir(dt, datos, T1H)

    # 2. la tabla propia de la Lanza
    if not eal.does_asset_exist(LANZA):
        if eal.duplicate_asset(T1H, LANZA) is None:
            raise RuntimeError("no pude duplicar la tabla de una mano")
    dt2, datos2 = _filas(LANZA)
    for f in datos2:
        if f["Name"] == "1":
            f["Montages"] = [M_LANZA]
    _escribir(dt2, datos2, LANZA)


def verificar():
    """Se relee del disco: el guardado miente."""
    fallos = []
    _, d1 = _filas(T1H)
    fila1 = [f for f in d1 if f["Name"] == "1"][0]["Montages"]
    if any("Lanza" in m for m in fila1):
        fallos.append("la lanza sigue colada en la tabla de DCS: %s" % fila1)
    if len(fila1) != 2:
        fallos.append("la fila 1 de DCS no quedo con sus dos montages: %s" % fila1)
    _, d2 = _filas(LANZA)
    filaL = [f for f in d2 if f["Name"] == "1"][0]["Montages"]
    if filaL != [M_LANZA]:
        fallos.append("la tabla de la lanza no quedo con su montage: %s" % filaL)
    return fallos


if __name__ == "__main__":
    pasada()
    f = verificar()
    print("[OK] lanza con tabla propia, y la de DCS limpia" if not f else "[FALLO]\n   " + "\n   ".join(f))
