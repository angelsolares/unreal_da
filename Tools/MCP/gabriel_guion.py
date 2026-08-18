import json

# Fase 1 de Gabriel, punto 1: la presentacion deja de repetirse, TERMINA, y su
# ultima linea enciende el ritual de los espejos.
#
# ANTES: `AlternarDialogo` conmutaba un booleano en el flanco de bajada de
# `Inspeccionando` y escribia uno de dos juegos de texto. Con dos estados nunca
# habia una tercera conversacion.
#
# AHORA: un INDICE (`Paso`) sobre tres arrays paralelos, y una salida al final de
# la cuenta. El detector de flanco, el sitio donde vive y el reparto con el HUD se
# quedan igual: lo unico que cambia es que cuenta.
#
# ### TRES ARRAYS PARALELOS Y NO UN ARRAY DE STRUCTS
#
# En Unreal lo normal seria un struct por pantalla, pero **el MCP no puede crear
# structs de usuario** y `set_properties` escribe structs a medias sin avisar. Los
# arrays de tipos simples si se escriben enteros. Tampoco una sola cadena con
# separador: habria que partirla en cada tick, y el formato de tres campos es
# justo el que el HUD ya sabe pintar.
#
# `Guion1[i]`, `Guion2[i]` y `Guion3[i]` son los tres RENGLONES de la pantalla i.
# **No son tres turnos: el HUD los pinta apilados en el mismo frame.** Anadir una
# pantalla = anadir un elemento a los tres arrays.
#
# ### DONDE VIVE, Y POR QUE NO EN EL INTERACTUABLE
#
# En `BP_DA_GiantBoss`. El sitio aparentemente natural —el evento `Interact`— no
# vale por dos razones que ya costaron trabajo: `interaccion_inspeccionar.py`
# reconstruye ese EventGraph nodo a nodo y borra lo que no sea un evento, y ese
# blueprint lo comparten SIETE interactuables de otras zonas.
#
# Gabriel ya tiene Tick, ya guarda la referencia al interactuable en `Encuadre` y
# ya la usa cada frame. Con `Encuadre` a null —el jefe de la arena— la funcion
# entera no hace nada, y esa guarda es la que protege el otro mapa.
#
# ### LA TRAMPA DEL NODO PURO
#
# Un `bind` sobre un nodo puro no cachea: se reevalua cada vez que alguien tira de
# su salida. En `Paso` importa: se ESCRIBE la variable primero y la comparacion
# LEE la variable, nunca se reutiliza la salida del +1 en dos sitios. Si no, el
# `if` compara contra un valor distinto del que se guardo, compila perfecto y
# falla en silencio.
#
# ### LAS AYUDANTES NO LLEVAN PARAMETROS, A PROPOSITO
#
# El diseno pedia `EscribirPantalla(Paso, Quien)` y `CerrarPresentacion(Quien)`.
# Se montan SIN parametros y leyendo `Paso` y `Encuadre` —que son variables
# miembro— para no depender de `add_function_param`, que es otra superficie del
# MCP sin verificar. El reparto de responsabilidades es el mismo.
#
# ### EL GESTO NO PUEDE IR POR EL INTERACTUABLE
#
# `BP_DA_Interactuable` tiene `Animado`/`AnimHablar`/`AnimReposo` y parece justo lo
# que hace falta, pero ese bloque hace
# `Class|SkeletalMeshActor|GetSkeletalMeshComponent`: solo funciona sobre props
# `SkeletalMeshActor`, como Sariel y Cassiel. Gabriel es un `Character`, asi que el
# montage lo lanza el mismo con `PlayAnimMontage`.
#
# ### DOS IDS QUE SE PARECEN Y NO SON EL MISMO
#
# `Class|BPDAHUD|SetObjective` es el del AHUD, que es el que se quiere.
# `Class|WBPDAHUD|SetObjective` es el del widget UMG. `find_node_types` devuelve
# los dos y el resolver del DSL ya eligio el equivocado en silencio una vez.

BPP = "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss.BP_DA_GiantBoss"
BP = {"refPath": BPP}
SUBASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
MONTAGE = ("/Game/DarkAngels/Animations/Boss/AM_DA_HitTheGroundAttack"
           ".AM_DA_HitTheGroundAttack")

# --- el guion: cuatro pantallas, tres renglones cada una ---
# 01 y 02 son literales del PDF. 03 y 04 son redaccion propia sobre lo que el PDF
# describe ("cada uno muestra un acto de bondad; uno solo refleja sus alas
# negras" / "no hay respuesta de dialogo: el jugador responde caminando").
PANTALLAS = [
    ["¿Qué mensaje traes?", "", ""],
    ["No te pregunté quién pareces ser.",
     "Te pregunté qué mensaje traes.", ""],
    ["Estos espejos guardan tus actos.", "Todos menos uno.", ""],
    ["No respondas con la boca.", "Cruza, y que responda tu conducta.", ""],
]

OBJETIVO = "OBJETIVO: Responde con tu conducta. Cruza los espejos."
OBJETIVO_INDICE = 11        # el HUD solo avanza si el indice sube; arranca en 0

NUEVAS = [("Paso", "int", False),
          ("FaseRitual", "int", True),
          ("ObjetivoTexto", "string", True),
          ("ObjetivoIndice", "int", True)]
ARRAYS = ["Guion1", "Guion2", "Guion3"]
VIEJAS = ["TurnoB", "MensajeA1", "MensajeB1", "MensajeB2"]


ALTERNAR = '''(fn AlternarDialogo ()
  (bind _e (Variables|Default|GetEncuadre))
  (Utilities|IsValid _e
    (:"Is Valid"
      (bind _i (Class|BPDAInteractuable|GetInspeccionando
                 (Utilities|Casting|CastToBP_DA_Interactuable _e)))
      (if (and (Variables|Default|GetHablandoAntes) (not _i))
        (Variables|Default|SetPaso (+ (Variables|Default|GetPaso) 1))
        (if (< (Variables|Default|GetPaso)
               (Utilities|Array|Length (Variables|Default|GetGuion1)))
          (CallFunction|EscribirPantalla)
          (else
            (CallFunction|CerrarPresentacion)
            (CallFunction|ArmarRitual))))
      (Variables|Default|SetHablandoAntes _i))
    (:"Is Not Valid")))
'''

ESCRIBIR = '''(fn EscribirPantalla ()
  (bind _it (Utilities|Casting|CastToBP_DA_Interactuable (Variables|Default|GetEncuadre)))
  (bind _p (Variables|Default|GetPaso))
  (Class|BPDAInteractuable|SetDialogo1 :self _it
    :Dialogo1 (Utilities|Array|Get(acopy) (Variables|Default|GetGuion1) _p))
  (Class|BPDAInteractuable|SetDialogo2 :self _it
    :Dialogo2 (Utilities|Array|Get(acopy) (Variables|Default|GetGuion2) _p))
  (Class|BPDAInteractuable|SetDialogo3 :self _it
    :Dialogo3 (Utilities|Array|Get(acopy) (Variables|Default|GetGuion3) _p)))
'''

# Se apaga la COLISION, no se destruye el actor: `Encuadre` lo lee cada tick, y en
# la fase 3 ese mismo actor vuelve a hacer falta para la rendicion. Sin colision
# DCS deja de encontrarlo y el cartel "[E] Hablar" se apaga solo — el mismo truco
# que ya se usa al recoger un objeto.
CERRAR = '''(fn CerrarPresentacion ()
  (bind _e (Variables|Default|GetEncuadre))
  (bind _it (Utilities|Casting|CastToBP_DA_Interactuable _e))
  (Class|BPDAInteractuable|SetDialogo1 :self _it :Dialogo1 "")
  (Class|BPDAInteractuable|SetDialogo2 :self _it :Dialogo2 "")
  (Class|BPDAInteractuable|SetDialogo3 :self _it :Dialogo3 "")
  (Collision|SetActorEnableCollision :self _e :bNewActorEnableCollision false))
'''

ARMAR = '''(fn ArmarRitual ()
  (Variables|Default|SetFaseRitual 1)
  (Animation|PlayAnimMontage :self self :AnimMontage "%s" :InPlayRate 1.0)
  (bind _hud (Utilities|Casting|CastToBP_DA_HUD (HUD|GetHUD (Game|GetPlayerController 0))))
  (Utilities|IsValid _hud
    (:"Is Valid"
      (Class|BPDAHUD|SetObjective :self _hud
        :InText (Variables|Default|GetObjetivoTexto)
        :InIndex (Variables|Default|GetObjetivoIndice)))
    (:"Is Not Valid")))
''' % MONTAGE

# `AlternarDialogo` va la ultima: llama a las otras tres, y si no existen todavia
# el `|EscribirPantalla` no resuelve.
FUNCIONES = [("EscribirPantalla", ESCRIBIR), ("CerrarPresentacion", CERRAR),
             ("ArmarRitual", ARMAR), ("AlternarDialogo", ALTERNAR)]


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


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g):
    """Deja el grafo con su nodo de entrada y nada mas.

    `write_graph_dsl` no reemplaza el cuerpo de una funcion: anade otra copia. Y
    `remove_function_graph` + `add_function_graph` tampoco vale, porque el segundo
    NO reutiliza el nombre y deja un `_0` huerfano (en el HUD ya hay cuatro).
    """
    borrados = 0
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(n)["type_id"])
        if "FunctionEntry" in tid or "FunctionEntry" in n["refPath"]:
            continue
        bt("delete_node", {"node": n})
        borrados += 1
    return borrados


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

    # --- 1. variables ---
    tiene = bt("list_variables", {"blueprint": BP})
    out["creadas"] = []
    for n, t, editable in NUEVAS:
        if n not in tiene:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": t})
            out["creadas"].append(n)
        if editable:
            bt("set_variable_instance_editable",
               {"blueprint": BP, "variable_name": n, "instance_editable": True})
    for n in ARRAYS:
        if n not in tiene:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": "string",
                                "container_type": "ARRAY"})
            out["creadas"].append(n)
        bt("set_variable_instance_editable",
           {"blueprint": BP, "variable_name": n, "instance_editable": True})

    # --- 2. las cuatro funciones ---
    out["vaciados"] = {}
    for nombre, codigo in FUNCIONES:
        grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
        if nombre not in grafos:
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
    bt("compile_blueprint", {"blueprint": BP})

    # --- 3. fuera lo viejo, ya sin referencias ---
    tiene = bt("list_variables", {"blueprint": BP})
    out["borradas"] = []
    for n in VIEJAS:
        if n in tiene:
            bt("remove_variable", {"blueprint": BP, "name": n})
            out["borradas"].append(n)
    bt("compile_blueprint", {"blueprint": BP})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [BPP.split(".")[0]]})

    # --- 4. el `false` de la colision se comprueba EN EL PIN, no leyendo el grafo ---
    for n in bt("find_nodes", {"graph": {"refPath": BPP + ":CerrarPresentacion"},
                               "title": "Collision"}):
        out["pin_colision"] = [[p["name"], str(p["value"])] for p in info(n)["input_pins"]]

    # --- 5. los textos, en la INSTANCIA: las variables nuevas de la clase no
    #        llegan a los actores ya colocados ---
    sc("load_level", {"level_path": SUBASSET})
    jefe = busca("GC2_Gabriel")
    inter = busca("Interact_Gabriel")
    if jefe is None or inter is None:
        return {"error": "falta GC2_Gabriel o Interact_Gabriel", "hecho": out}

    for idx, nombre in enumerate(ARRAYS):
        ot("set_properties", {"instance": jefe,
                              "values": json.dumps({nombre: [p[idx] for p in PANTALLAS]})})
    ot("set_properties", {"instance": jefe,
                          "values": json.dumps({"objetivoTexto": OBJETIVO})})
    ot("set_properties", {"instance": jefe,
                          "values": json.dumps({"objetivoIndice": OBJETIVO_INDICE})})
    ot("set_properties", {"instance": jefe, "values": json.dumps({"faseRitual": 0})})

    # El interactuable arranca en la pantalla 0, por si una pasada anterior lo dejo
    # en otra.
    for k, v in (("Dialogo1", PANTALLAS[0][0]), ("Dialogo2", PANTALLAS[0][1]),
                 ("Dialogo3", PANTALLAS[0][2])):
        ot("set_properties", {"instance": inter, "values": json.dumps({k: v})})

    out["instancia"] = json.loads(ot("get_properties", {"instance": jefe, "properties":
        ["Guion1", "Guion2", "Guion3", "objetivoTexto", "objetivoIndice", "faseRitual"]}))
    out["interactuable"] = json.loads(ot("get_properties", {"instance": inter,
        "properties": ["Verbo", "Dialogo1", "Dialogo2", "Dialogo3"]}))

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [SUBASSET]})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": SUBASSET})
    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = sc("get_current_level", {})
    return out
