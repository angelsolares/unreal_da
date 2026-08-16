import json

# Modo inspeccion: la E planta la camara delante del objeto, y la E otra vez
# devuelve el juego a la normalidad. **La misma tecla entra y sale.**
#
# COMO SE RESUELVE LA CAMARA SIN TOCAR AL JUGADOR:
# el actor lleva un `CameraComponent` colgado en su -X local. Al entrar se GIRA
# el actor para que ese -X apunte al jugador, con lo que la camara aparece entre
# jugador y objeto, encarandolo; luego `SetViewTargetWithBlend` hacia el propio
# actor. Girar el actor es gratis porque no tiene malla visible: es solo volumen.
#
# **SOLO SE COPIA EL YAW.** La primera version metia la rotacion entera de
# `FindLookAtRotation` y la camara salia siempre picada, mirando el objeto desde
# arriba. La causa: el origen del jugador esta a la altura del pecho y el del
# objeto en el suelo, asi que el pitch siempre miraba hacia abajo. Rompiendo el
# rotator y quedandose solo con el yaw, la camara queda a nivel y de frente, que
# es el angulo que se quiere de un objeto.
#
# **Se esconde al jugador** mientras dura, el y todo lo que lleve encajado
# —`GetAttachedActors` recursivo—, porque el escudo y la espada se colaban en el
# encuadre.
#
# NADA DE ESC: en el editor Escape para la sesion de PIE, asi que no vale como
# tecla de salida. Se sale con la misma E, y mientras se esta dentro el cartel de
# DCS dice "Aceptar" en vez del verbo (ver `GetInteractionMessage`).
#
# DOS COSAS QUE CONDICIONAN EL MONTAJE:
#   1. **No hay nodo `Self` creable.** La referencia a uno mismo se saca por
#      `GetZona` -> `Components|GetOwner`.
#   2. **En un nodo de EVENTO el pin de ejecucion no es el 0** (el 0 es el
#      OutputDelegate). Aqui los pines se buscan POR NOMBRE, que es a prueba de eso.

BP = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable"
EG = {"refPath": BP + ":EventGraph"}

VAR = "Inspeccionando"
CERRADO = "Cerrado"
ABIERTO = "Abierto"
CAMARA = "Camara"
DISTANCIA = -220.0
ALTURA = 90.0
MEZCLA = "0.35"


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
    clave = "input_pins" if direccion == "EGPD_Input" else "output_pins"
    for p in info(n)[clave]:
        if p["name"] == nombre:
            return p["pin_id"]
    raise RuntimeError("sin pin '" + nombre + "' en " + str(info(n)["type_id"]))


def ent(n, nombre):
    return pin(n, "EGPD_Input", nombre)


def sal(n, nombre):
    return pin(n, "EGPD_Output", nombre)


def unir(a, b):
    bt("connect_pins", {"output_pin": a, "input_pin": b})


def valor(p, v):
    bt("set_pin_value", {"pin": p, "value": v})


def exec_evento(n):
    for p in info(n)["output_pins"]:
        if p["name"] in ("then", "Then"):
            return p["pin_id"]
    return info(n)["output_pins"][1]["pin_id"]


def rama(pc, pawn, oculto, destino, marca, y):
    """Una de las dos mitades del conmutador. Devuelve (primer nodo, ultimo)."""
    esconde = nodo("Rendering|SetActorHiddenInGame", 200, y)
    pegados = nodo("Actor|GetAttachedActors", 200, y + 260)
    bucle = nodo("Utilities|Array|ForEachLoop", 450, y)
    esconde2 = nodo("Rendering|SetActorHiddenInGame", 750, y + 160)
    quietoM = nodo("Input|SetIgnoreMoveInput", 1050, y)
    quietoL = nodo("Input|SetIgnoreLookInput", 1300, y)
    marcar = nodo("Variables|Default|Set" + VAR, 1550, y)
    ver = nodo("Game|Player|SetViewTargetwithBlend", -50, y)

    unir(sal(pc, "ReturnValue"), ent(ver, "self"))
    unir(sal(destino, "ReturnValue"), ent(ver, "NewViewTarget"))
    valor(ent(ver, "BlendTime"), MEZCLA)

    unir(sal(ver, "then"), ent(esconde, "execute"))
    unir(sal(pawn, "ReturnValue"), ent(esconde, "self"))
    valor(ent(esconde, "bNewHidden"), oculto)

    unir(sal(pawn, "ReturnValue"), ent(pegados, "self"))
    valor(ent(pegados, "bRecursivelyIncludeAttachedActors"), "true")

    unir(sal(esconde, "then"), ent(bucle, "Exec"))
    unir(sal(pegados, "OutActors"), ent(bucle, "Array"))
    unir(sal(bucle, "LoopBody"), ent(esconde2, "execute"))
    unir(sal(bucle, "Array Element"), ent(esconde2, "self"))
    valor(ent(esconde2, "bNewHidden"), oculto)

    unir(sal(bucle, "Completed"), ent(quietoM, "execute"))
    unir(sal(pc, "ReturnValue"), ent(quietoM, "self"))
    valor(ent(quietoM, "bNewMoveInput"), marca)
    unir(sal(quietoM, "then"), ent(quietoL, "execute"))
    unir(sal(pc, "ReturnValue"), ent(quietoL, "self"))
    valor(ent(quietoL, "bNewLookInput"), marca)
    unir(sal(quietoL, "then"), ent(marcar, "execute"))
    valor(ent(marcar, VAR), marca)
    return ver


def run():
    bp = {"refPath": BP}
    out = {}

    variables = str(bt("list_variables", {"blueprint": bp}))
    if VAR not in variables:
        bt("add_variable", {"blueprint": bp, "name": VAR, "type_name": "bool"})
    # El intercambio de malla al interactuar: cerrado fuera, abierto dentro. Se
    # dejan vacias en los interactuables que no cambian de aspecto, y el grafo
    # las salta con un IsValid.
    for v in (CERRADO, ABIERTO):
        if v not in variables:
            bt("add_object_variable", {"blueprint": bp, "name": v,
                                       "object_class": {"refPath": "/Script/Engine.Actor"}})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": v, "instance_editable": True})

    # --- de cero: se borra todo lo que no sea un evento ---
    borrados = 0
    for n in bt("find_nodes", {"graph": EG, "title": ""}):
        if not str(info(n)["type_id"]).startswith("AddEvent|"):
            bt("delete_node", {"node": n})
            borrados += 1
    out["nodos_borrados"] = borrados

    # --- la camara ---
    tenia = {}
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": bp})}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c
    cam = tenia[CAMARA] if CAMARA in tenia else at("add_component", {
        "owner": bp, "name": CAMARA, "component_type": {"refPath": "/Script/Engine.CameraComponent"}})
    if CAMARA not in tenia:
        at("set_parent_component", {"component": cam, "parent": tenia["Raiz"]})
    # Un campo por llamada: el setter de structs solo aplica el primero.
    ot("set_properties", {"instance": cam, "values": json.dumps({"RelativeLocation": {"x": DISTANCIA}})})
    ot("set_properties", {"instance": cam, "values": json.dumps({"RelativeLocation": {"z": ALTURA}})})

    # --- piezas comunes ---
    zona = nodo("Variables|Default|GetZona", -1500, 700)
    yo = nodo("Components|GetOwner", -1300, 700)
    unir(sal(zona, "Zona"), ent(yo, "self"))
    pc = nodo("Game|GetPlayerController", -1500, 800)
    pawn = nodo("Game|GetPlayerCharacter", -1500, 880)
    estado = nodo("Variables|Default|Get" + VAR, -1300, 120)

    # --- el conmutador ---
    ev = bt("add_event", {"blueprint": bp, "event_name": "Interact", "position": {"x": -1500, "y": 0}})
    br = nodo("Utilities|FlowControl|Branch", -1100, 0)
    unir(exec_evento(ev), ent(br, "execute"))
    unir(sal(estado, VAR), ent(br, "Condition"))

    # SALIR (ya estabamos dentro): vista al pawn, se le vuelve a ver, mando suelto
    salir = rama(pc, pawn, "false", pawn, "false", 1200)
    unir(sal(br, "then"), ent(salir, "execute"))

    # ENTRAR: primero girar de cara al jugador, y solo con el YAW
    locPawn = nodo("Transformation|GetActorLocation", -1100, 880)
    locYo = nodo("Transformation|GetActorLocation", -1100, 700)
    mirar = nodo("Math|Rotator|FindLookatRotation", -850, 800)
    romper = nodo("Math|Rotator|BreakRotator", -650, 800)
    hacer = nodo("Math|Rotator|MakeRotator", -450, 800)
    girar = nodo("Transformation|SetActorRotation", -300, 300)

    unir(sal(pawn, "ReturnValue"), ent(locPawn, "self"))
    unir(sal(yo, "ReturnValue"), ent(locYo, "self"))
    # Start = jugador, Target = objeto: el +X va del jugador al objeto, o sea que
    # el -X —donde vive la camara— cae del lado del jugador.
    unir(sal(locPawn, "ReturnValue"), ent(mirar, "Start"))
    unir(sal(locYo, "ReturnValue"), ent(mirar, "Target"))
    unir(sal(mirar, "ReturnValue"), ent(romper, "InRot"))
    unir(sal(romper, "Yaw"), ent(hacer, "Yaw"))      # Roll y Pitch se quedan a 0
    unir(sal(hacer, "ReturnValue"), ent(girar, "NewRotation"))

    entrar = rama(pc, pawn, "true", yo, "true", 300)
    unir(sal(br, "else"), ent(girar, "execute"))

    # --- el cambiazo de malla: el cerrado se esconde, el abierto aparece ---
    # No se deshace al salir: una vez abierto, el cofre se queda abierto.
    # Cada uno pasa por un `IsValid` porque la mayoria de interactuables dejan
    # estas dos variables vacias y no cambian de aspecto al interactuar.
    bloques = []
    for i, (variable, oculto) in enumerate(((CERRADO, "true"), (ABIERTO, "false"))):
        lee = nodo("Variables|Default|Get" + variable, -250, 560 + i * 220)
        valido = nodo("Utilities|IsValid", -60, 500 + i * 220)
        cambia = nodo("Rendering|SetActorHiddenInGame", 180, 500 + i * 220)
        unir(sal(lee, variable), ent(valido, "InputObject"))
        unir(sal(lee, variable), ent(cambia, "self"))
        valor(ent(cambia, "bNewHidden"), oculto)
        unir(sal(valido, "Is Valid"), ent(cambia, "execute"))
        bloques.append({"entrada": ent(valido, "exec"),
                        "salidas": [sal(valido, "Is Not Valid"), sal(cambia, "then")]})

    # Las dos salidas de cada bloque desembocan en el siguiente: un pin de
    # ejecucion de ENTRADA admite varias conexiones.
    anterior = [sal(girar, "then")]
    for b in bloques:
        for s in anterior:
            unir(s, b["entrada"])
        anterior = b["salidas"]
    for s in anterior:
        unir(s, ent(entrar, "execute"))

    # --- el cartel de DCS dice "Aceptar" mientras se esta dentro ---
    bt("write_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"},
                           "code": "(fn GetInteractionMessage ()\n"
                                   '  (return (Utilities|String|SelectString "Aceptar"'
                                   " (Variables|Default|GetVerbo)"
                                   " (Variables|Default|Get" + VAR + "))))"})

    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["mensaje"] = bt("read_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"}})
    out["compila"] = "SI"
    return out
