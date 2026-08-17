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
# AL SALIR SE RECOGE, si el interactuable lleva item: el objeto entra en el
# inventario de DCS y desaparece del mundo. Ver `bloque_recoger`.
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
ANIMADO = "Animado"
HABLAR = "AnimHablar"
REPOSO = "AnimReposo"
ITEM = "ItemAlRecoger"
CANTIDAD = "CantidadItem"
MUNDO = "MallaMundo"
CAMARA = "Camara"
DISTANCIA = -220.0
ALTURA = 90.0
MEZCLA = "0.35"

DCS = "/Game/DynamicCombatSystem/DCS/Blueprints/"
CLASE_INVENTARIO = DCS + "Components/Inventory/BP_InventoryComponent.BP_InventoryComponent_C"
CLASE_ITEM = DCS + "Items/ObjectItems/BP_DA_Item_Base.BP_DA_Item_Base_C"
# Se espera a que la camara termine de volver antes de destruir nada. Ver
# `bloque_recoger` para el porque.
ESPERA = "0.45"


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
    """Una de las dos mitades del conmutador.

    Devuelve un dict con el primer nodo —para engancharle la entrada— y el
    ultimo, que hace falta para colgar la recogida detras de la salida.
    """
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
    return {"inicio": ver, "fin": marcar}


def bloque_anim(cual, y):
    """Lanza en bucle una animacion sobre el actor de `Animado`.

    Devuelve el pin de entrada y los de salida, para encadenarlo. Va detras de un
    `IsValid` porque los interactuables que no son NPC dejan `Animado` vacio.
    """
    lee = nodo("Variables|Default|Get" + ANIMADO, -250, y + 60)
    valido = nodo("Utilities|IsValid", -60, y)
    comp = nodo("Class|SkeletalMeshActor|GetSkeletalMeshComponent", -60, y + 160)
    anim = nodo("Variables|Default|Get" + cual, -60, y + 240)
    play = nodo("Components|Animation|PlayAnimation", 180, y)

    unir(sal(lee, ANIMADO), ent(valido, "InputObject"))
    unir(sal(lee, ANIMADO), ent(comp, "self"))
    unir(sal(comp, "SkeletalMeshComponent"), ent(play, "self"))
    unir(sal(anim, cual), ent(play, "NewAnimToPlay"))
    valor(ent(play, "bLooping"), "true")
    unir(sal(valido, "Is Valid"), ent(play, "execute"))
    return {"entrada": ent(valido, "exec"),
            "salidas": [sal(valido, "Is Not Valid"), sal(play, "then")]}


def bloque_recoger(evento, yo, y):
    """Mete el item en el inventario de DCS y borra el objeto del mundo.

    Cuelga del final de la rama de SALIR: se recoge al aceptar, no al enfocar,
    que es lo que se ve en pantalla —vuelves a la vista normal y el objeto ya no
    esta—. Si `ItemAlRecoger` esta vacio no hace nada, asi que los NPC y los
    cofres pasan de largo sin enterarse.

    QUIEN RECOGE: el pin `Caller` del evento, que es a quien DCS le pasa la
    interaccion. No `GetPlayerCharacter`: asi vale igual si algun dia recoge otro.

    HAY UN CAST, no basta con `GetComponentByClass`: el nodo devuelve
    `ActorComponent` a secas y `AddItem` pide un `BP_InventoryComponent`. Poner
    la clase en el pin no reetiqueta la salida cuando se monta por MCP —en el
    editor a mano si—, asi que la conexion se rechazaria.

    LO QUE SE VE ES INMEDIATO Y LO QUE SE BORRA ES CON RETRASO, y por dos razones
    distintas:
      - `SetViewTargetWithBlend` **no cambia de vista al momento**: durante toda
        la mezcla el `ViewTarget` sigue siendo el actor viejo y solo al final
        pasa a ser el nuevo. Destruirlo a mitad de camino deja a la camara sin
        origen y en vez de mezclar, corta. Por eso el `Delay`, un pelo mas largo
        que la mezcla.
      - Pero durante esa espera el objeto seguiria en pie y respondiendo a la E,
        y una segunda pulsacion meteria la camara en un actor a punto de morir.
        Asi que nada mas recoger se le quita la colision a `Zona` —DCS deja de
        encontrarlo y el cartel se apaga— y se esconde la malla. Para el jugador
        el objeto desaparece en el acto; el borrado de verdad viene detras.
    """
    lee = nodo("Variables|Default|Get" + ITEM, -250, y + 60)
    valido = nodo("Utilities|IsValid", -60, y)
    comp = nodo("Actor|GetComponentbyClass", 150, y + 240)
    casteo = nodo("Utilities|Casting|CastToBP_InventoryComponent", 400, y)
    cuanto = nodo("Variables|Default|Get" + CANTIDAD, 600, y + 300)
    mete = nodo("Modify|AddItem", 700, y)
    zona = nodo("Variables|Default|GetZona", 900, y + 200)
    sorda = nodo("Collision|SetCollisionEnabled", 950, y)
    leeMundo = nodo("Variables|Default|Get" + MUNDO, 1150, y + 260)
    validoEsconde = nodo("Utilities|IsValid", 1200, y)
    esconde = nodo("Rendering|SetActorHiddenInGame", 1420, y)
    espera = nodo("Utilities|FlowControl|Delay", 1650, y)
    validoBorra = nodo("Utilities|IsValid", 1850, y)
    borraMundo = nodo("Actor|DestroyActor", 2080, y)
    borraYo = nodo("Actor|DestroyActor", 2320, y)

    unir(sal(lee, ITEM), ent(valido, "InputObject"))
    unir(sal(lee, ITEM), ent(mete, "ItemToAdd"))

    unir(sal(evento, "Caller"), ent(comp, "self"))
    valor(ent(comp, "ComponentClass"), CLASE_INVENTARIO)
    unir(sal(comp, "ReturnValue"), ent(casteo, "Object"))
    unir(sal(valido, "Is Valid"), ent(casteo, "execute"))

    unir(sal(casteo, "then"), ent(mete, "execute"))
    unir(sal(casteo, "AsBP Inventory Component"), ent(mete, "self"))
    unir(sal(cuanto, CANTIDAD), ent(mete, "Amount"))

    unir(sal(mete, "then"), ent(sorda, "execute"))
    unir(sal(zona, "Zona"), ent(sorda, "self"))
    valor(ent(sorda, "NewType"), "NoCollision")

    unir(sal(leeMundo, MUNDO), ent(validoEsconde, "InputObject"))
    unir(sal(leeMundo, MUNDO), ent(esconde, "self"))
    unir(sal(leeMundo, MUNDO), ent(validoBorra, "InputObject"))
    unir(sal(leeMundo, MUNDO), ent(borraMundo, "self"))

    unir(sal(sorda, "then"), ent(validoEsconde, "exec"))
    unir(sal(validoEsconde, "Is Valid"), ent(esconde, "execute"))
    valor(ent(esconde, "bNewHidden"), "true")

    # Las dos salidas del IsValid caen en el mismo sitio: haya o no malla suelta,
    # se espera igual.
    unir(sal(validoEsconde, "Is Not Valid"), ent(espera, "execute"))
    unir(sal(esconde, "then"), ent(espera, "execute"))
    valor(ent(espera, "Duration"), ESPERA)

    unir(sal(espera, "then"), ent(validoBorra, "exec"))
    unir(sal(validoBorra, "Is Valid"), ent(borraMundo, "execute"))
    unir(sal(validoBorra, "Is Not Valid"), ent(borraYo, "execute"))
    unir(sal(borraMundo, "then"), ent(borraYo, "execute"))
    unir(sal(yo, "ReturnValue"), ent(borraYo, "self"))
    return ent(valido, "exec")


def encadenar(desde, bloques, hasta):
    """Cose una fila de bloques guardados. Las dos salidas de cada uno entran en
    el siguiente: un pin de ejecucion de ENTRADA admite varias conexiones."""
    anterior = desde
    for b in bloques:
        for s in anterior:
            unir(s, b["entrada"])
        anterior = b["salidas"]
    for s in anterior:
        unir(s, hasta)


def run():
    bp = {"refPath": BP}
    out = {}

    variables = str(bt("list_variables", {"blueprint": bp}))
    if VAR not in variables:
        bt("add_variable", {"blueprint": bp, "name": VAR, "type_name": "bool"})
    # El intercambio de malla al interactuar: cerrado fuera, abierto dentro. Se
    # dejan vacias en los interactuables que no cambian de aspecto, y el grafo
    # las salta con un IsValid.
    # Y la animacion: a que NPC hablarle y con que. Tambien vacias por defecto.
    # `ItemAlRecoger` y `MallaMundo` son la recogida: que item de DCS entra en el
    # inventario y que actor hay que borrar del mundo con el. Vacias en todo lo
    # que no se recoge.
    for v, clase in ((CERRADO, "/Script/Engine.Actor"),
                     (ABIERTO, "/Script/Engine.Actor"),
                     (ANIMADO, "/Script/Engine.SkeletalMeshActor"),
                     (HABLAR, "/Script/Engine.AnimationAsset"),
                     (REPOSO, "/Script/Engine.AnimationAsset"),
                     (ITEM, CLASE_ITEM),
                     (MUNDO, "/Script/Engine.Actor")):
        if v not in variables:
            bt("add_object_variable", {"blueprint": bp, "name": v,
                                       "object_class": {"refPath": clase}})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": v, "instance_editable": True})
    if CANTIDAD not in variables:
        bt("add_variable", {"blueprint": bp, "name": CANTIDAD, "type_name": "int"})
    bt("set_variable_instance_editable",
       {"blueprint": bp, "variable_name": CANTIDAD, "instance_editable": True})

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

    # SALIR (ya estabamos dentro): el NPC vuelve al idle, vista al pawn, se le
    # vuelve a ver, mando suelto
    salir = rama(pc, pawn, "false", pawn, "false", 1200)
    encadenar([sal(br, "then")], [bloque_anim(REPOSO, 1600)],
              ent(salir["inicio"], "execute"))
    # ...y al final de esa rama, la recogida.
    unir(sal(salir["fin"], "then"), bloque_recoger(ev, yo, 1900))

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

    entrar = rama(pc, pawn, "true", yo, "true", 300)["inicio"]
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

    # Y detras, la animacion de hablar del NPC, si lo hay.
    bloques.append(bloque_anim(HABLAR, 900))
    encadenar([sal(girar, "then")], bloques, ent(entrar, "execute"))

    # --- el cartel de DCS dice "Aceptar" mientras se esta dentro ---
    bt("write_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"},
                           "code": "(fn GetInteractionMessage ()\n"
                                   '  (return (Utilities|String|SelectString "Aceptar"'
                                   " (Variables|Default|GetVerbo)"
                                   " (Variables|Default|Get" + VAR + "))))"})

    bt("compile_blueprint", {"blueprint": bp})
    # La cantidad por defecto: uno. Se pone DESPUES de compilar, que hasta
    # entonces el CDO no tiene la propiedad recien creada.
    ot("set_properties", {"instance": bt("get_default_object", {"blueprint": bp}),
                          "values": json.dumps({CANTIDAD: 1})})
    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["mensaje"] = bt("read_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"}})
    out["cantidad_por_defecto"] = json.loads(ot("get_properties", {
        "instance": bt("get_default_object", {"blueprint": bp}),
        "properties": [CANTIDAD]}))
    out["compila"] = "SI"
    return out
