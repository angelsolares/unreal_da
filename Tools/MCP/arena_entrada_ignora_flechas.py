"""La caja `Entrada` deja de interceptar flechas, SIN cegar a los enemigos.

    node ue.mjs script arena_entrada_ignora_flechas.py

HISTORIA CORTA, porque hubo dos intentos fallidos antes de este y los dos enseñan algo.

EL PROBLEMA ORIGINAL. `Entrada` es una caja de 37 m que cubre la arena entera, con perfil
`OverlapAllDynamic`, que **solapa el canal `Projectile`**. Las flechas de DCS golpean con un
`CollisionHandler` que barre por ese canal, asi que lo PRIMERO que tocaba cualquier flecha
disparada dentro de la arena era la caja de la propia arena. El Arquero disparaba y no
acertaba nunca.

INTENTO 1: poner las cinco cajas en `OverlapOnlyPawn` desde el ConstructionScript. No
sirvio: **el BeginPlay fuerza el perfil** y pisa lo que deje el ConstructionScript.

INTENTO 2: cambiar el literal del BeginPlay a `OverlapOnlyPawn`. Arreglo las flechas y
**rompio la IA**: Angel lo vio enseguida —"no voltean para atacarme, como si no se
activaran"— y el registro le dio la razon, 47 s de partida con vida 100 y cero golpes.
El motivo, medido:

    Entrada con OverlapOnlyPawn:   vs Visibility = BLOCK

`OverlapOnlyPawn` solo declara Pawn, Vehicle y Camera; para Visibility se queda con el
defecto del canal, que es BLOQUEAR. O sea que una caja de 37 m pasaba a **cortar todas las
trazas de linea de vision de la arena**, que es exactamente lo que usa la percepcion de la
IA para verte. Con `OverlapAllDynamic` eso no pasaba porque solapa TODO, y un solapamiento
no corta una traza.

LO QUE HACE ESTA PASADA, que es lo que habia que hacer desde el principio: **no tocar el
perfil**. Se deja `OverlapAllDynamic` en el BeginPlay tal y como estaba, y se le cambia
UNICAMENTE la respuesta al canal `Projectile` a Ignore, en las cinco cajas. Todo lo demas
—Visibility, Camera, Pawn— sigue igual que antes.

Y se llama DESPUES del BeginPlay, no desde el ConstructionScript, porque si no lo pisa
igual que la primera vez.

LA LECCION, que ya iba por la tercera repeticion en este proyecto: cambiar un PERFIL entero
para arreglar UN canal toca todos los demas de rebote. La nota de los ZoneTrigger de
Malkuth avisaba de la mitad de esto ("su BeginPlay fuerza el perfil"); la otra mitad —que
`OverlapOnlyPawn` bloquea Visibility— es nueva y cara.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BPP = RUTA + ".BP_DA_Arena"
BP = {"refPath": BPP}
GRAFO = {"refPath": BPP + ":EventGraph"}
PERFIL_BUENO = "OverlapAllDynamic"
CAJAS = ["Entrada", "MuroNorte", "MuroSur", "MuroEste", "MuroOeste"]
CANAL = "ECC_GameTraceChannel1"        # el canal "Projectile" de este proyecto
FN = "AjustarColisiones"

AJUSTAR = ("(fn " + FN + " ()\n" + "\n".join(
    '  (Collision|SetCollisionResponseToChannel (Variables|Default|Get%s) "%s" "ECR_Ignore")'
    % (c, CANAL) for c in CAJAS) + ")\n")


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(bt("get_node_infos", {"nodes": [nodo]})[0]["type_id"])
        if "FunctionEntry" in tid or "FunctionResult" in tid or "ReturnNode" in tid:
            continue
        bt("delete_node", {"node": nodo})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}

    # 1. El perfil del BeginPlay vuelve a ser el de siempre. Si el intento 2 lo dejo en
    #    OverlapOnlyPawn, aqui se deshace: es lo que cegaba a los enemigos.
    infos = bt("get_node_infos", {"nodes": bt("find_nodes", {"graph": GRAFO, "title": ""})})
    perfiles = []
    for i in infos:
        if "SetCollisionProfileName" not in str(i["type_id"]):
            continue
        for p in i["input_pins"]:
            if p["name"] == "InCollisionProfileName":
                perfiles.append((i, p, str(p["value"])))
    out["perfiles_antes"] = [v for _i, _p, v in perfiles]
    for i, p, v in perfiles:
        if v == "OverlapOnlyPawn":
            bt("set_pin_value", {"pin": p["pin_id"], "value": PERFIL_BUENO})
            out["perfil_restaurado"] = PERFIL_BUENO

    # 2. La funcion que apaga SOLO el canal de proyectil.
    if FN not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": FN})
    g = {"refPath": BPP + ":" + FN}
    vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": AJUSTAR})

    # 3. Engancharla en el BeginPlay DETRAS del ultimo SetCollisionProfileName. Se busca
    #    por forma: el ultimo de la cadena es el que no encadena con otro igual.
    infos = bt("get_node_infos", {"nodes": bt("find_nodes", {"graph": GRAFO, "title": ""})})
    porRef = {}
    for i in infos:
        porRef[i["node"]["refPath"]] = i
    if any(FN in str(i["type_id"]) for i in infos):
        out["enchufe"] = "ya estaba"
    else:
        ultimo = None
        salida = None
        siguiente = None
        for i in infos:
            if "SetCollisionProfileName" not in str(i["type_id"]):
                continue
            for p in i["output_pins"]:
                if p["name"] != "then":
                    continue
                sig = None
                for c in p["connected_pins"]:
                    sig = porRef.get(c["node"]["refPath"])
                if sig is not None and "SetCollisionProfileName" not in str(sig["type_id"]):
                    ultimo, salida, siguiente = i, p["pin_id"], sig
        if ultimo is None:
            out["enchufe"] = "NO ENCONTRADO el final de la cadena de perfiles"
            return out
        entrada = None
        for p in siguiente["input_pins"]:
            if p["type_id"] == "Exec" and p["name"] in ("execute", "then", "Exec"):
                entrada = p["pin_id"]
        if entrada is None:
            out["enchufe"] = "el nodo siguiente no tiene pin de ejecucion"
            return out
        pos = ultimo["position"]
        nuevo = bt("create_node", {"graph": GRAFO, "type_id": "CallFunction|" + FN,
                                   "pos": {"x": int(pos["x"]) + 160, "y": int(pos["y"]) + 200}})
        ni = bt("get_node_infos", {"nodes": [nuevo]})[0]
        pin_in = pin_out = None
        for p in ni["input_pins"]:
            if p["type_id"] == "Exec":
                pin_in = p["pin_id"]
        for p in ni["output_pins"]:
            if p["type_id"] == "Exec":
                pin_out = p["pin_id"]
        bt("break_pins", {"output_pin": salida, "input_pin": entrada})
        bt("connect_pins", {"output_pin": salida, "input_pin": pin_in})
        bt("connect_pins", {"output_pin": pin_out, "input_pin": entrada})
        out["enchufe"] = "enchufada tras el ultimo SetCollisionProfileName"

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # RELEER, que el `true` no vale nada.
    ev = str(bt("read_graph_dsl", {"graph": GRAFO}))
    out["perfiles_despues"] = [v for v in ["OverlapAllDynamic", "OverlapOnlyPawn", "InvisibleWall"]
                               if v in ev]
    out["llama_a_" + FN] = FN in ev
    out[FN] = str(bt("read_graph_dsl", {"graph": g}))
    return out
