import json

# Engancha las dos funciones del salto de zona al EventGraph del HUD, sin tocar
# la logica que ya habia.
#
# Dos cosas que hay que saber de estos grafos:
#   - En un nodo de EVENTO el pin de ejecucion es el de indice **1**: el 0 es el
#     OutputDelegate. Conectar al 0 no da error y no hace nada.
#   - El tipo de nodo para llamar a una funcion propia es `CallFunction|<Nombre>`
#     **sin guiones bajos**: `SaltoZonas_Dibujar` -> `CallFunction|SaltoZonasDibujar`.
#
# El dibujado se inserta ANTES de lo que ya colgaba de DrawHUD y se vuelve a
# encadenar detras, asi no hay que buscar el final de una cadena que acaba en
# rama. El panel va al borde derecho y el objetivo al centro: no se pisan.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
EG = BP + ":EventGraph"

# K2Node_Event_3 = ReceiveDrawHUD (SizeX, SizeY) ; K2Node_Event_2 = Tick (DeltaSeconds)
ENGANCHES = [
    ("K2Node_Event_3", "CallFunction|SaltoZonasDibujar", 1200, 900),
    ("K2Node_Event_2", "CallFunction|SaltoZonasTick", 1200, 1500),
]


def call(tool, args):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + tool,
                        json.dumps(args))["returnValue"]


def pin(nodo_ref, direccion, indice):
    return {"direction": direccion, "index_id": indice, "node": {"refPath": nodo_ref}}


def run():
    res = {}
    for nodo, tipo, x, y in ENGANCHES:
        ev_ref = EG + "." + nodo
        info = call("get_node_infos", {"nodes": [{"refPath": ev_ref}]})[0]

        seguia = None
        for p in info["output_pins"]:
            if p["name"] == "then":
                if p["connected_pins"]:
                    seguia = p["connected_pins"][0]
                break

        llamada = call("create_node", {"graph": {"refPath": EG}, "type_id": tipo,
                                       "pos": {"x": x, "y": y}})
        call("connect_pins", {"output_pin": pin(ev_ref, "EGPD_Output", 1),
                              "input_pin": pin(llamada["refPath"], "EGPD_Input", 0)})
        if seguia is not None:
            call("connect_pins", {"output_pin": pin(llamada["refPath"], "EGPD_Output", 0),
                                  "input_pin": seguia})
        res[nodo] = {"tipo": tipo,
                     "reencadenado": seguia is not None}

    call("compile_blueprint", {"blueprint": {"refPath": BP}})
    res["compila"] = "SI"
    return res
