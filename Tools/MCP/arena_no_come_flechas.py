"""Las cajas de la arena dejan de comerse las flechas.

    node ue.mjs script arena_no_come_flechas.py

EL FALLO. `BP_DA_Arena` tiene cinco cajas enormes —`Entrada` (37 m de lado) y los cuatro
muros— y las cinco con perfil `OverlapAllDynamic`, que **SOLAPA el canal Projectile**:

    Entrada    perfil=OverlapAllDynamic   vs Projectile = OVERLAP
    MuroNorte  perfil=OverlapAllDynamic   vs Projectile = OVERLAP
    MuroSur    ... y Este y Oeste igual

Las flechas de DCS no tienen colision propia: golpean con un `BP_CollisionHandlerComponent`
que barre con una esfera entre la posicion del fotograma anterior y la actual. Trazando ese
mismo barrido a mano del Arquero a Malakh, por el canal Projectile, sale esto:

    Forja_Arena                comp=Entrada   perfil=OverlapAllDynamic  -> OVERLAP
    Forja_Cobertura_cob_pilar  comp=Mesh      perfil=BlockAll           -> BLOCK

O sea que **la primera cosa que toca cualquier flecha disparada dentro de la arena es la
caja de la propia arena**. Y por tipos de objeto (Pawn), que es como traza el manejador de
mele que SI funciona, el mismo barrido da dos impactos limpios y los dos son Malakh.

Esto ya se habia aprendido una vez en este proyecto y se olvido: la nota de los ZoneTrigger
de Malkuth dice literalmente "OverlapOnlyPawn o envenenan la punteria".

EL ARREGLO. `OverlapOnlyPawn` para las cinco. Ese perfil solapa Pawn y Vehicle, ignora
Camera, y para los canales PERSONALIZADOS —Projectile es uno— usa el valor por defecto del
canal, que es Ignore. Que es justo lo que hace falta: las cajas siguen detectando al
jugador y dejan de existir para las flechas.

DONDE SE PONE. En una funcion nueva colgada del ConstructionScript, detras de
`ColocarMuros`. Asi vale para la arena que ya esta en el nivel Y para todas las que exporte
la Forja, sin tocar a mano ninguna instancia. `ColocarMuros` no se reescribe —es larga y
funciona— sino que se le añade una hermana.

OJO: el ConstructionScript se reescribe entero, pero cabe en dos lineas y esta leido antes
de tocarlo.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BPP = RUTA + ".BP_DA_Arena"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeCol"
CAJAS = ["Entrada", "MuroNorte", "MuroSur", "MuroEste", "MuroOeste"]
PERFIL = "OverlapOnlyPawn"

AJUSTAR = "(fn AjustarColisiones ()\n" + "\n".join(
    '  (Collision|SetCollisionProfileName (Variables|Default|Get%s) "%s" false)' % (c, PERFIL)
    for c in CAJAS) + ")\n"

CONSTRUCCION = """(fn ConstructionScript ()
  (CallFunction|ColocarMuros)
  (CallFunction|AjustarColisiones))
"""


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


def prevuelo(codigo, nombre):
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        i = m.find("does not exist")
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 90):i + 14]) if i > 0 else m[:260]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}
    for n in [SCRATCH, "AjustarColisiones"]:
        if n not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": n})

    out["antes_ConstructionScript"] = str(bt("read_graph_dsl",
                                             {"graph": {"refPath": BPP + ":UserConstructionScript"}}))

    out["prevuelo"] = prevuelo(AJUSTAR, "AjustarColisiones") or "OK"
    if out["prevuelo"] != "OK":
        return out

    g = {"refPath": BPP + ":AjustarColisiones"}
    vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": AJUSTAR})

    gc = {"refPath": BPP + ":UserConstructionScript"}
    vaciar(gc)
    bt("write_graph_dsl", {"graph": gc, "code": CONSTRUCCION})

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # RELEER, que el `true` del guardado no vale nada.
    out["AjustarColisiones"] = str(bt("read_graph_dsl", {"graph": g}))
    out["ConstructionScript"] = str(bt("read_graph_dsl", {"graph": gc}))
    return out
