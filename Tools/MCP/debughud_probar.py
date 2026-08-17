import json

# Prueba en PIE del DA Debug HUD.
#
# El panel se fuerza visible desde el CDO para poder verlo SIN pulsar teclas
# (el script no puede teclear). Al terminar se deja como estaba, invisible.
#
# La captura la hace fuera PowerShell, con CopyFromScreen: las capturas del MCP
# **no muestran UI de pantalla** —ni CaptureViewport ni CaptureEditorImage
# dibujan el canvas del HUD— y ya costaron horas de falso negativo una vez.

HIJO = "/Game/DarkAngels/Debug/BP_DA_DebugHUD.BP_DA_DebugHUD"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def obj(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t,
                        json.dumps(a))["returnValue"]


def app(t, a):
    return execute_tool("EditorToolset.EditorAppToolset." + t, json.dumps(a))


VISIBLE = False      # ponlo a False para dejarlo apagado al terminar


def run():
    visible = VISIBLE
    cdo = bp("get_default_object", {"blueprint": {"refPath": HIJO}})
    obj("set_properties", {"instance": cdo,
                           "values": json.dumps({"DbgVisible": visible})})
    leido = json.loads(obj("get_properties", {"instance": cdo,
                                              "properties": ["DbgVisible",
                                                             "DbgHabilitado"]}))
    if not visible:
        return {"apagado": leido}
    # Que nivel esta abierto: el actor que instala el HUD solo esta en el Master.
    escena = execute_tool("editor_toolset.toolsets.scene.SceneTools.find_actors",
                          json.dumps({"name": "DebugZonas", "tag": "",
                                      "collision_channels": []}))["returnValue"]
    if not escena:
        return {"error": "no hay ningun BP_DA_DebugZonas en el nivel abierto",
                "cdo": leido}
    if app("IsPIERunning", {})["returnValue"]:
        app("StopPIE", {})
    app("StartPIE", {"options": {"bSimulate": False,
                                 "playMode": "PlayMode_InViewPort",
                                 "warmupSeconds": 6.0}})
    return {"cdo": leido, "pie": app("IsPIERunning", {})["returnValue"]}
