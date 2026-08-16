import json

# Monta `ABP_DA_Alas`, el Anim Blueprint de las alas, para que se animen segun lo
# que hace el personaje que las lleva.
#
# POR QUE NO SE CASTEA A `BP_BaseAI`, QUE ES LO QUE SE PIDIO:
#   - `BP_BaseAI` casi no expone nada: `BehaviorTreeAsset`, `BaseAIController`,
#     `TargetActor` y `HeadSocketName`. El estado de combate vive en componentes.
#   - Y `BP_BaseAI` y `BP_CombatCharacter` —el jugador— **no tienen antepasado
#     comun**: los dos cuelgan directamente de `Character`. Castear a `BP_BaseAI`
#     dejaria al jugador fuera para siempre.
# Lo que las alas necesitan —velocidad y si esta en el aire— vive en `Character`,
# que si comparten. Asi valen para enemigos, para el jugador y para lo que venga,
# sin depender de DCS ni del pack de la demo.
#
# POR QUE NO SE PORTA `ABP_Wings5` DEL PACK: su maquina de estados es de vuelo
# —dash, planning, takeoff, fall, scream— y para un enemigo de tierra sobra casi
# entera; ademas arrastraria las 26 animaciones y `BP_ThirdPersonCharacter` con
# su cadena de input y game mode.
#
# EL ASSET LO CREA ANGEL A MANO. El MCP no puede asignarle el esqueleto destino:
# `TargetSkeleton` vive en el UAnimBlueprint y `set_properties` resuelve al CDO,
# el mismo problema que con las interfaces. Un AnimBP sin esqueleto no sirve.

ABP = "/Game/DarkAngels/Blueprints/Alas/ABP_DA_Alas.ABP_DA_Alas"
AG = {"refPath": ABP + ":AnimGraph"}
EG = {"refPath": ABP + ":EventGraph"}

PACK = "Animation|Sequences|Play'AS__AS_W5_%s'"
QUIETO = PACK % "idle_ground"
MOVIENDO = PACK % "flapping"
VOLANDO = PACK % "fly_idle"

MOV = "Moviendose"
AIRE = "EnElAire"
UMBRAL = 10.0        # a partir de que velocidad se considera que se mueve
MEZCLA = "0.25"      # segundos de transicion entre poses


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def nodo(g, tipo, x, y):
    return bt("create_node", {"graph": g, "type_id": tipo, "pos": {"x": x, "y": y}})


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


def buscar(g, tipo):
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        if str(info(n)["type_id"]) == tipo:
            return n
    return None


def vaciar(g, conservar):
    """Borra los nodos del grafo menos los que se listen. Nunca se borra el
    grafo entero: `remove_function_graph` + `add` no reutiliza el nombre."""
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        if str(info(n)["type_id"]) not in conservar:
            bt("delete_node", {"node": n})


def run():
    bp = {"refPath": ABP}
    out = {}

    ya = str(bt("list_variables", {"blueprint": bp}))
    for v in (MOV, AIRE):
        if v not in ya:
            bt("add_variable", {"blueprint": bp, "name": v, "type_name": "bool"})
    bt("compile_blueprint", {"blueprint": bp})

    # ---------------- EventGraph: leer al personaje ----------------
    vaciar(EG, ("AddEvent|EventBlueprintUpdateAnimation",))
    ev = buscar(EG, "AddEvent|EventBlueprintUpdateAnimation")
    if ev is None:
        return {"error": "no esta el evento BlueprintUpdateAnimation"}

    pawn = nodo(EG, "Animation|TryGetPawnOwner", -1000, 300)
    cast = nodo(EG, "Utilities|Casting|CastToCharacter", -750, 0)
    unir(sal(pawn, "ReturnValue"), ent(cast, "Object"))
    salida_ev = None
    for p in info(ev)["output_pins"]:
        if p["name"] == "then":
            salida_ev = p["pin_id"]
    unir(salida_ev, ent(cast, "execute"))

    # Se mueve: modulo de la velocidad por encima del umbral.
    vel = nodo(EG, "Transformation|GetVelocity", -500, 250)
    largo = nodo(EG, "Math|Vector|VectorLength", -300, 250)
    mayor = nodo(EG, "Utilities|Operators|Greater(>)", -120, 250)
    ponMov = nodo(EG, "Variables|Default|Set" + MOV, 120, 0)
    unir(sal(cast, "AsCharacter"), ent(vel, "self"))
    unir(sal(vel, "ReturnValue"), ent(largo, "A"))
    unir(sal(largo, "ReturnValue"), ent(mayor, "A"))
    valor(ent(mayor, "B"), str(UMBRAL))
    unir(sal(mayor, "ReturnValue"), ent(ponMov, MOV))
    unir(sal(cast, "then"), ent(ponMov, "execute"))

    # En el aire: `IsFalling` del componente de movimiento. Se pide por clase y
    # no se castea al blueprint, que asi vale para cualquier Character.
    comp = nodo(EG, "Actor|GetComponentbyClass", -500, 520)
    cae = nodo(EG, "Movement|IsFalling", -250, 520)
    ponAire = nodo(EG, "Variables|Default|Set" + AIRE, 380, 0)
    unir(sal(cast, "AsCharacter"), ent(comp, "self"))
    valor(ent(comp, "ComponentClass"), "/Script/Engine.CharacterMovementComponent")
    unir(sal(comp, "ReturnValue"), ent(cae, "self"))
    unir(sal(cae, "ReturnValue"), ent(ponAire, AIRE))
    unir(sal(ponMov, "then"), ent(ponAire, "execute"))

    # ---------------- AnimGraph: elegir la pose ----------------
    vaciar(AG, ("Misc.|OutputPose",))
    salidaPose = buscar(AG, "Misc.|OutputPose")
    if salidaPose is None:
        return {"error": "no esta el nodo Output Pose"}

    quieto = nodo(AG, QUIETO, -700, 0)
    moviendo = nodo(AG, MOVIENDO, -700, 200)
    volando = nodo(AG, VOLANDO, -700, 450)
    getMov = nodo(AG, "Variables|Default|Get" + MOV, -700, 380)
    getAire = nodo(AG, "Variables|Default|Get" + AIRE, -400, 620)
    b1 = nodo(AG, "Animation|Blends|BlendPosesbybool", -400, 60)
    b2 = nodo(AG, "Animation|Blends|BlendPosesbybool", -100, 300)

    # Primer blend: quieto o aleteando, segun se mueva.
    unir(sal(quieto, "Pose"), ent(b1, "BlendPose_0"))
    unir(sal(moviendo, "Pose"), ent(b1, "BlendPose_1"))
    unir(sal(getMov, MOV), ent(b1, "bActiveValue"))
    for p in ("BlendTime_0", "BlendTime_1"):
        valor(ent(b1, p), MEZCLA)

    # Segundo blend: lo anterior, o vuelo si esta en el aire. Manda este.
    unir(sal(b1, "Pose"), ent(b2, "BlendPose_0"))
    unir(sal(volando, "Pose"), ent(b2, "BlendPose_1"))
    unir(sal(getAire, AIRE), ent(b2, "bActiveValue"))
    for p in ("BlendTime_0", "BlendTime_1"):
        valor(ent(b2, p), MEZCLA)

    unir(sal(b2, "Pose"), ent(salidaPose, "Result"))

    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [ABP.split(".")[0]]}))
    out["variables"] = [str(v) for v in bt("list_variables", {"blueprint": bp})]
    out["compila"] = "SI"
    return out
