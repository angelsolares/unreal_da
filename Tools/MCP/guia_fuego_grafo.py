import json

# El movimiento del fuego fatuo: busca por donde entrar a su ruta, la recorre y
# se apaga al llegar.
#
# Va por DSL y no nodo a nodo porque casi todo son matematicas, que es lo que el
# resolver hace bien. Las operaciones de vector se escriben con los operadores
# del DSL (`+`, `*`): el resolver elige el nodo segun el tipo. Buscarlos con
# `find_node_types` no sirve, no aparecen con esos nombres —el `+` de vectores
# acaba siendo `Math|Vector|vector+vector`—.
#
# **HAY QUE PASARLE `self` A MANO** a lo que tenga pin de `Target`.
# `SetActorLocation`, `DestroyActor` y `SetLifeSpan` lo tienen, y el DSL asigna
# los argumentos por posicion: sin el, el primer argumento se va al pin `self` y
# revienta con "Could not connect pin ReturnValue to self". `self` es un token
# valido del DSL —sale en el grafo de `BP_PickupActor` del pack—; lo que no hay
# es un nodo `Self` que crear con `create_node`.
#
# `Math|Vector|GetUnitDirection(Vector)` da el vector unitario de A a B en un
# solo nodo: ahorra el restar y el normalizar.
#
# LOS PUNTOS NO SE LE PASAN, SE LOS BUSCA. El fuego guarda una referencia al
# actor `BP_DA_Ruta` y le pide la polilinea. Es asi por obligacion —el DSL no
# sabe cablear pines de array entre nodos, y `SetPuntos _f (GetPuntos _r)` no
# compila— pero sale mejor de todas formas: no se copia una lista de 71 vectores
# cada vez que nace un fuego.
#
# `Listo` ES UN CERROJO, no un adorno. Quien suelta el fuego lo crea primero y le
# pasa la ruta despues, asi que sin el, el primer Tick veria `Ruta` vacia y el
# fuego se destruiria antes de nacer.
#
# Y EL FUEGO SE BUSCA LA VIDA. Con `Indice` a -1 —su valor por defecto— en el
# primer tick util recorre su ruta, se queda con el punto mas cercano al sitio
# donde nacio, y si ni el mas cercano cae dentro de `Radio` se destruye solo. Asi
# quien lo suelta no tiene que saber nada: tira uno por cada ruta del nivel y los
# que no vienen a cuento se descartan solos. Once por pulsacion, de los que
# sobreviven uno, dos o tres segun las salidas que haya donde estas.

BP = "/Game/DarkAngels/Blueprints/Level/BP_DA_Fuego.BP_DA_Fuego"
EG = {"refPath": BP + ":EventGraph"}

RADIO = 4000.0     # a que distancia de una ruta se considera que estas en ella
VIDA = 14.0

CODIGO = """
(event EventBeginPlay
  (Actor|SetLifeSpan self 14.0))

(event EventTick (DeltaSeconds)
  (bind _puntos (Class|BPDARuta|GetPuntos (Variables|Default|GetRuta)))
  (if (Variables|Default|GetListo)
    (if (< (Variables|Default|GetIndice) 0)
      (Variables|Default|SetMejorDist 100000000.0)
      (for _k (range 0 (Utilities|Array|Length _puntos))
        (if (< (Math|Vector|Distance(Vector)
                 (Utilities|Array|Get(acopy) _puntos _k)
                 (Transformation|GetActorLocation self))
               (Variables|Default|GetMejorDist))
          (Variables|Default|SetMejorDist
            (Math|Vector|Distance(Vector)
              (Utilities|Array|Get(acopy) _puntos _k)
              (Transformation|GetActorLocation self)))
          (Variables|Default|SetIndice _k)))
      (if (> (Variables|Default|GetMejorDist) (Variables|Default|GetRadio))
        (Actor|DestroyActor self))
      (else
        (if (>= (Variables|Default|GetIndice) (Utilities|Array|Length _puntos))
          (Actor|DestroyActor self)
          (else
            (bind _obj (+ (Utilities|Array|Get(acopy) _puntos
                            (Variables|Default|GetIndice))
                          (Math|Vector|MakeVector 0.0 0.0
                            (Variables|Default|GetAltura))))
            (bind _aqui (Transformation|GetActorLocation self))
            (Transformation|SetActorLocation self
              (+ _aqui (* (Math|Vector|GetUnitDirection(Vector) _aqui _obj)
                          (* (Variables|Default|GetVelocidad) DeltaSeconds))))
            (if (< (Math|Vector|Distance(Vector) _obj _aqui)
                   (Variables|Default|GetCerca))
              (Variables|Default|SetIndice
                (+ (Variables|Default|GetIndice) 1)))))))))
"""


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ot(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    if execute_tool("EditorToolset.EditorAppToolset.IsPIERunning", "{}")["returnValue"]:
        return {"error": "PIE esta corriendo"}
    bp = {"refPath": BP}

    variables = str(bt("list_variables", {"blueprint": bp}))
    for nombre, tipo in (("Listo", "bool"), ("MejorDist", "float"), ("Radio", "float")):
        if nombre not in variables:
            bt("add_variable", {"blueprint": bp, "name": nombre, "type_name": tipo})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": nombre, "instance_editable": True})
    bt("compile_blueprint", {"blueprint": bp})

    bt("write_graph_dsl", {"graph": EG, "code": CODIGO})
    bt("compile_blueprint", {"blueprint": bp})

    # Valores por defecto, DESPUES de compilar: hasta entonces el CDO no tiene
    # las propiedades recien creadas. `Indice` a -1 es lo que dispara la busqueda
    # del punto de entrada.
    cdo = bt("get_default_object", {"blueprint": bp})
    for k, v in (("Indice", -1), ("Radio", RADIO)):
        ot("set_properties", {"instance": cdo, "values": json.dumps({k: v})})
    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))

    return {"defaults": json.loads(ot("get_properties", {
                "instance": bt("get_default_object", {"blueprint": bp}),
                "properties": ["Indice", "Radio", "Velocidad", "Altura", "Cerca"]})),
            "grafo": bt("read_graph_dsl", {"graph": EG})}
