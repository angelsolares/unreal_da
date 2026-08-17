import json

# La tecla G: suelta un fuego fatuo por cada ruta del nivel y deja que se
# descarten solos los que no vienen a cuento (ver `guia_fuego_grafo.py`).
#
# Se engancha como `Guia_Tick`, una funcion mas del HUD llamada desde el evento
# de dibujado, que es el patron que ya usa `SaltoZonas_Tick` para el teclado
# numerico. Asi no hay que tocar el IMC de DCS ni anadir un InputAction.
#
# LA G ESTABA LIBRE: en `IMC_Player` estan cogidas A, C, D, E, F, I, Q, R, S, U,
# W, X, Tab, Shift, Ctrl, Space y los botones del raton; y el HUD ya usa K, L y
# el bloque numerico.
#
# DOS COSAS QUE EL DSL NO HACE, Y LA SEGUNDA CAMBIA EL DISENIO:
#
# 1. **Hay que castear lo que devuelve `GetAllActorsOfClass`**: da `Actor` a
#    secas aunque le pidas una clase concreta.
#
# 2. **No sabe cablear pines de ARRAY entre nodos.** Pasarle la polilinea al
#    fuego con `SetPuntos _f (GetPuntos _r)` falla con "Could not connect pin
#    ReturnValue to Puntos" aunque los dos lados sean arrays de vectores, y el
#    cast no tiene nada que ver —lo probe con y sin el—. La vuelta es **no pasar
#    el array**: se le da al fuego una **referencia al actor de la ruta** y que
#    lea sus puntos el solo. Las referencias a objeto si se conectan sin
#    problema, es como estan atados `Animado`, `MallaMundo` e `ItemAlRecoger`.
#    De paso sale mas barato: no se copia una lista de 71 vectores por fuego.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
FN = "Guia_Tick"
RUTA = "/Game/DarkAngels/Blueprints/Level/BP_DA_Ruta.BP_DA_Ruta_C"
FUEGO = "/Game/DarkAngels/Blueprints/Level/BP_DA_Fuego.BP_DA_Fuego_C"
ZONA = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger_C"
TECLA = "G"
CERCA_ZONA = 8000.0   # a que distancia de un trigger se considera que estas en el

CODIGO = """
(fn Guia_Tick ()
  (bind _pc (Game|GetPlayerController 0))
  (bind _pj (Game|GetPlayerCharacter 0))
  (if (Game|Player|WasInputKeyJustPressed _pc "%(tecla)s")
    (Variables|Default|SetGuiaBloqueada false)
    (for _az (Actor|GetAllActorsOfClass "%(zona)s")
      (bind _z (."AsBP DA Zone Trigger" (Utilities|Casting|CastToBP_DA_ZoneTrigger _az)))
      (if (not (Class|BPDAZoneTrigger|GetPermiteGuia _z))
        (if (< (Math|Vector|Distance(Vector)
                 (Transformation|GetActorLocation _az)
                 (Transformation|GetActorLocation _pj))
               %(cerca)s)
          (Variables|Default|SetGuiaBloqueada true))))
    (if (not (Variables|Default|GetGuiaBloqueada))
      (for _ar (Actor|GetAllActorsOfClass "%(ruta)s")
        (bind _r (."AsBP DA Ruta" (Utilities|Casting|CastToBP_DA_Ruta _ar)))
        (bind _f (Game|SpawnActorfromClass "%(fuego)s"
                   (Transformation|GetActorTransform _pj)))
        (Class|BPDAFuego|SetRuta _f _r)
        (Class|BPDAFuego|SetPrincipal _f (Class|BPDARuta|GetEsPrincipal _r))
        (Class|BPDAFuego|SetListo _f true)))))
""" % {"tecla": TECLA, "zona": ZONA, "ruta": RUTA, "fuego": FUEGO,
       "cerca": CERCA_ZONA}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    # En el fuego: `Principal` para pintarse dorado o apagado, y `Ruta` para
    # leerse los puntos el solo en vez de que se los pasen.
    fuego = {"refPath": FUEGO[:-2]}
    variables = str(bt("list_variables", {"blueprint": fuego}))
    if "Principal" not in variables:
        bt("add_variable", {"blueprint": fuego, "name": "Principal", "type_name": "bool"})
    if "Ruta" not in variables:
        bt("add_object_variable", {"blueprint": fuego, "name": "Ruta",
                                   "object_class": {"refPath": RUTA}})
    for v in ("Principal", "Ruta"):
        bt("set_variable_instance_editable",
           {"blueprint": fuego, "variable_name": v, "instance_editable": True})
    bt("compile_blueprint", {"blueprint": fuego})

    bp = {"refPath": BP}
    if "GuiaBloqueada" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "GuiaBloqueada", "type_name": "bool"})
        bt("compile_blueprint", {"blueprint": bp})

    grafos = [str(g["refPath"]).split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
    if FN not in grafos:
        bt("add_function_graph", {"blueprint": bp, "graph_name": FN})
    bt("write_graph_dsl", {"graph": {"refPath": BP + ":" + FN}, "code": CODIGO})
    bt("compile_blueprint", {"blueprint": bp})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [BP.split(".")[0], FUEGO[:-2].split(".")[0]]})
    return {"funcion": bt("read_graph_dsl", {"graph": {"refPath": BP + ":" + FN}})}
