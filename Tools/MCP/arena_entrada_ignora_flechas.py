"""La caja `Entrada` de la arena deja de interceptar flechas. De verdad esta vez.

    node ue.mjs script arena_entrada_ignora_flechas.py

POR QUE HAY UNA SEGUNDA PASADA. `arena_no_come_flechas.py` puso las cinco cajas en
`OverlapOnlyPawn` desde el ConstructionScript, y agarro en los cuatro muros... pero NO en
`Entrada`. Leido de la partida viva:

    Entrada    perfil=OverlapAllDynamic   vs Projectile = OVERLAP    <- seguia mal
    MuroNorte  perfil=Custom              vs Projectile = IGNORE
    MuroSur/Este/Oeste   igual que el norte

El motivo estaba en el EventGraph, en el BeginPlay de la arena:

    (SetCollisionProfileName (GetEntrada)   "OverlapAllDynamic" false)
    (SetCollisionProfileName (GetMuroNorte) "InvisibleWall"     false)   ... y los otros tres

O sea que **el BeginPlay fuerza el perfil** y pisa lo que dejo el ConstructionScript. Los
muros salvan porque `InvisibleWall` ignora los canales personalizados; `Entrada` no.

Y esto ya estaba escrito en las notas de Malkuth, sobre los ZoneTrigger: "su BeginPlay
fuerza el perfil; OverlapOnlyPawn o envenenan la punteria". Mismo fallo, tercer actor.

QUE HACE ESTA PASADA. Cambia ese literal del BeginPlay: `OverlapAllDynamic` ->
`OverlapOnlyPawn`. Nada mas. Se busca POR FORMA —el nodo `SetCollisionProfileName` cuyo
target es `Entrada`— y no por posicion, para que aguante que el grafo se reordene.

`OverlapOnlyPawn` solapa Pawn y Vehicle e ignora Camera; para los canales PERSONALIZADOS
—`Projectile` es uno, `ECC_GameTraceChannel1`— usa el defecto del canal, que es Ignore. La
caja sigue detectando al jugador (que es su unico trabajo: sellar al entrar) y desaparece
para las flechas.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BPP = RUTA + ".BP_DA_Arena"
BP = {"refPath": BPP}
GRAFO = {"refPath": BPP + ":EventGraph"}
VIEJO = "OverlapAllDynamic"
NUEVO = "OverlapOnlyPawn"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"candidatos": []}

    nodos = bt("find_nodes", {"graph": GRAFO, "title": ""})
    infos = bt("get_node_infos", {"nodes": nodos})

    objetivo = None
    for i in infos:
        if "SetCollisionProfileName" not in str(i["type_id"]):
            continue
        # OJO: el valor del pin viene en la clave "value", no en "default_value".
        perfil = None
        for p in i["input_pins"]:
            if p["name"] == "InCollisionProfileName":
                perfil = p
        v = str(perfil["value"]) if perfil is not None else "?"
        out["candidatos"].append("%s perfil=%s" % (i["type_id"], v))
        # Se identifica por el VALOR y no por el target: de los cinco nodos, solo el de
        # "Entrada" pone OverlapAllDynamic; los cuatro muros ponen InvisibleWall.
        if v == VIEJO:
            objetivo = (i, perfil)

    if objetivo is None:
        out["error"] = "no encuentro el SetCollisionProfileName con " + VIEJO
        return out

    i, perfil = objetivo
    bt("set_pin_value", {"pin": perfil["pin_id"], "value": NUEVO})
    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # RELEER del grafo, que el `true` no vale nada.
    releido = str(bt("read_graph_dsl", {"graph": GRAFO}))
    out["quedan_OverlapAllDynamic"] = releido.count(VIEJO)
    out["hay_OverlapOnlyPawn"] = releido.count(NUEVO)
    return out
