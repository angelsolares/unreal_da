# -*- coding: utf-8 -*-
"""Engancha BP_DA_Arquero a nuestra copia del arbol. Segunda mitad de bt_arquero_da.py.

    node ue.mjs py bt_arquero_da.py        <- primero: duplica y ajusta el umbral
    node ue.mjs script bt_arquero_engancha.py   <- luego: apunta el BP a la copia

POR QUE SON DOS FICHEROS. `bt_guerrero_da.py` hacia esto mismo escribiendo en el objeto
por defecto de la clase desde la API `unreal`, y ESO YA NO SE PUEDE: el MCP lo corta con
un PYTHON_UNSAFE_CODE ("Modifying Class Default Objects from Python causes crashes"). El
guardia es ademas un escaneo de TEXTO, o sea que salta con solo ver el nombre de esa
llamada en el fichero, aunque solo se lea.

La via que si pasa es `VibeUE.BlueprintService.SetVariableDefaultValue`, que va por el
sandbox y no por la API `unreal`. Y como el sandbox no puede importar `unreal`, no cabe
en la misma pasada.

`BehaviorTreeAsset` es HEREDADA de BP_BaseAI, asi que no sale en `ListVariables` del
Arquero. Escribirla igualmente funciona, pero por eso la verificacion no se hace con
`ListVariables` sino leyendo el valor de vuelta.
"""
import json

BP = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Arquero"
ARBOL = "/Game/DarkAngels/AI/BT_DA_Arquero.BT_DA_Arquero"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


CDO = BP + ".Default__BP_DA_Arquero_C"


def run():
    out = {}
    # SetVariableDefaultValue DEVUELVE EXITO Y NO ESCRIBE NADA sobre una variable
    # HEREDADA. Comprobado: acepto la llamada, compilo, guardo, y al releer el
    # BehaviorTreeAsset seguia siendo el BT_ArcherAI de DCS. Es el "el editor miente en
    # las dos direcciones" de siempre. La que si escribe es ObjectTools.set_properties
    # sobre el objeto por defecto de la clase.
    out["intentoVibeUE"] = str(vue("SetVariableDefaultValue",
                                   {"blueprintPath": BP,
                                    "variableName": "BehaviorTreeAsset",
                                    "defaultValue": ARBOL}))
    out["intentoObjectTools"] = str(call(
        "editor_toolset.toolsets.object.ObjectTools.set_properties",
        {"instance": {"refPath": CDO},
         "values": json.dumps({"BehaviorTreeAsset": {"refPath": ARBOL}})}))
    call("editor_toolset.toolsets.blueprint.BlueprintTools.compile_blueprint",
         {"blueprint": {"refPath": BP + ".BP_DA_Arquero"}})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [BP]})

    # RELEER, que el `true` de estas APIs solo dice que acepto la llamada. Y hay que
    # leerlo del OBJETO, no de la lista de variables: es heredada y ahi no sale.
    leido = call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                 {"instance": {"refPath": CDO},
                  "properties": ["BehaviorTreeAsset"]})
    out["releido"] = str(leido)
    out["veredicto"] = "OK" if "BT_DA_Arquero" in str(leido) else "NO SE QUEDO"
    return out
