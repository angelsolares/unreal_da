import json

# Modo inspeccion: al pulsar E sobre un interactuable, la camara se planta
# delante del objeto y lo encuadra; con ESC se vuelve al juego.
#
# COMO SE RESUELVE LA CAMARA SIN TOCAR AL JUGADOR:
# el actor lleva un `CameraComponent` colgado en su -X local, mirando hacia el
# objeto. Al interactuar se **gira el actor** para que su -X apunte al jugador,
# con lo que la camara aparece entre el jugador y el objeto, encarandolo. Girar
# el actor es gratis porque no tiene malla visible: es solo volumen.
# Luego `SetViewTargetWithBlend` hacia el propio actor y el motor hace la
# transicion. Al salir, se devuelve la vista al pawn.
#
# TRES COSAS QUE CONDICIONAN EL MONTAJE:
#   1. **No hay nodo `Self` creable.** `find_node_types` no lo encuentra y
#      `Variables|Self-Reference` no existe como type_id. La referencia a uno
#      mismo se saca por `GetZona` -> `Components|GetOwner`, que devuelve el
#      actor dueno del componente.
#   2. **En un nodo de EVENTO el pin de ejecucion no es el 0** (el 0 es el
#      OutputDelegate). Aqui los pines se buscan POR NOMBRE, que es a prueba de
#      esa clase de sorpresas.
#   3. **`set_properties` sobre un struct solo aplica el primer campo**, asi que
#      `RelativeLocation` se escribe **un campo por llamada**.
#
# OJO CON ESC EN PIE: Escape es el atajo de PARAR la sesion de PIE, asi que
# dentro del editor no se puede probar la salida con ESC. Por eso se acepta
# tambien **Retroceso**, que en PIE si funciona. En build ESC va normal.

BP = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable"
EG = {"refPath": BP + ":EventGraph"}

VAR = "Inspeccionando"
CAMARA = "Camara"
DISTANCIA = -220.0   # -X local: la camara va del lado del jugador
ALTURA = 60.0
MEZCLA = "0.35"
SALIDAS = ["Escape", "BackSpace"]


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def at(t, a):
    return execute_tool("editor_toolset.toolsets.actor.ActorTools." + t, json.dumps(a))["returnValue"]


def ot(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t, json.dumps(a))["returnValue"]


def nodo(tipo, x, y):
    return bt("create_node", {"graph": EG, "type_id": tipo, "pos": {"x": x, "y": y}})


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def pin(n, direccion, nombre):
    """Por NOMBRE, no por indice: los indices cambian segun el tipo de nodo."""
    i = info(n)
    clave = "input_pins" if direccion == "EGPD_Input" else "output_pins"
    for p in i[clave]:
        if p["name"] == nombre:
            return p["pin_id"]
    raise RuntimeError("sin pin " + nombre + " en " + str(i["type_id"]))


def ent(n, nombre):
    return pin(n, "EGPD_Input", nombre)


def sal(n, nombre):
    return pin(n, "EGPD_Output", nombre)


def unir(a, b):
    bt("connect_pins", {"output_pin": a, "input_pin": b})


def valor(p, v):
    bt("set_pin_value", {"pin": p, "value": v})


def exec_de_evento(n):
    """El pin de ejecucion de un evento: el 0 es el OutputDelegate."""
    for p in info(n)["output_pins"]:
        if p["name"] in ("then", "Then"):
            return p["pin_id"]
    return info(n)["output_pins"][1]["pin_id"]


def run():
    bp = {"refPath": BP}
    out = {}

    # --- variable de estado ---
    if VAR not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": VAR, "type_name": "bool"})

    # --- la camara ---
    tenia = {}
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": bp})}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c
    if CAMARA in tenia:
        cam = tenia[CAMARA]
    else:
        cam = at("add_component", {"owner": bp, "name": CAMARA,
                                   "component_type": {"refPath": "/Script/Engine.CameraComponent"}})
        at("set_parent_component", {"component": cam, "parent": tenia["Raiz"]})
    # Un campo por llamada: el setter de structs solo aplica el primero.
    ot("set_properties", {"instance": cam, "values": json.dumps({"RelativeLocation": {"x": DISTANCIA}})})
    ot("set_properties", {"instance": cam, "values": json.dumps({"RelativeLocation": {"z": ALTURA}})})
    out["camara"] = json.loads(ot("get_properties", {"instance": cam, "properties": ["RelativeLocation"]}))

    # --- piezas comunes ---
    zona = nodo("Variables|Default|GetZona", -1200, 500)
    yo = nodo("Components|GetOwner", -1000, 500)
    unir(sal(zona, "Zona"), ent(yo, "self"))

    # =================== Interact ===================
    ev = bt("add_event", {"blueprint": bp, "event_name": "Interact", "position": {"x": -1200, "y": 0}})
    ya = nodo("Variables|Default|Get" + VAR, -1050, 120)
    guarda = nodo("Utilities|FlowControl|Branch", -850, 0)
    pc = nodo("Game|GetPlayerController", -1200, 300)
    pawn = nodo("Game|GetPlayerCharacter", -1200, 380)
    locPawn = nodo("Transformation|GetActorLocation", -1000, 380)
    locYo = nodo("Transformation|GetActorLocation", -800, 500)
    mirar = nodo("Math|Rotator|FindLookatRotation", -600, 420)
    girar = nodo("Transformation|SetActorRotation", -400, 0)
    ver = nodo("Game|Player|SetViewTargetwithBlend", -150, 0)
    quietoM = nodo("Input|SetIgnoreMoveInput", 150, 0)
    quietoL = nodo("Input|SetIgnoreLookInput", 400, 0)
    marcar = nodo("Variables|Default|Set" + VAR, 650, 0)

    unir(sal(pawn, "ReturnValue"), ent(locPawn, "self"))
    unir(sal(yo, "ReturnValue"), ent(locYo, "self"))
    # Start = jugador, Target = objeto: asi el +X mira del jugador al objeto, o
    # sea que el -X —donde vive la camara— cae del lado del jugador.
    unir(sal(locPawn, "ReturnValue"), ent(mirar, "Start"))
    unir(sal(locYo, "ReturnValue"), ent(mirar, "Target"))
    unir(sal(mirar, "ReturnValue"), ent(girar, "NewRotation"))

    unir(exec_de_evento(ev), ent(guarda, "execute"))
    unir(sal(ya, VAR), ent(guarda, "Condition"))
    unir(sal(guarda, "else"), ent(girar, "execute"))          # solo si no estaba ya dentro
    unir(sal(girar, "then"), ent(ver, "execute"))
    unir(sal(pc, "ReturnValue"), ent(ver, "self"))
    unir(sal(yo, "ReturnValue"), ent(ver, "NewViewTarget"))
    valor(ent(ver, "BlendTime"), MEZCLA)
    unir(sal(ver, "then"), ent(quietoM, "execute"))
    unir(sal(pc, "ReturnValue"), ent(quietoM, "self"))
    valor(ent(quietoM, "bNewMoveInput"), "true")
    unir(sal(quietoM, "then"), ent(quietoL, "execute"))
    unir(sal(pc, "ReturnValue"), ent(quietoL, "self"))
    valor(ent(quietoL, "bNewLookInput"), "true")
    unir(sal(quietoL, "then"), ent(marcar, "execute"))
    valor(ent(marcar, VAR), "true")

    # =================== salir con ESC ===================
    tick = None
    for n in bt("find_nodes", {"graph": EG, "title": ""}):
        if "EventTick" in str(info(n)["type_id"]):
            tick = n
            break
    if tick is None:
        tick = bt("add_event", {"blueprint": bp, "event_name": "ReceiveTick", "position": {"x": -1200, "y": 900}})

    dentro = nodo("Variables|Default|Get" + VAR, -1050, 1020)
    br0 = nodo("Utilities|FlowControl|Branch", -850, 900)
    pc2 = nodo("Game|GetPlayerController", -1200, 1100)
    pawn2 = nodo("Game|GetPlayerCharacter", -1200, 1180)
    volver = nodo("Game|Player|SetViewTargetwithBlend", 150, 900)
    sueltaM = nodo("Input|SetIgnoreMoveInput", 400, 900)
    sueltaL = nodo("Input|SetIgnoreLookInput", 650, 900)
    desmarcar = nodo("Variables|Default|Set" + VAR, 900, 900)

    unir(exec_de_evento(tick), ent(br0, "execute"))
    unir(sal(dentro, VAR), ent(br0, "Condition"))

    # Una rama por tecla de salida, todas desembocando en la misma cadena: un
    # pin de ejecucion de ENTRADA admite varias conexiones.
    anterior = sal(br0, "then")
    for i, tecla in enumerate(SALIDAS):
        lee = nodo("Game|Player|WasInputKeyJustPressed", -650, 900 + i * 200)
        br = nodo("Utilities|FlowControl|Branch", -400, 900 + i * 200)
        unir(sal(pc2, "ReturnValue"), ent(lee, "self"))
        valor(ent(lee, "Key"), tecla)
        unir(sal(lee, "ReturnValue"), ent(br, "Condition"))
        unir(anterior, ent(br, "execute"))
        unir(sal(br, "then"), ent(volver, "execute"))
        anterior = sal(br, "else")

    unir(sal(pc2, "ReturnValue"), ent(volver, "self"))
    unir(sal(pawn2, "ReturnValue"), ent(volver, "NewViewTarget"))
    valor(ent(volver, "BlendTime"), MEZCLA)
    unir(sal(volver, "then"), ent(sueltaM, "execute"))
    unir(sal(pc2, "ReturnValue"), ent(sueltaM, "self"))
    valor(ent(sueltaM, "bNewMoveInput"), "false")
    unir(sal(sueltaM, "then"), ent(sueltaL, "execute"))
    unir(sal(pc2, "ReturnValue"), ent(sueltaL, "self"))
    valor(ent(sueltaL, "bNewLookInput"), "false")
    unir(sal(sueltaL, "then"), ent(desmarcar, "execute"))
    valor(ent(desmarcar, VAR), "false")

    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["compila"] = "SI"
    out["salidas"] = SALIDAS
    return out
