# -*- coding: utf-8 -*-
import json

# `BP_DA_Paso`: un paso que se cruza PULSANDO, no andando encima.
#
# Es la logica de `Cruzar` de `BP_DA_Umbral` --teletransporte del jugador a un
# actor `Destino` con `bTeleport = true`-- colgada de la interaccion de DCS en vez
# del solape. El umbral del espejo sigue como estaba: esto no lo toca.
#
# ### POR QUE ES HIJO DE `BP_DA_Interactuable` Y NO UN ACTOR SUELTO
#
# Por la interfaz. DCS encuentra los interactuables trazando una capsula contra
# el TIPO DE OBJETO `Interactable` y les pide el cartel por `I_IsInteractable`,
# y **el MCP no sabe declarar una interfaz**: `interaccion_crear_bp.py` termina
# diciendo "PENDIENTE a mano". Un hijo la hereda ya puesta, y con ella hereda el
# `Zona` con su canal `ECC_GameTraceChannel2` y su `QueryOnly` bien configurados.
# Cero pasos manuales.
#
# Comprobado antes de construir: en el hijo, `list_events` da `Interact` con
# `bIsImplemented: False` y `list_functions` da `GetInteractionMessage` igual, o
# sea que las dos se pueden sobreescribir. Y `add_function_graph` con el nombre
# de la funcion heredada **no crea una funcion nueva: crea la sobreescritura**,
# con su `ReturnNode` y su pin `Message` de tipo Name ya puestos.
#
# ### QUE PASA CON EL MODO INSPECCION: SE VA
#
# El padre gasta la E en un conmutador de camara (encuadrar el objeto, esconder
# al jugador, bloquearle el mando, y salir con la misma tecla). Al sobreescribir
# el evento `Interact` aqui, **nada de eso se ejecuta**: una E, un cruce.
#
# No es solo una preferencia, es que no hay eleccion: `find_node_types` con
# filtro "Parent:" devuelve **vacio**, o sea que el DSL no puede crear la llamada
# al padre. (Ojo: eso NO significa que el nodo no exista. Al crear el hijo,
# Unreal le metio solo sobreescrituras de `BeginPlay`, `Tick` y
# `ActorBeginOverlap` con su `Parent:` correspondiente ya cableado. Las borramos
# abajo: el padre las tiene vacias y una de ellas es un Tick por actor.)
#
# Y aunque se pudiera, tampoco convendria: un paso es algo que CRUZAS, no algo
# que miras. Meterle una toma de camara obligatoria a cada puerta es friccion, y
# el cruce ocurriria con el pawn escondido y el mando bloqueado, que es justo el
# estado en el que no quieres teletransportar a nadie.
#
# **Si algun dia se quiere la ceremonia** --encuadrar la puerta y cruzar al
# aceptar-- no hay que tocar esto: se pone al lado un `BP_DA_MarcarFlag`, que ya
# vigila el flanco de `Inspeccionando` de un interactuable sin modificarlo. Ese
# es el patron que usan `BP_DA_Decision` y la tableta del Gazebo.
#
# ### EL ESTADO NO ESTA AQUI
#
# `BP_DA_Umbral` lleva un `Activo` propio que se apaga al cruzar, y ese es
# justamente el reparto que `BP_DA_GameState` vino a terminar. Aqui no hay
# ninguna variable de estado: `FlagRequerido` decide si se puede cruzar y
# `FlagPaso` deja constancia de que se cruzo, y las dos son NOMBRES de flags del
# GameState, no el estado en si. El cartel sale de `VerboPaso`, tambien del
# GameState (ver `paso_verbo.py`).
#
# Consecuencia buena: el Debug HUD ya ve si un paso se ha cruzado, sin saber que
# los pasos existen.
#
# ### LA ROTACION AL LLEGAR NO SE CALCULA: SE LEE DEL DESTINO
#
# Unica desviacion respecto a `Cruzar` del umbral. Alli el yaw sale de un
# `FindLookAtRotation` desde el destino hacia el umbral, o sea que **apareces
# mirando por donde has venido**. En una sala redonda de espejos es lo que
# quieres; cruzando una puerta no: sales de espaldas al camino. Aqui el yaw es
# el del propio actor `Destino`, que ademas se ve girado en el editor.
#
# Lo que si se copia tal cual, porque es el meollo: `SetActorLocationAndRotation`
# con `bSweep = false` y `bTeleport = true`, y detras `SetControlRotation`. Las
# dos llamadas, no solo la primera: en DCS el pawn no gira con la camara, asi que
# sin la segunda reapareces mirando hacia donde mirabas antes de cruzar.

CARPETA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Paso"
BPP = CARPETA + "/" + NOMBRE + "." + NOMBRE
BP = {"refPath": BPP}
PADRE = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable_C"

# El blanco al que apunta la traza de DCS. Mas ancho y mas alto que el del padre
# (60/60/90, pensado para un cofre): un paso es un hueco de puerta.
CAJA = {"x": 200.0, "y": 60.0, "z": 200.0}

# `IsValid` es multi-exec y TERMINA el hilo que lo envuelve, asi que esto no
# puede ir en linea dentro del evento: tiene que ser su propia funcion. Es la
# misma razon por la que en el umbral `RomperEspejo` y `Cruzar` van separadas.
CRUZAR = """(fn CruzarPaso ()
  (bind _dst (Variables|Default|GetDestino))
  (Utilities|IsValid _dst
    (:"Is Valid"
      (bind _pj (Game|GetPlayerPawn 0))
      (bind _loc (Transformation|GetActorLocation _dst))
      (bind _rot (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0
                   :Yaw (.yaw (Transformation|GetActorRotation _dst))))
      (Transformation|SetActorLocationAndRotation :self _pj
        :NewLocation _loc :NewRotation _rot :bSweep false :bTeleport true)
      (Pawn|SetControlRotation :self (Game|GetPlayerController 0) :NewRotation _rot))
    (:"Is Not Valid")))
"""

# El cartel. Se sobreescribe el del padre --que dice `Verbo`, o "Aceptar"
# mientras inspeccionas-- porque aqui la palabra la decide el GameState.
# Devuelve un **Name**, no un string: el pin de salida heredado es `Message` de
# tipo Name, de ahi el `StringToName`.
MENSAJE = """(fn GetInteractionMessage ()
  (return (Utilities|String|StringToName
            (Class|BPDAGameState|VerboPaso
              :self (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState))
              :Requerido (Variables|Default|GetFlagRequerido)))))
"""

# Dos `if` hermanos y no uno dentro de otro: comprobado que un `if` NO termina
# el hilo (detras suyo se sigue ejecutando), pero anidar es pedirle mas al DSL
# de lo necesario.
#
# El flag se apunta ANTES de cruzar. Da igual para el resultado, pero asi el
# unico nodo que podria cortar el hilo (`Cruzar`, con su `IsValid` dentro) queda
# el ultimo y no se lleva nada por delante si el `Destino` esta sin poner.
#
# `FlagPaso` vacio no escribe nada. Sin esta guarda un paso sin configurar
# meteria la cadena vacia en `Flags`, y `TieneFlag("")` empezaria a decir que si.
EVENTO = """(event Interaction|EventInteract (Caller)
  (bind _gs (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState)))
  (bind _ok (or (Utilities|String|IsEmpty (Variables|Default|GetFlagRequerido))
                (Class|BPDAGameState|TieneFlag :self _gs
                  :Nombre (Variables|Default|GetFlagRequerido))))
  (if (and _ok (not (Utilities|String|IsEmpty (Variables|Default|GetFlagPaso))))
    (Class|BPDAGameState|MarcarFlag :self _gs
      :Nombre (Variables|Default|GetFlagPaso)))
  (if _ok
    (CallFunction|CruzarPaso)))
"""


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g, todo):
    """Vacia un grafo. `todo` incluye los eventos.

    Hace falta SIEMPRE antes de un `write_graph_dsl`: escribir sobre un grafo con
    cuerpo no lo reemplaza, anade otra copia entera.
    """
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        if not todo and tid.startswith("AddEvent|"):
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}

    # --- 1. el blueprint, hijo del interactuable ---
    if ast("exists", {"path": CARPETA + "/" + NOMBRE}):
        out["blueprint"] = "reutilizado"
    else:
        bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": PADRE}})
        out["blueprint"] = "creado"
    out["padre"] = str(bt("get_parent", {"blueprint": BP})["refPath"])

    # --- 2. variables: NOMBRES de flags, no estado ---
    ya = str(bt("list_variables", {"blueprint": BP}))
    for n, t in (("FlagRequerido", "string"), ("FlagPaso", "string")):
        if "'" + n + "'" not in ya:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": t})
    if "'Destino'" not in ya:
        bt("add_object_variable", {"blueprint": BP, "name": "Destino",
                                   "object_class": {"refPath": "/Script/Engine.Actor"}})
    for n in ("Destino", "FlagRequerido", "FlagPaso"):
        bt("set_variable_instance_editable",
           {"blueprint": BP, "variable_name": n, "instance_editable": True})

    # --- 3. la caja que ve la traza de DCS ---
    zona = None
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": BP})}):
        if c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "") == "Zona":
            zona = c
    ot("set_properties", {"instance": zona, "values": json.dumps({"BoxExtent": CAJA})})
    ot("set_properties", {"instance": zona,
                          "values": json.dumps({"RelativeLocation": {"z": CAJA["z"]}})})

    # --- 4. los grafos ---
    # El de `CruzarPaso` ANTES que el evento: una llamada a funcion propia no
    # resuelve si el grafo llamado todavia no existe.
    #
    # SE LLAMA `CruzarPaso` Y NO `Cruzar` POR EL LECTOR, no por el escritor.
    #
    # Llamandola `Cruzar` el grafo funciona --el `type_id` del nodo es
    # `|Cruzar`, categoria vacia, o sea una llamada propia-- pero
    # `read_graph_dsl` la imprime como **`(Class|BPDAUmbral|Cruzar)`**: el lector
    # resuelve el nombre por todo el proyecto y le cuelga el blueprint
    # equivocado, porque `BP_DA_Umbral` tiene una funcion que se llama igual.
    #
    # O sea que releer el grafo --que es como se comprueba todo aqui-- daba un
    # diagnostico falso: parecia que el DSL habia cogido la funcion del vecino,
    # como ya paso de verdad con `Pawn|GetControlRotation`. Con un nombre que no
    # tenga nadie mas, lo que se lee es lo que hay. La comprobacion buena es
    # mirar el `type_id` del nodo (`a_quien_llama`, mas abajo), no el texto.
    # El EventGraph se vacia lo PRIMERO, y entero, eventos incluidos. Dos motivos:
    # ahi estan las tres sobreescrituras vacias que Unreal le puso al crear el
    # hijo (`BeginPlay`, `Tick` y `ActorBeginOverlap`, cada una con su `Parent:`
    # cableado; el padre las tiene vacias, asi que quitarlas no pierde nada y
    # ahorra un Tick por actor), y ahi esta tambien la llamada de una pasada
    # anterior: si se borra una funcion mientras alguien la llama, el blueprint
    # ya no compila y el script muere en el `compile_blueprint` de abajo.
    eg = {"refPath": BPP + ":EventGraph"}
    out.setdefault("vaciados", {})["EventGraph"] = vaciar(eg, True)

    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
    if "Cruzar" in grafos:
        bt("remove_function_graph", {"blueprint": BP, "graph_name": "Cruzar"})
        out["cruzar_viejo"] = "borrado"
    for nombre in ("CruzarPaso", "GetInteractionMessage"):
        if nombre not in grafos:
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
    bt("compile_blueprint", {"blueprint": BP})

    for nombre, codigo in (("CruzarPaso", CRUZAR), ("GetInteractionMessage", MENSAJE)):
        g = {"refPath": BPP + ":" + nombre}
        out.setdefault("vaciados", {})[nombre] = vaciar(g, True)
        bt("write_graph_dsl", {"graph": g, "code": codigo})

    bt("write_graph_dsl", {"graph": eg, "code": EVENTO})

    bt("compile_blueprint", {"blueprint": BP})
    ast("save_assets", {"asset_paths": [CARPETA + "/" + NOMBRE]})

    # --- 5. releer, que el `true` de estas APIs solo dice "acepte la llamada" ---
    out["CruzarPaso"] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":CruzarPaso"}}))
    out["mensaje"] = str(bt("read_graph_dsl",
                            {"graph": {"refPath": BPP + ":GetInteractionMessage"}}))
    out["EventGraph"] = str(bt("read_graph_dsl", {"graph": eg}))
    out["variables"] = [str(v) for v in bt("list_variables", {"blueprint": BP})]
    out["zona"] = json.loads(ot("get_properties", {"instance": zona,
                                "properties": ["BoxExtent", "RelativeLocation"]}))

    # A quien apunta de verdad la llamada del evento. El `type_id` de una funcion
    # PROPIA es `|CruzarPaso`, con la categoria VACIA; si sale
    # `Class|BPDAUmbral|...` es que el DSL ha vuelto a coger la del vecino.
    for n in bt("find_nodes", {"graph": eg, "title": ""}):
        tid = str(info(n)["type_id"])
        if "Cruzar" in tid:
            out["a_quien_llama"] = tid

    # El `bTeleport` se comprueba EN EL PIN: `read_graph_dsl` omite los valores
    # por defecto, asi que releyendo el grafo no se distingue `true` de no puesto.
    for n in bt("find_nodes", {"graph": {"refPath": BPP + ":CruzarPaso"}, "title": ""}):
        i = info(n)
        b = [[p["name"], str(p["value"])] for p in i["input_pins"]
             if p["name"] in ("bSweep", "bTeleport")]
        if b:
            out["pines_teleport"] = b
    return out
