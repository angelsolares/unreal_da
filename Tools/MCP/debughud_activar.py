import json

# DA Debug HUD (fase 1) — el actor del nivel que lo instala.
#
# `BP_DA_DebugZonas` ya existe y ya esta colocado en L_DA_Malkuth_Master (con la
# etiqueta DEBUG_SaltoZonas): en BeginPlay hacia `ClientSetHUD(BP_DA_HUD_C)`,
# porque el GameMode del proyecto es el de DCS y su HUDClass es el pelado del
# motor, asi que sin este actor el HUD del juego no se instancia siquiera.
#
# Ahora instala el HIJO (BP_DA_DebugHUD), que trae ademas el Debug HUD.
#
# LA CLASE SE PIDE POR REFERENCIA BLANDA, a proposito: asi el nivel **no tiene
# ninguna referencia dura** a /Game/DarkAngels/Debug y esa carpeta se puede
# poner en DirectoriesToNeverCook. En un build empaquetado la carga devuelve
# nulo, se cae al HUD normal del juego y no falta nada. Esa es la proteccion de
# Shipping de verdad: el codigo de debug no esta en el build.

ACTOR = "/Game/DarkAngels/Blueprints/Level/BP_DA_DebugZonas.BP_DA_DebugZonas"
HUD_DEBUG = "/Game/DarkAngels/Debug/BP_DA_DebugHUD.BP_DA_DebugHUD_C"
HUD_JUEGO = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD_C"

CODIGO = ('(event EventBeginPlay\n'
          '  (bind pc (Game|GetPlayerController 0))\n'
          # La ruta va como VALOR del pin, no como nodo: MakeSoftClassPath
          # devuelve un SoftClassPath y el pin quiere un SoftClassReference,
          # que son tipos distintos y el DSL no los enchufa.
          '  (bind clase (Utilities|LoadClassAssetBlocking'
          ' :AssetClass "' + HUD_DEBUG + '"))\n'
          # El cast es a HUD **del motor**, no a la clase de debug: asi el
          # blueprint sigue sin conocer nada de /Debug. Es un cast puro, sin
          # pines de ejecucion, asi que la validez se mira antes.
          '  (if (Utilities|IsValidClass clase)\n'
          '    (HUD|ClientSetHUD :self pc'
          ' :NewHUDClass (Utilities|Casting|CastToHUDClass :Class clase))\n'
          '    (else\n'
          '      (HUD|ClientSetHUD :self pc :NewHUDClass "' + HUD_JUEGO + '"))))')


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ast(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    bp("write_graph_dsl", {"graph": {"refPath": ACTOR + ":EventGraph"}, "code": CODIGO})
    bp("compile_blueprint", {"blueprint": {"refPath": ACTOR}})
    ast("save_assets", {"asset_paths": [ACTOR.split(".")[0],
                                        "/Game/DarkAngels/Debug/BP_DA_DebugHUD",
                                        "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD"]})
    return {"grafo": bp("read_graph_dsl", {"graph": {"refPath": ACTOR + ":EventGraph"}}),
            "sucio_actor": ast("is_dirty", {"asset_path": ACTOR.split(".")[0]}),
            "sucio_hud": ast("is_dirty", {"asset_path":
                                          "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD"}),
            "sucio_debug": ast("is_dirty", {"asset_path":
                                            "/Game/DarkAngels/Debug/BP_DA_DebugHUD"})}
