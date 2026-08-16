import json


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def run():
    call("EditorToolset.EditorAppToolset.SelectActors", {"actors": []})
    return {"seleccion": call("EditorToolset.EditorAppToolset.GetSelectedActors", {})}
