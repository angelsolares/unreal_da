import json
import math

# Punto 2 del plan de Gabriel, primera rebanada: **cruzar un espejo**.
#
# Crea `BP_DA_Umbral`, lo coloca delante de un nicho midiendo desde el espejo, y
# pone el punto de reaparicion en el centro de la sala. Lo que hace al cruzar:
# marcarse como gastado, romper el espejo y teletransportar al jugador.
#
# NO monta todavia: la ronda de enemigos, la linea de Gabriel al limpiarla, el
# fundido de camara, ni la afirmacion en pantalla. `Afirmacion` y `Encuentro` se
# guardan ya en la instancia para que el siguiente paso solo tenga que leerlos.
#
# ### LA GEOMETRIA DE LA SALA, MEDIDA
#
# Once espejos en un anillo de **radio 1260** alrededor de (0, 0) del submapa,
# cada 30 grados. Falta el de 180 grados: **ese hueco es la entrada**. Gabriel
# esta en (520, 0) mirando justo hacia ella.
#
# En coordenadas del mundo el centro es (-66000, -15000): la Level Instance suma
# (-66000, -15000, 0). Por eso aqui se copia la X/Y del espejo de referencia y no
# se escribe un solo numero del maestro.
#
# ### EL ESPEJO SON DOS ACTORES, Y EL QUE SE ROMPE ES EL SEGUNDO
#
# El diseno decia "el `Espejo_N` al que pertenece, para romperlo". No es ese:
#
#   `Espejo_N`     -> `SM_MMLK_Mirror_Straight_200x300`, el MARCO de piedra
#   `EspejoSup_N`  -> `..._MirrorSurface`, el CRISTAL, con `M_DA_MK_Espejo`
#
# La variable `Espejo` apunta al `EspejoSup_N`.
#
# ### TRES TRAMPAS QUE COSTARON LA TARDE
#
# 1. **`Rendering|SetMaterial` NO es el de las mallas.** Ese id resuelve al de
#    `VolumetricCloudComponent`, y ni con `declaring_class` se puede forzar: no
#    existe para `MeshComponent`. El bueno es **`Rendering|Material|SetMaterial`**,
#    con `Material` en medio. Se encuentra pasando `context_pins` a
#    `find_node_types` con el pin del componente: **ese parametro es el que
#    desambigua**, y hasta ahora se estaba llamando siempre con la lista vacia.
#
# 2. **`SetMaterialByName` no falla: no hace nada.** El nombre que devuelve
#    `get_material_slots` es el importado, y `SetMaterialByName` compara contra el
#    `MaterialSlotName`, que puede ser otro. No hay error, no hay aviso, y el
#    material se queda como estaba. Por indice —que con una sola ranura es
#    inequivoco— funciona a la primera. Si algun dia hace falta el nombre de
#    verdad, existe `Rendering|Material|GetMaterialSlotNames`.
#
# 3. **Un cast fallido se lleva por delante el resto de la funcion, en silencio.**
#    `CastToStaticMeshActor` es un cast CON ejecucion: si falla, sale por su rama
#    de fallo, que esta sin conectar, y la funcion termina. Como la llamaba el
#    evento y despues seguia con `Cruzar`, el teletransporte funcionaba y el
#    espejo no, que es un sintoma que despista mucho. Se quito el cast y se usa
#    `Actor|GetComponentByClass`, que vale para cualquier actor con malla.
#
# ### Y UNA REGLA DEL DSL QUE NO ESTABA ESCRITA
#
# **Un nodo multi-exec termina el flujo que lo contiene.** No se pueden encadenar
# dos `IsValid` en el mismo cuerpo: el segundo da "Unreachable code after
# branch/return". Por eso `RomperEspejo` y `Cruzar` son funciones aparte y no dos
# bloques del evento.
#
# ### COMO SE DIAGNOSTICO
#
# Con una variable `Diag` entera puesta a 1/2/3 en los tres puntos de la funcion y
# leida desde PIE con `get_properties`. Es el sustituto del `PrintString` cuando
# no se puede mirar la pantalla: `Diag = 2` demostro que el componente SI se
# encontraba y que el que no hacia nada era el `SetMaterialByName`. Sin eso se
# habrian seguido probando hipotesis a ciegas.

SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CARPETA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Umbral"
RUTA = CARPETA + "/" + NOMBRE + "." + NOMBRE
CLASE = RUTA + "_C"
ROTO = "/Game/DarkAngels/Materials/Malkuth/M_DA_MK_Espejo_Roto.M_DA_MK_Espejo_Roto"

# Que espejo se prepara. El 3 esta en (0, 1260), perpendicular a la entrada y sin
# Gabriel delante.
CUAL = 3
DENTRO = 110.0                                  # cuanto se mete la caja hacia el centro
CENTRO = {"x": 0.0, "y": 0.0, "z": 100.0}       # reaparicion, en coords del submapa
CAJA = {"x": 150.0, "y": 60.0, "z": 200.0}      # semiejes; el espejo mide 300 de ancho

AFIRMACION = "Eres humano."
ENCUENTRO = "0:2, 2:1"

ROMPER = '''(fn RomperEspejo ()
  (bind _esp (Variables|Default|GetEspejo))
  (bind _c (Actor|GetComponentByClass _esp "/Script/Engine.StaticMeshComponent"))
  (Utilities|IsValid _c
    (:"Is Valid"
      (Rendering|Material|SetMaterial :self _c :ElementIndex 0 :Material "%s"))
    (:"Is Not Valid")))
''' % ROTO

# Las dos llamadas, no solo la primera: en DCS el pawn no gira con la camara, asi
# que sin `SetControlRotation` reapareces mirando hacia donde mirabas antes de
# cruzar, que en una sala circular es desorientacion pura.
CRUZAR = '''(fn Cruzar ()
  (bind _dst (Variables|Default|GetDestino))
  (Utilities|IsValid _dst
    (:"Is Valid"
      (bind _pj (Game|GetPlayerPawn 0))
      (bind _loc (Transformation|GetActorLocation _dst))
      (bind _rot (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0
                   :Yaw (.yaw (Math|Rotator|FindLookatRotation _loc (Transformation|GetActorLocation self)))))
      (Transformation|SetActorLocationAndRotation :self _pj
        :NewLocation _loc :NewRotation _rot :bSweep false :bTeleport true)
      (Pawn|SetControlRotation :self (Game|GetPlayerController 0) :NewRotation _rot))
    (:"Is Not Valid")))
'''

EVENTO = '''(event Collision|EventActorBeginOverlap (OtherActor)
  (if (Variables|Default|GetActivo)
    (bind _pj (Utilities|Casting|CastToBP_CombatCharacter OtherActor))
    (Utilities|IsValid _pj
      (:"Is Valid"
        (Variables|Default|SetActivo false)
        (CallFunction|RomperEspejo)
        (CallFunction|Cruzar))
      (:"Is Not Valid"))))
'''


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g):
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(n)["type_id"])
        if "FunctionEntry" in tid or "FunctionEntry" in n["refPath"]:
            continue
        bt("delete_node", {"node": n})


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {}

    # --- 1. el blueprint ---
    if not ast("exists", {"path": CARPETA + "/" + NOMBRE}):
        bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"
    else:
        out["blueprint"] = "ya estaba"
    bp = {"refPath": RUTA}

    tenia = {}
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": bp})}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c

    def componente(nombre, tipo):
        if nombre in tenia:
            return tenia[nombre]
        return at("add_component", {"owner": bp, "name": nombre,
                                    "component_type": {"refPath": tipo}})

    raiz = componente("Raiz", "/Script/Engine.SceneComponent")
    zona = componente("Zona", "/Script/Engine.BoxComponent")
    at("set_parent_component", {"component": zona, "parent": raiz})
    ot("set_properties", {"instance": zona, "values": json.dumps({
        "BoxExtent": CAJA,
        "RelativeLocation": {"x": 0.0, "y": 0.0, "z": CAJA["z"]},
        "BodyInstance": {"collisionEnabled": "QueryOnly",
                         "collisionProfileName": "OverlapAllDynamic"}})})

    tiene = bt("list_variables", {"blueprint": bp})
    for n, t in (("Afirmacion", "string"), ("Encuentro", "string"), ("Activo", "bool")):
        if n not in tiene:
            bt("add_variable", {"blueprint": bp, "name": n, "type_name": t})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": n, "instance_editable": True})
    for n in ("Destino", "Espejo"):
        if n not in tiene:
            bt("add_object_variable", {"blueprint": bp, "name": n,
                                       "object_class": {"refPath": "/Script/Engine.Actor"}})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": n, "instance_editable": True})

    for nombre, codigo in (("RomperEspejo", ROMPER), ("Cruzar", CRUZAR)):
        grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
        if nombre not in grafos:
            bt("add_function_graph", {"blueprint": bp, "graph_name": nombre})
        g = {"refPath": RUTA + ":" + nombre}
        vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
    eg = {"refPath": RUTA + ":EventGraph"}
    vaciar(eg)
    bt("write_graph_dsl", {"graph": eg, "code": EVENTO})
    bt("compile_blueprint", {"blueprint": bp})
    ast("save_assets", {"asset_paths": [CARPETA + "/" + NOMBRE]})

    # El `true` del bTeleport se comprueba EN EL PIN, no leyendo el grafo.
    for n in bt("find_nodes", {"graph": {"refPath": RUTA + ":Cruzar"}, "title": ""}):
        i = info(n)
        b = [[p["name"], str(p["value"])] for p in i["input_pins"]
             if p["name"] in ("bSweep", "bTeleport")]
        if b:
            out["pines_teleport"] = b

    # --- 2. colocarlo, midiendo desde el espejo ---
    sc("load_level", {"level_path": SUB})
    esp = busca("Espejo_%d" % CUAL)
    sup = busca("EspejoSup_%d" % CUAL)
    if esp is None or sup is None:
        return {"error": "falta el espejo %d" % CUAL, "hecho": out}
    te = at("get_actor_transform", {"actor": esp})

    xd = {"location": CENTRO, "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
          "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
    dst = busca("Destino_Centro")
    if dst is None:
        dst = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": "/Script/Engine.TargetPoint"},
            "name": "Destino_Centro", "xform": xd, "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": dst, "label": "Destino_Centro"})
    at("set_actor_transform", {"actor": dst, "worldspace": True, "xform": xd})

    ang = math.atan2(te["location"]["y"], te["location"]["x"])
    xu = {"location": {"x": te["location"]["x"] - math.cos(ang) * DENTRO,
                       "y": te["location"]["y"] - math.sin(ang) * DENTRO,
                       "z": te["location"]["z"]},
          "rotation": {"pitch": 0.0, "yaw": te["rotation"]["yaw"], "roll": 0.0},
          "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
    etiqueta = "Umbral_%d" % CUAL
    umb = busca(etiqueta)
    if umb is None:
        umb = sc("add_to_scene_from_class", {"actor_type": {"refPath": CLASE},
                                             "name": etiqueta, "xform": xu,
                                             "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": umb, "label": etiqueta})
    at("set_actor_transform", {"actor": umb, "worldspace": True, "xform": xu})

    for k, v in (("Afirmacion", AFIRMACION), ("Encuentro", ENCUENTRO), ("Activo", True)):
        ot("set_properties", {"instance": umb, "values": json.dumps({k: v})})
    ot("set_properties", {"instance": umb,
                          "values": json.dumps({"Destino": {"refPath": dst["refPath"]}})})
    ot("set_properties", {"instance": umb,
                          "values": json.dumps({"Espejo": {"refPath": sup["refPath"]}})})

    out["instancia"] = json.loads(ot("get_properties", {"instance": umb, "properties":
        ["Afirmacion", "Encuentro", "Activo", "Destino", "Espejo"]}))
    out["sitios"] = {"espejo": [round(te["location"][k]) for k in ("x", "y", "z")],
                     "umbral": [round(xu["location"][k]) for k in ("x", "y", "z")],
                     "destino": [round(CENTRO[k]) for k in ("x", "y", "z")]}

    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio"] = ast("is_dirty", {"asset_path": SUB})
    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = sc("get_current_level", {})
    return out
