import json

# Sonda: como funciona el inventario de DCS. Que hace falta para que la llave
# entre en la mochila y desaparezca del suelo.

DCS = "/Game/DynamicCombatSystem/DCS/Blueprints/"
INV = DCS + "Components/Inventory/"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ref(p):
    return {"refPath": p + "." + p.split("/")[-1]}


def dsl(bp, nombre):
    for g in bt("list_graphs", {"blueprint": bp}):
        if str(g["refPath"]).split(":")[-1] == nombre:
            return bt("read_graph_dsl", {"graph": g})
    return "NO ESTA: " + nombre


def run():
    out = {}
    pk = ref(INV + "BP_PickupActor")
    out["grafos_pickup"] = bt("list_graphs", {"blueprint": pk})
    out["EventGraph"] = dsl(pk, "EventGraph")
    out["TakeAllItems"] = dsl(pk, "TakeAllItems")
    out["TakeItem"] = dsl(pk, "TakeItem")
    out["GetInteractionMessage"] = dsl(pk, "GetInteractionMessage")
    out["DestroySelfIfEmpty"] = dsl(pk, "DestroySelfIfEmpty")
    out["UserConstructionScript"] = dsl(pk, "UserConstructionScript")
    return out
