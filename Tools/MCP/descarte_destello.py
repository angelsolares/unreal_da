# -*- coding: utf-8 -*-
#
# EL VFX DEL DESCARTE (§9): un destello celestial al sacrificar el arma.
#
#   node ue.mjs script descarte_destello.py
#
# ### QUE PIDE EL PDF
#
# La fila "Discard Special" del §9: "VFX/anticipacion fuerte; el arma se consume
# por decision del jugador". Los cinco descartes funcionaban pero no se
# anunciaban: pulsabas y salia el montaje, sin nada que dijera "esto ha costado
# el arma".
#
# ### LO QUE MONTA
#
# `BP_DA_DestelloDescarte`, un actor efimero (SetLifeSpan 0.8) que se spawnea a
# los pies de Malakh EN CUANTO arranca CUALQUIER descarte — el spawn vive en
# `ArrojarLanza`, el despachador comun de las cinco familias, antes del enrutado
# por arma, asi que un solo punto cubre lanza, estandarte, arco, escudo y golpe
# de suelo.
#
# El destello son dos piezas con UN latido (`Latir`, timer a 50 Hz):
#   - un disco en el suelo con `MI_DA_PilarArma` (el material celestial del
#     pilar: aditivo, sin sombra) que se EXPANDE de 0.8 a ~6.8 de escala, y
#   - una luz azul que nace a 25.000 y muere a 0 en 0,7 s.
# En aditivo, expandirse ya es desvanecerse: la energia se reparte. No hace
# falta animar la opacidad — y MEJOR, porque el nodo de parametro escalar de
# material es AMBIGUO al escribirlo (resuelve al de Parameter Collection y
# revienta; la misma trampa que en arma_pilar_luz.py).
#
# ### LA FORMA DEL ACTOR: FUNCIONES + UN EVENTO COSIDO
#
# Los eventos no se escriben por DSL con garantias, asi que el actor se
# construye igual que el resto de lo de hoy: TODA la logica en funciones
# (`Arrancar`, `Latir`, escritas enteras) y el `BeginPlay` se añade con
# `add_event` y se conecta por cirugia a `Arrancar`. Un nodo, una conexion.

import json

DEST_RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_DestelloDescarte"
DEST = DEST_RUTA + ".BP_DA_DestelloDescarte"
PJ_RUTA = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter"
PJ = PJ_RUTA + ".BP_DA_PlayerCharacter"

MI = "/Game/DarkAngels/Materials/MI_DA_PilarArma.MI_DA_PilarArma"
DURACION = 0.7

ARRANCAR = '''(fn Arrancar ()
  (bind _self self)
  (Actor|SetLifeSpan _self 0.8)
  (Variables|Default|SetTNacio (Utilities|Time|GetGameTimeInSeconds))
  (bind _m (Game|AddComponentbyClass _self "/Script/Engine.StaticMeshComponent"))
  (Variables|Default|SetAnillo (Utilities|Casting|CastToStaticMeshComponent _m))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetAnillo) "/Engine/BasicShapes/Plane.Plane")
  (Rendering|Material|SetMaterial (Variables|Default|GetAnillo) 0 "%(mi)s")
  (Collision|SetCollisionEnabled (Variables|Default|GetAnillo))
  (Transformation|SetRelativeLocation (Variables|Default|GetAnillo) (Math|Vector|MakeVector 0.0 0.0 12.0))
  (Transformation|SetRelativeScale3D (Variables|Default|GetAnillo) (Math|Vector|MakeVector 0.8 0.8 1.0))
  (bind _l (Game|AddComponentbyClass _self "/Script/Engine.PointLightComponent"))
  (Variables|Default|SetLuzD (Utilities|Casting|CastToPointLightComponent _l))
  (Rendering|Components|Light|SetLightColor (Variables|Default|GetLuzD) (Utilities|Struct|MakeLinearColor 0.3 0.62 1.0 1.0))
  (Rendering|Lighting|SetAttenuationRadius (Variables|Default|GetLuzD) 1200.0)
  (Rendering|Components|Light|SetIntensity (Variables|Default|GetLuzD) 25000.0)
  (Utilities|Time|SetTimerbyFunctionName _self "Latir" 0.02 true))
''' % {"mi": MI}

LATIR = '''(fn Latir ()
  (bind _k (Math|Float|Min(Float) 1.0 (/ (- (Utilities|Time|GetGameTimeInSeconds) (Variables|Default|GetTNacio)) %(dur)s)))
  (bind _s (+ 0.8 (* 6.0 _k)))
  (Rendering|Components|Light|SetIntensity (Variables|Default|GetLuzD) (* 25000.0 (- 1.0 _k)))
  (Transformation|SetRelativeScale3D (Variables|Default|GetAnillo) (Math|Vector|MakeVector _s _s 1.0)))
''' % {"dur": DURACION}

# ArrojarLanza, entera: lo unico nuevo es el spawn del destello, primera
# sentencia de la rama valida — las sentencias van ANTES del if, y el enrutado
# por familia queda tal cual estaba.
ARROJAR = '''(fn ArrojarLanza ()
  (bind _self self)
  (bind _armatemporal (Variables|Default|GetArmaTemporal))
  (Utilities|IsValid _armatemporal
    (:"Is Valid"
      (Game|SpawnActorfromClass "%(destello)s_C" (Math|Transform|MakeTransform (Transformation|GetActorLocation _self) (Math|Rotator|MakeRotator 0.0)) "AlwaysSpawn")
      (if (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _armatemporal) "DA_DA_Trompeta")
        (Animation|PlayAnimMontage _self "/Game/DarkAngels/Animations/Estandarte/M_DA_ClavarEstandarte.M_DA_ClavarEstandarte")
        (elif (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _armatemporal) (Utilities|GetObjectName (Variables|Default|GetArmaArrojadiza)))
          (Animation|PlayAnimMontage _self "/Game/DarkAngels/Animations/Throw/M_DA_ArrojarLanza.M_DA_ArrojarLanza")
          (elif (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _armatemporal) "DA_ElvenBow")
            (Animation|PlayAnimMontage _self "/Game/DarkAngels/Animations/Arco/M_DA_LluviaFirmamento.M_DA_LluviaFirmamento")
            (elif (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _armatemporal) "DA_WoodenShield")
              (Animation|PlayAnimMontage _self "/Game/DarkAngels/Animations/Escudo/M_DA_LanzarEscudo.M_DA_LanzarEscudo")
              (else
                (Animation|PlayAnimMontage _self "/Game/DarkAngels/Animations/Espadon/M_DA_GolpeDeSuelo.M_DA_GolpeDeSuelo")))))))))
''' % {"destello": DEST}

VARIABLES = [("TNacio", "double", "0.0", ""),
             ("Anillo", "StaticMeshComponent", "", ""),
             ("LuzD", "PointLightComponent", "", "")]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def grafos(bpp):
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": {"refPath": bpp}})]


def vaciar(g):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def pin(direccion, indice, nodo):
    return {"direction": direccion, "index_id": indice, "node": nodo}


def exec_pins(inf, clave):
    return [p for p in inf[clave] if str(p["type_id"]) == "Exec"]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"escritas": [], "vaciados": {}}

    # 1. El actor lo crea ANTES `descarte_destello_crear.py` (py-mode): los
    # errores de toolset abortan este sandbox y no los caza un try, asi que
    # aqui no hay comprobacion de existencia posible — se asume creado.
    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": DEST_RUTA}))
    for nombre, tipo, defecto, cont in VARIABLES:
        if nombre in existentes:
            continue
        vue("AddMemberVariable", {"blueprintPath": DEST_RUTA, "variableName": nombre,
                                  "variableType": tipo, "defaultValue": defecto,
                                  "containerType": cont})
        out["escritas"].append("var nueva -> " + nombre)

    for nombre, codigo in [("Arrancar", ARRANCAR), ("Latir", LATIR)]:
        if nombre not in grafos(DEST):
            bt("add_function_graph", {"blueprint": {"refPath": DEST}, "graph_name": nombre})
        g = {"refPath": DEST + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)
    bt("compile_blueprint", {"blueprint": {"refPath": DEST}})

    # 2. BeginPlay -> Arrancar, por cirugia.
    g = {"refPath": DEST + ":EventGraph"}
    todos = [(n, info(n)) for n in bt("find_nodes", {"graph": g, "title": ""})]
    if any("Arrancar" in str(i["type_id"]) for _, i in todos):
        out["cirugia"] = "ya estaba"
    else:
        begin = next(((n, i) for n, i in todos if "BeginPlay" in str(i["type_id"])), None)
        if begin is None:
            nodo = bt("add_event", {"blueprint": {"refPath": DEST},
                                    "event_name": "EventBeginPlay"})
            begin = (nodo, info(nodo))
            out["escritas"].append("evento nuevo -> BeginPlay")
        ts = bt("find_node_types", {"graph": g, "type_id_filter": "Arrancar", "context_pins": []})
        tipo = next((str(x) for x in ts if str(x).endswith("|Arrancar")), None)
        if tipo is None:
            return {"error": "no hay tipo de nodo para Arrancar", "out": out}
        sal = exec_pins(begin[1], "output_pins")
        pos = begin[1]["position"]
        nuevo = bt("create_node", {"graph": g, "type_id": tipo,
                                   "pos": {"x": int(pos["x"]) + 300, "y": int(pos["y"])}})
        ent = exec_pins(info(nuevo), "input_pins")
        bt("connect_pins", {"output_pin": pin("EGPD_Output", sal[0]["pin_id"]["index_id"], begin[0]),
                            "input_pin": pin("EGPD_Input", ent[0]["pin_id"]["index_id"], nuevo)})
        out["cirugia"] = "cosido: BeginPlay -> Arrancar"
    bt("compile_blueprint", {"blueprint": {"refPath": DEST}})
    st("save_assets", {"asset_paths": [DEST_RUTA]})

    # 3. ArrojarLanza con el spawn del destello.
    g = {"refPath": PJ + ":ArrojarLanza"}
    out["vaciados"]["ArrojarLanza"] = vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": ARROJAR})
    out["escritas"].append("ArrojarLanza")
    bt("compile_blueprint", {"blueprint": {"refPath": PJ}})
    st("save_assets", {"asset_paths": [PJ_RUTA]})

    out["releido"] = {
        "EventGraph": str(bt("read_graph_dsl", {"graph": {"refPath": DEST + ":EventGraph"}})),
        "Arrancar": str(bt("read_graph_dsl", {"graph": {"refPath": DEST + ":Arrancar"}})),
        "ArrojarLanza": str(bt("read_graph_dsl", {"graph": {"refPath": PJ + ":ArrojarLanza"}})),
    }
    return out

