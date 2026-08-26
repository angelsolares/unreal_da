# -*- coding: utf-8 -*-
"""Arregla la punteria del arco, para el Arquero y para Malakh.

    node ue.mjs script punteria_arco.py

EL FALLO. `BP_CombatComponent.GetDirectionToSpawnProjectile` (DCS) convierte una direccion
de entrada correcta en una que apunta casi al cielo. Medido el 26/08 llamandola a mano con
los MISMOS argumentos en los dos componentes:

    direccion que se le pasa   pitch  -6,4   yaw +162,7
    componente del ARQUERO ->  pitch +75,6   yaw +168,2
    componente de MALAKH   ->  pitch +75,6   yaw +168,2

Consecuencia en juego: las flechas salen casi verticales y suben 14.000 cm. El Arquero no
acierta JAMAS, a ninguna distancia. Barriendo sus parametros, el `MaxRange` es INERTE (1 y
15.000 dan el mismo resultado) y el `TraceRadius` no: o sea que el punto al que acaba
apuntando esta pegado al tirador, no lejos. Cuadra con su primera linea, que pone el inicio
de la traza a `|SpawnLocation - ViewLocation|` de los ojos —51 cm medidos, la distancia del
arco a los ojos— y de ahi no se extiende. La direccion resultante es la del arco a un punto
justo delante de la cara, y como el arco cuelga POR DEBAJO de los ojos, eso apunta arriba.

POR QUE NO SE TOCA DCS. Se podria arreglar la funcion en su sitio, pero es un asset de pago
y esas modificaciones se pierden al reinstalar sin avisar a nadie. En vez de eso se
SOBRESCRIBE `GetLocAndDirToSpawnArrow` en nuestros dos blueprints, que es quien la llama.
DCS queda intacto y el arreglo viaja en git.

Y hay una razon tecnica ademas: una funcion SOBRESCRITA hereda los pines de retorno del
padre. El escritor del DSL no sabe crearlos —comprobado el 26/08, tres funciones salieron
vacias por eso— asi que esta es la unica forma de escribir por MCP una funcion que devuelve
dos valores.

QUE HACE CADA UNA:

  - El ARQUERO apunta al blanco con la MISMA prediccion que traia el original: posicion del
    objetivo mas su velocidad por el tiempo de vuelo. Lo unico que se quita es la llamada
    rota.
  - MALAKH apunta a 150 m por delante de la camara. Sin traza: eso hace que el arco y la
    camara CONVERJAN a esa distancia, que es lo normal en un tercera persona y basta de
    sobra. Si algun dia se quiere que la flecha vaya exactamente al punto bajo la mira, ahi
    es donde iria una traza desde la camara.

EL PUNTO DE SALIDA VA EN LINEA, y no por pereza: `Combat|GetProjectileSpawnLocation`
resuelve a la version de `BP_CombatCharacter`, y el Arquero NO es uno (deriva de
`BP_BaseAI`). Sin target da "must have a connection" al compilar, y con `self` da pines
incompatibles; `CallFunction|...` no existe. Lo que si vale para los dos es inlinear lo
que hace `BP_BaseAI.GetProjectileSpawnLocation`, que es identico al del jugador: pedirle
el punto al item mostrado en la mano principal.

OJO CON EL VOCABULARIO: la aritmetica se escribe con OPERADORES, no con nombres de nodo.
El lector muestra `Math|Vector|vector*float` y `Math|Vector|vector+vector`, pero el
escritor no conoce ninguno de los dos (ni Multiply_VectorFloat, ni ScaleVector, ni
vector*vector: probados los seis). Lo que si acepta es `(* v f)` y `(+ a b)`.

VERIFICACION. Al final relee las dos funciones del disco. La prueba de verdad es en PIE:
pedirle la direccion y compararla con donde esta el blanco (ver `probe_punteria.py`).
"""
import json

ARQUERO = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Arquero"
MALAKH = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter"
FUNCION = "GetLocAndDirToSpawnArrow"
SCRATCH = "ZZProbePunteria"

# El Arquero: apunta al blanco, con la prediccion del original.
CUERPO_ARQUERO = """(fn GetLocAndDirToSpawnArrow ()
  (bind _spawn (Class|BPBaseDisplayedItem|GetProjectileSpawnLocation (DisplayedItems|GetMainHandDisplayedItem)))
  (bind _blanco (Variables|AI|GetTargetActor))
  (bind _prediccion (+ (Transformation|GetActorLocation _blanco)
    (* (Transformation|GetVelocity _blanco)
       (/ (Transformation|GetDistanceTo _blanco) (Variables|Archery|GetArrowInitialSpeed)))))
  (return _spawn (Math|Conversions|RotationFromXVector
    (Math|Vector|GetUnitDirection(Vector) _spawn _prediccion))))
"""

# Malakh: apunta a 150 m por delante de la camara.
CUERPO_MALAKH = """(fn GetLocAndDirToSpawnArrow ()
  (bind _spawn (Class|BPBaseDisplayedItem|GetProjectileSpawnLocation (DisplayedItems|GetMainHandDisplayedItem)))
  (bind (_vloc _vrot) (Pawn|GetPlayerViewPoint (Pawn|GetController)))
  (bind _lejos (+ _vloc (* (Math|Rotator|GetRotationXVector _vrot) 15000.0)))
  (return _spawn (Math|Conversions|RotationFromXVector
    (Math|Vector|GetUnitDirection(Vector) _spawn _lejos))))
"""

TRABAJO = [(ARQUERO, "BP_DA_Arquero", CUERPO_ARQUERO),
           (MALAKH, "BP_DA_PlayerCharacter", CUERPO_MALAKH)]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def grafos(bpp):
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": {"refPath": bpp}})]


def vaciar(g):
    """OJO: el nodo de retorno se llama `ReturnNode`, no `FunctionResult`. Filtrarlo mal
    lo borra, y con el se van los pines de salida que son justo lo que se venia a
    aprovechar de una funcion sobrescrita."""
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(bt("get_node_infos", {"nodes": [nodo]})[0]["type_id"])
        if "FunctionEntry" in tid or "FunctionResult" in tid or "ReturnNode" in tid:
            continue
        bt("delete_node", {"node": nodo})


def prevuelo(bpp, codigo):
    """Comprueba el VOCABULARIO en un grafo suelto. El `(return a b)` se cambia por un
    bind porque el banco no tiene pines de salida: lo que se quiere saber es si los nodos
    existen, no si la firma cuadra."""
    g = {"refPath": bpp + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + FUNCION + " ", "(fn " + SCRATCH + " ", 1)
    # El return devuelve DOS valores y `bind` solo admite uno, asi que se tira el primero
    # (que ya viene de un bind anterior y por tanto tambien queda probado).
    cuerpo = cuerpo.replace("(return _spawn ", "(bind _zz ", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        j = m.find("does not exist")
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, j - 90):j + 14]) if j > 0 else m[:260]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}
    for ruta, nombre, codigo in TRABAJO:
        bpp = ruta + "." + nombre
        r = {}
        if FUNCION not in grafos(bpp):
            vue("OverrideFunction", {"blueprintPath": ruta, "functionName": FUNCION})
            r["override"] = "creado"
        else:
            r["override"] = "ya estaba"
        if SCRATCH not in grafos(bpp):
            bt("add_function_graph", {"blueprint": {"refPath": bpp}, "graph_name": SCRATCH})
        fallo = prevuelo(bpp, codigo)
        r["prevuelo"] = fallo or "OK"
        if fallo:
            out[nombre] = r
            continue
        g = {"refPath": bpp + ":" + FUNCION}
        vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        bt("compile_blueprint", {"blueprint": {"refPath": bpp}})
        st("save_assets", {"asset_paths": [ruta]})
        # RELEER, que el `true` del guardado no vale nada.
        r["releido"] = str(bt("read_graph_dsl", {"graph": g}))
        out[nombre] = r
    return out
