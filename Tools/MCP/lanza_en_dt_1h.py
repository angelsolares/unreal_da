# -*- coding: utf-8 -*-
"""Mete (o quita) el montage de la Lanza en el combo ligero de DCS.

    node ue.mjs script lanza_en_dt_1h.py          -> lo mete
    QUITAR=1 no existe: para revertir, cambia MODO abajo a "restaurar"

ESTO ES UNA MODIFICACION VIVA SOBRE UN ASSET DE PAGO. `DT_Player_1H_Montages` es de
DCS, esta en `.gitignore` y por tanto **el cambio no viaja en el repositorio**: lo que
viaja es este fichero. Si reinstalas DCS o el pack, se pierde y hay que volver a pasarlo.
Ver la nota de "modificaciones vivas sobre DCS" en DarkAngels_POC_Notas.md.

QUE HACE, EXACTAMENTE. La fila `1` de la tabla es `Action.Attack.Light` y su array son
los golpes del combo ligero. Se le AÑADE `M_DA_Lanza_AtaqueLigero_01` al final, sin
tocar los dos que ya estaban:

    M_1H_LightAttack_02  +  M_1H_LightAttack_01  +  M_DA_Lanza_AtaqueLigero_01

Se añade en vez de sustituir porque asi es reversible y no se pierde nada. `RESTAURA`
guarda el contenido original literal para poder volver.

LO QUE HAY QUE SABER ANTES DE JUGARLO. Esa tabla la elige `BP_CombatCharacter` por TIPO
DE COMBATE, no por arma: la referencia esta CABLEADA en un grafo suyo y el personaje no
tiene ninguna variable de DataTable que se pueda cambiar al equipar. O sea que el tercer
golpe del combo ligero saldra con animacion de lanza **lleves lo que lleves**, tambien
con la espada. Para que fuera exclusivo de la Lanza haria falta duplicar la tabla y
enganchar el cambio al equipar, y eso ya es tocar los grafos de DCS.
"""
import json

TABLA = ("/Game/DynamicCombatSystem/DCS/DataTables/Montages/Player/"
         "DT_Player_1H_Montages.DT_Player_1H_Montages")
FILA = "1"
LANZA = ("/Script/Engine.AnimMontage'/Game/DarkAngels/Animations/Lanza/"
         "M_DA_Lanza_AtaqueLigero_01.M_DA_Lanza_AtaqueLigero_01'")

# El contenido original, literal, tal y como lo devolvio `get_rows` antes de tocarlo.
RESTAURA = {
    "1": {
        "actionTag": {"TagName": "Action.Attack.Light"},
        "montages": [
            "/Script/Engine.AnimMontage'/Game/DynamicCombatSystem/DCS/Animations/"
            "OneHandShield/Montages/Player/M_1H_LightAttack_02.M_1H_LightAttack_02'",
            "/Script/Engine.AnimMontage'/Game/DynamicCombatSystem/DCS/Animations/"
            "OneHandShield/Montages/Player/M_1H_LightAttack_01.M_1H_LightAttack_01'",
        ],
    }
}

MODO = "montar"          # "montar" o "restaurar"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def dtt(t, a):
    return call("editor_toolset.toolsets.data_table.DataTableTools." + t, a)


def leer():
    return json.loads(dtt("get_rows", {"data_table": {"refPath": TABLA},
                                       "row_names": [FILA]}))


def run():
    antes = leer()
    fila = antes[FILA]

    if MODO == "restaurar":
        nueva = RESTAURA
    else:
        montages = list(fila["montages"])
        if LANZA in montages:
            return {"estado": "ya estaba", "montages": [m.split(".")[-1] for m in montages]}
        montages.append(LANZA)
        nueva = {FILA: {"actionTag": fila["actionTag"], "montages": montages}}

    dtt("set_rows", {"data_table": {"refPath": TABLA}, "values": json.dumps(nueva)})

    # RELEER, que aqui el `true` del guardado no vale de nada: hay que mirar la fila.
    despues = leer()
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [TABLA.split(".")[0]]})
    return {
        "modo": MODO,
        "antes": [m.split(".")[-1].rstrip("'") for m in fila["montages"]],
        "despues": [m.split(".")[-1].rstrip("'") for m in despues[FILA]["montages"]],
    }
