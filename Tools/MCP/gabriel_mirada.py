import json

# Gabriel sigue al jugador con la mirada, y se voltea si te pones detras.
#
# ### LA MECANICA YA EXISTIA EN DCS
#
# `AnimInstance_BaseCharacter` —la clase padre de los AnimBP de DCS— ya trae
# `LookAtPitch`, `LookAtYaw`, `LookAtAlpha`, las funciones `UpdateLookAtData` y
# `GetLookAtTargetRotation`, y un grafo `SkeletalControls` en `ABP_CombatCharacter`.
# El turn-in-place tambien: estados `TurnInPlace`, `UpdateRootYawOffset`,
# `ProcessTurnYawCurve`. O sea que los enemigos de DCS ya hacen esto.
#
# Gabriel no puede usarlo porque hereda de `BP_Giant` y corre `ABP_Giant`, del pack,
# cuyo AnimGraph es una maquina de estados con `Idle_Walk_Run` y `Death_Anim` y nada
# mas: cero skeletal controls. Asi que se replica.
#
# ### EL ANIMBP ES UNA COPIA, Y SE ASIGNA POR INSTANCIA
#
# `ABP_Giant` esta en `GiantBossProject`, que es asset de pago y no se toca. Se
# duplica a `/Game/DarkAngels/Blueprints/Bosses/ABP_DA_Gabriel` (el duplicado
# conserva el `TargetSkeleton`, comprobado).
#
# **El `animClass` se pone en el COMPONENTE DE LA INSTANCIA `GC2_Gabriel`, no en la
# clase.** Si se pusiera en `BP_DA_GiantBoss` lo heredaria tambien el jefe de la
# arena, que debe seguir con `ABP_Giant` intacto.
#
# ### LA CADENA DEL ANIMGRAPH
#
#   GiantStateMachine -> Slot'DefaultSlot' -> LocalToComponent
#     -> LookAt(spine_05, alpha*0.3, clamp 40)
#     -> LookAt(neck_01,  alpha*0.5, clamp 40)
#     -> LookAt(head,     alpha*1.0, clamp 70)
#   -> ComponentToLocal -> OutputPose
#
# Va **detras del Slot** a proposito: asi la mirada sigue durante los montages de
# ataque. Y se reparte entre tres huesos porque un `LookAt` solo en la cabeza da
# cuello de buho; el padre aporta poco y el hijo remata.
#
# `LookAt` trabaja en Component Space, de ahi los dos nodos de conversion: por MCP
# no se insertan solos como en el editor.
#
# **`LookAtLocation` hay que EXPONERLO COMO PIN** para poder moverlo por frame; de
# fabrica es solo un ajuste del panel. Se hace poniendo `bShowPin = true` en su
# entrada de `showPinForProperties`. Dos trampas del setter de arrays:
#   - No admite cambiar tamanio y contenido a la vez ("insertion points are
#     ambiguous"), asi que se reescribe el array con el MISMO numero de elementos.
#   - Con tamanio igual **no** se pierde el ultimo elemento (19 antes, 19 despues).
#
# ### EL GIRO DEL CUERPO
#
# En `BP_DA_GiantBoss`: variable `SigueAlJugador` (Instance Editable, **default
# false** para que el jefe de la arena no se entere), variable `Girando`, funcion
# `MirarAlJugador` y un `EventTick` que la llama.
#
# El Tick se engancha **por cirugia de nodos**, nunca con `write_graph_dsl`: ese
# EventGraph tiene el BeginPlay, TakeDamage y OnHit buenos y el DSL lo reescribe
# entero.
#
# El angulo sale de `GetHorizontalDotProductTo`, que ya ignora la Z: 1 = de frente,
# -1 = a la espalda. Con histeresis, que si no se queda parado a mitad de giro:
# empieza a girar por debajo de 0,34 (~70 grados) y no para hasta pasar de 0,99.
#
# ### VERIFICADO EN PIE
#
# Jugador delante: yaw 180, quieto. Jugador detras: yaw 180 -> -60 (`Girando` true)
# -> -6,7 (`Girando` false). Encara al jugador y para.
#
# ### PENDIENTE
#
# - **El eje del `LookAt` sigue en el de fabrica (0,1,0) local.** No se ha podido
#   calibrar: `CaptureViewport` devuelve el viewport del EDITOR, no el de PIE, asi
#   que la mirada hay que mirarla a ojo jugando. Si apunta torcido, es este campo.
# - **En el editor Gabriel se ve como un amasijo** (bounds 782 de alto, bajando a
#   z=-216) mientras que en PIE esta perfecto (594, de -19 a 575). Solo afecta a la
#   previsualizacion. Descartado que sea la cadena de `LookAt` (puenteada, sigue
#   igual), el AnimGraph (restaurado al original, sigue igual), las variables
#   (`speed` 0, `death_anim` false, correctas) y la pose de referencia de
#   `SK_DA_Gabriel` (limpia, comprobada con `CaptureAssetImage`). Sin causa.

ABP_ORIG = "/Game/GiantBossProject/Anims/ABP_Giant"
ABP = "/Game/DarkAngels/Blueprints/Bosses/ABP_DA_Gabriel"
JEFE = "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss"
SUBASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"

RADIO = 4000.0        # a partir de aqui ni mira ni gira
UMBRAL = 0.34         # dot: ~70 grados, donde el cuerpo toma el relevo
ALINEADO = 0.99       # dot al que deja de girar
VELOCIDAD = 2.0       # RInterpTo del giro

# hueso, clamp en grados, variable de alpha
HUESOS = [("spine_05", 40.0, "AlphaEspalda"),
          ("neck_01", 40.0, "AlphaCuello"),
          ("head", 70.0, "AlphaCabeza")]

MIRADA = '''(event EventBlueprintUpdateAnimation (DeltaTimeX)
  (bind _owner (Utilities|Casting|CastToBP_Giant (Animation|TryGetPawnOwner)))
  (Variables|Default|SetSpeed (Math|Vector|VectorLength (Transformation|GetVelocity _owner)))
  (Variables|Default|SetDeathAnim (Class|BPGiant|GetDeath _owner))
  (bind _jug (Game|GetPlayerPawn 0))
  (Utilities|IsValid _jug
    (:"Is Valid"
      (bind _ploc (Transformation|GetActorLocation _jug))
      (Variables|Default|SetPuntoDeMirada (+ _ploc (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 60.0)))
      (bind _d (Math|Vector|VectorLength (- _ploc (Transformation|GetActorLocation _owner))))
      (bind _a (select (< _d 4000.0) 1.0 0.0))
      (Variables|Default|SetAlphaCabeza _a)
      (Variables|Default|SetAlphaCuello (* _a 0.5))
      (Variables|Default|SetAlphaEspalda (* _a 0.3)))
    (:"Is Not Valid"
      (Variables|Default|SetAlphaCabeza 0.0)
      (Variables|Default|SetAlphaCuello 0.0)
      (Variables|Default|SetAlphaEspalda 0.0))))
'''

# OJO: `GetPlayerPawn` es null en el editor. Sin el `IsValid` esto llena el log de
# "Accessed None" y ademas revienta cualquier `set_properties` sobre el actor.

GIRO = '''(fn MirarAlJugador ()
  (if (Variables|Default|GetSigueAlJugador)
    (bind _jug (Game|GetPlayerPawn 0))
    (Utilities|IsValid _jug
      (:"Is Valid"
        (bind _d (Math|Vector|VectorLength (- (Transformation|GetActorLocation _jug) (Transformation|GetActorLocation self))))
        (if (< _d 4000.0)
          (bind _dot (Transformation|GetHorizontalDotProductTo :OtherActor _jug))
          (if (< _dot 0.34)
            (Variables|Default|SetGirando true))
          (if (> _dot 0.99)
            (Variables|Default|SetGirando false))
          (if (Variables|Default|GetGirando)
            (bind _obj (Math|Rotator|FindLookatRotation (Transformation|GetActorLocation self) (Transformation|GetActorLocation _jug)))
            (Transformation|SetActorRotation
              :NewRotation (Math|Interpolation|RInterpTo
                             :Current (Transformation|GetActorRotation self)
                             :Target (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (.yaw _obj))
                             :DeltaTime (Utilities|Time|GetWorldDeltaSeconds)
                             :InterpSpeed 2.0)
              :bTeleportPhysics false))
          (else
            (Variables|Default|SetGirando false))))
      (:"Is Not Valid"))))
'''


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def pin(nodo, direccion, nombre):
    for i in bt("get_node_infos", {"nodes": [nodo]}):
        lista = i["input_pins"] if direccion == "EGPD_Input" else i["output_pins"]
        for idx, p in enumerate(lista):
            if p["name"] == nombre:
                return {"direction": direccion, "index_id": idx, "node": nodo}
    return None


def une(nsal, psal, nent, pent):
    bt("connect_pins", {"output_pin": pin(nsal, "EGPD_Output", psal),
                        "input_pin": pin(nent, "EGPD_Input", pent)})


def exponer(nodo, propiedad):
    """Saca una propiedad del nodo como pin. Mismo tamanio de array o falla."""
    arr = json.loads(ot("get_properties", {"instance": nodo,
                                           "properties": ["showPinForProperties"]}))["showPinForProperties"]
    for e in arr:
        if e["propertyName"] == propiedad:
            e["bShowPin"] = True
    ot("set_properties", {"instance": nodo,
                          "values": json.dumps({"showPinForProperties": arr})})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {}

    # --- 1. la copia del AnimBP ---
    if not ast("exists", {"path": ABP}):
        ast("duplicate", {"path": ABP_ORIG, "new_path": ABP})
        out["abp"] = "duplicado"
    else:
        out["abp"] = "ya estaba"
    bp = {"refPath": ABP + ".ABP_DA_Gabriel"}
    ag = {"refPath": ABP + ".ABP_DA_Gabriel:AnimGraph"}
    eg = {"refPath": ABP + ".ABP_DA_Gabriel:EventGraph"}

    # --- 2. variables y datos de mirada ---
    tiene = bt("list_variables", {"blueprint": bp})
    for n, t in (("PuntoDeMirada", "Vector"), ("AlphaCabeza", "float"),
                 ("AlphaCuello", "float"), ("AlphaEspalda", "float")):
        if n not in tiene:
            bt("add_variable", {"blueprint": bp, "name": n, "type_name": t})
    bt("write_graph_dsl", {"graph": eg, "code": MIRADA})

    # --- 3. la cadena de LookAt ---
    l2c = bt("create_node", {"graph": ag, "type_id": "Animation|ConvertSpaces|LocalToComponent",
                             "pos": {"x": -900, "y": 400}})
    c2l = bt("create_node", {"graph": ag, "type_id": "Animation|ConvertSpaces|ComponentToLocal",
                             "pos": {"x": 300, "y": 400}})
    nodos = []
    for i, (hueso, clamp, var) in enumerate(HUESOS):
        n = bt("create_node", {"graph": ag, "type_id": "Animation|SkeletalControls|LookAt",
                               "pos": {"x": -600 + i * 300, "y": 400}})
        exponer(n, "LookAtLocation")
        st = json.loads(ot("get_properties", {"instance": n, "properties": ["node"]}))["node"]
        st["boneToModify"]["boneName"] = hueso
        st["lookAtClamp"] = clamp
        st["interpolationTime"] = 0.25
        ot("set_properties", {"instance": n, "values": json.dumps({"node": st})})
        nodos.append((n, var))

    raiz = bt("find_nodes", {"graph": ag, "title": "Output Pose"})[0]
    slot = bt("find_nodes", {"graph": ag, "title": "DefaultSlot"})[0]
    bt("break_pins", {"output_pin": pin(slot, "EGPD_Output", "Pose"),
                      "input_pin": pin(raiz, "EGPD_Input", "Result")})
    une(slot, "Pose", l2c, "LocalPose")
    anterior, pin_ant = l2c, "ComponentPose"
    for n, _v in nodos:
        une(anterior, pin_ant, n, "ComponentPose")
        anterior, pin_ant = n, "Pose"
    une(anterior, pin_ant, c2l, "ComponentPose")
    une(c2l, "Pose", raiz, "Result")

    getter = bt("create_node", {"graph": ag, "type_id": "Variables|Default|GetPuntoDeMirada",
                                "pos": {"x": -900, "y": 700}})
    for i, (n, var) in enumerate(nodos):
        une(getter, "PuntoDeMirada", n, "LookAtLocation")
        g = bt("create_node", {"graph": ag, "type_id": "Variables|Default|Get" + var,
                               "pos": {"x": -600 + i * 300, "y": 800}})
        une(g, var, n, "Alpha")
    bt("compile_blueprint", {"blueprint": bp})

    # --- 4. el giro, en el jefe ---
    jbp = {"refPath": JEFE + ".BP_DA_GiantBoss"}
    tiene = bt("list_variables", {"blueprint": jbp})
    for n in ("SigueAlJugador", "Girando"):
        if n not in tiene:
            bt("add_variable", {"blueprint": jbp, "name": n, "type_name": "bool"})
    bt("set_variable_instance_editable", {"blueprint": jbp, "variable_name": "SigueAlJugador",
                                          "instance_editable": True})
    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": jbp})]
    if "MirarAlJugador" not in grafos:
        bt("add_function_graph", {"blueprint": jbp, "graph_name": "MirarAlJugador"})
    bt("write_graph_dsl", {"graph": {"refPath": JEFE + ".BP_DA_GiantBoss:MirarAlJugador"},
                           "code": GIRO})

    # El Tick, por cirugia: el EventGraph NO se toca con DSL.
    jeg = {"refPath": JEFE + ".BP_DA_GiantBoss:EventGraph"}
    tick = bt("find_nodes", {"graph": jeg, "title": "Tick"})
    t = tick[0] if tick else bt("create_node", {"graph": jeg, "type_id": "AddEvent|EventTick",
                                                "pos": {"x": -1800, "y": 2400}})
    llamada = bt("create_node", {"graph": jeg, "type_id": "CallFunction|MirarAlJugador",
                                 "pos": {"x": -1450, "y": 2400}})
    bt("connect_pins", {"output_pin": pin(t, "EGPD_Output", "then"),
                        "input_pin": pin(llamada, "EGPD_Input", "execute")})
    bt("compile_blueprint", {"blueprint": jbp})

    # Los literales `true` del DSL: releer SIEMPRE.
    out["booleanos"] = []
    for n in bt("find_nodes", {"graph": {"refPath": JEFE + ".BP_DA_GiantBoss:MirarAlJugador"},
                               "title": "Girando"}):
        for i in bt("get_node_infos", {"nodes": [n]}):
            out["booleanos"].append([i["type_id"],
                                     [[p["name"], str(p["value"])] for p in i["input_pins"]]])

    ast("save_assets", {"asset_paths": [ABP, JEFE]})
    return out
