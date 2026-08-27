# -*- coding: utf-8 -*-
#
# EL PILAR DE LUZ DEL ARMA EN EL SUELO (§9, fila «Arma disponible»).
#
# ### QUE PIDE EL PDF, Y QUE HABIA
#
# El §9 pide para un arma disponible: «brillo celestial corto + sonido
# identificable + prompt contextual discreto». De los tres:
#
#   - **El prompt YA ESTABA**: `BP_DA_DroppedWeapon` hereda de
#     `BP_DA_Interactuable`, con su cartel y su `OcultarCartel`.
#   - **El brillo YA ESTABA A MEDIAS**: hay un `PointLightComponent` llamado `Luz`
#     y un `PulsarLuz` que le late la intensidad en el Tick,
#     `6000 * (0.78 + 0.22*sin(t*2.6))`. Lo que NO tenia es color —salia blanca— ni
#     forma de verse de lejos: una luz puntual se apaga con la distancia y a veinte
#     metros el arma no existe.
#   - **El sonido**, desde el 26/08: se dispara aqui mismo, al final de
#     `MontarPilar`, con `Audio|PlaySoundatLocation`. Va donde el brillo porque
#     los dos anuncian LO MISMO —"hay un arma ahi"— y separarlos seria que un dia
#     uno suene y el otro no. El cue lleva su propia atenuacion dentro, asi que
#     aqui no se le pasa: solo el sonido y el sitio.
#
#     OJO: `Audio|PlaySoundatLocation` NO tiene pin de contexto de mundo. El
#     primer argumento es el SONIDO, no `self`.
#
# OJO A ESTO SI VUELVES A AUDITAR EL §9: la auditoria del 26/08 dijo «no existe
# ningun feedback» porque mire `BP_DA_WeaponDropComponent` —el componente que
# SUELTA el arma— en vez de `BP_DA_DroppedWeapon`, que es el arma soltada. El
# componente no tiene ni un nodo de VFX y es verdad; el actor si.
#
# ### LO QUE MONTA ESTO
#
# Un **pilar de luz celestial** que sale del arma hacia arriba y se ve desde el
# otro lado de la arena: un cilindro alto con `M_DA_HazLuz` —aditivo, unlit,
# two-sided, con parametros `Color`, `Brillo` y `Opacidad`—, que es **el mismo haz
# que ya usan los orbes de las Sefirot**. No se estrena material.
#
# Y de paso la `Luz` que ya estaba pasa a azul celeste y con radio de atenuacion,
# para que ademas tiña el suelo alrededor del arma. El pilar te dice DONDE desde
# lejos; la luz te dice QUE hay algo ahi cuando llegas.
#
# El latido es uno solo: `PulsarLuz` ya movia la intensidad de la luz, y ahora
# ademas ensancha y estrecha el pilar con el MISMO factor. Si laten por separado
# se nota y queda sucio.
#
# ### POR QUE VIVE EN EL ACTOR Y NO EN QUIEN LO SUELTA
#
# `BP_DA_DroppedWeapon` es NUESTRO y es por donde pasan todas las armas del suelo,
# las suelte quien las suelte. Ademas se destruye al recogerla (el `EventInteract`
# acaba en `DestroyActor` por los cuatro caminos), asi que **el pilar se apaga solo
# y no hay que acordarse de apagarlo**. Colgarlo del `WeaponDropComponent` habria
# sido acordarse.
#
# ### DONDE SE ENGANCHA
#
# Por cirugia de UN nodo en el `EventBeginPlay`, que hoy es solo
# `(event EventBeginPlay (|Parent:BeginPlay))`. Aqui la cirugia es aun mas barata
# que en `BP_DA_Arena`: el pin de ejecucion de `Parent: BeginPlay` esta LIBRE, asi
# que no hay que cortar ninguna arista — solo conectar.
#
# El EventGraph NO se reescribe: lleva el `EventInteract` entero, que es el camino
# de recogida, y reescribirlo por DSL es justo el riesgo que no toca correr aqui.
#
# ### LOS NUMEROS, Y COMO SE TOCAN
#
# `AlturaPilar` (1200 uu, unos 6,7 Malakhs) es variable del blueprint: se cambia en
# el panel de la instancia y ya. **El color, el brillo y la opacidad se tocan
# abriendo `MI_DA_PilarArma` en el editor**, sin script y sin recompilar. El ancho
# y el radio de la luz viven aqui arriba.
#
# ### LAS DOS TRAMPAS DEL ESCRITOR, CAZADAS POR EL PREVUELO
#
# 1. **`Game|AddComponentbyClass` NO tiene aqui los cuatro pines que enseña el
#    lector.** `BP_DA_AuraComponent` se lee con
#    `(Game|AddComponentbyClass owner "..." false 0)`, y copiarlo da:
#
#        received 4 positional arg(s) but has 2 data input pin(s).
#        Available: ['self', 'Class']
#
#    Con dos basta: los que no se ven se quedan en su defecto, que es justo lo que
#    queremos (auto-attach al root, transform identidad).
#
# 2. **`Rendering|Material|SetScalarParameterValue` SALE DOS VECES** en
#    `find_node_types` —la del material y la de un Parameter Collection— y el
#    escritor elige en silencio la equivocada:
#
#        Could not connect pin MatPilar to Collection.
#
#    En vez de pelearse con la ambiguedad, el look se saco a `MI_DA_PilarArma` y el
#    grafo solo hace `Rendering|SetMaterial` —ese si es unico—. Salio mejor diseño
#    que el original: los numeros del look quedan donde Angel puede tocarlos.
#    Y `SetMaterial` tiene los suyos, que costaron dos vueltas mas:
#    `Rendering|SetMaterial` es **el de un Volumetric Cloud Component** —el nombre
#    corto no es el generico—. El bueno es `Rendering|Material|SetMaterial`, con
#    (self: Primitive Component, ElementIndex, Material). Se ve de un vistazo con
#    `get_node_type_pins`, que devuelve un DICT con `input_pins`, no una lista:
#        d = bt("get_node_type_pins", {"graph": g, "type_id": tid})
#        ["%s:%s" % (p["name"], p["type_id"]) for p in d["input_pins"]]

import json

BPP = "/Game/DarkAngels/Blueprints/Combat/BP_DA_DroppedWeapon.BP_DA_DroppedWeapon"
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_DroppedWeapon"
BP = {"refPath": BPP}
SCRATCH = "ZZProbePilar"

# El look del pilar NO se fija por codigo: vive en `MI_DA_PilarArma`, un material
# instance de `M_DA_HazLuz` con Color (0.30, 0.62, 1.0), Brillo 3 y Opacidad 0.30.
# Lo crea `arma_pilar_luz_material.py` y se toca abriendolo en el editor, sin
# tocar este script ni recompilar nada. Ver la nota 2 de las trampas.
MI_PILAR = "/Game/DarkAngels/Materials/MI_DA_PilarArma.MI_DA_PilarArma"
CILINDRO = "/Engine/BasicShapes/Cone.Cone"   # ver EL CONO, ABAJO
# El sonido del arma disponible, la otra mitad de la fila del §9. Lo construye
# `arma_sonido_disponible.py`; la atenuacion va DENTRO del cue, no aqui.
SONIDO = "/Game/DarkAngels/Audio/SC_DA_ArmaDisponible.SC_DA_ArmaDisponible"

# Azul celeste: mas frio que blanco, sin llegar a azul de neon. Aqui solo para la
# luz puntual, que no es un material y no puede salir del MI.
COLOR = "(Utilities|Struct|MakeLinearColor 0.30 0.62 1.0 1.0)"
ANCHO = 0.75          # SUELO del diametro (75 cm). El de verdad sale del arma:
                      # ver 'EL PILAR CUBRE EL ARMA ENTERA' abajo.
RADIO_LUZ = 900.0     # atenuacion de la luz puntual que ya estaba

# EL CONO, Y NO EL CILINDRO. La primera version usaba
# `/Engine/BasicShapes/Cylinder`, y en juego se leia como un TUBO DE PLASTICO: el
# cilindro es una malla cerrada, asi que arriba se ve la TAPA —un disco duro
# recortado contra el cielo— y el haz no se desvanece por ningun lado. El cono
# tiene el vertice arriba: la base envuelve el arma y se va afilando, que es como
# se lee un haz de luz. La tapa deja de existir porque el cono no la tiene.
#
# EL PILAR CUBRE EL ARMA ENTERA, NO SU PIVOTE. En la primera foto en juego el haz
# salia de UN EXTREMO de la lanza: estaba centrado en `GetActorLocation`, y el
# pivote de un arma de DCS esta en la empuñadura, no en su centro. Ahora
# `PulsarLuz` lee `GetLocalBounds` del mesh, centra el pilar en el CENTRO de esa
# caja —pasado a mundo con el transform del mesh, que el arma queda tumbada en
# cualquier direccion— y le da de diametro el LADO MAYOR de la caja. Asi el pilar
# envuelve el arma entera, la mida lo que la mida: una lanza de 2 m pide 2 m de
# pilar, y una daga se queda en el suelo de 75 cm.
#
# Se lee del MESH y no del actor a proposito: `GetActorBounds` incluiria al propio
# pilar —que es un componente del actor— y cada tick lo haria mas gordo. Es un
# bucle de realimentacion, no un detalle.
#
# EL PILAR NO PUEDE COLGAR DE LA ROTACION DEL ARMA, y esto se vio en la primera
# foto: salia TORCIDO, apuntando a donde hubiera quedado mirando la lanza. El arma
# cae simulando fisica y al posarse `Posar` le pasa al ACTOR la rotacion con la que
# quedo el mesh —`SetActorLocationAndRotation(self, ..., GetWorldRotation(mesh))`—,
# asi que cualquier hijo del root hereda el tumbo. Medido: el arma en
# (-2354, -156, 115) y su pilar en (-2284, 388, -127), o sea metido en el suelo.
#
# La cura: el transform del pilar lo lleva `PulsarLuz`, que ya corre cada Tick, y lo
# fija en COORDENADAS DE MUNDO —rotacion cero y base sobre el arma—. Por eso
# `MontarPilar` no pone ni posicion ni escala: hay UN solo dueño del transform.
#
# El cilindro de Engine mide 100 de alto y su pivote esta en el CENTRO: por eso la
# escala Z es alto/100 y el centro va alto/2 por encima del arma.
MONTAR = '''(fn MontarPilar ()
  (bind _alto (Variables|Default|GetAlturaPilar))
  (bind _nuevo (Game|AddComponentbyClass self "/Script/Engine.StaticMeshComponent"))
  (Variables|Default|SetPilar (Utilities|Casting|CastToStaticMeshComponent _nuevo))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetPilar) "%(cil)s")
  (Rendering|Material|SetMaterial (Variables|Default|GetPilar) 0 "%(mi)s")
  (Collision|SetCollisionEnabled (Variables|Default|GetPilar))
  (Rendering|Components|Light|SetLightColor (Variables|Default|GetLuz) %(color)s)
  (Rendering|Lighting|SetAttenuationRadius (Variables|Default|GetLuz) %(radio)s)
  (Audio|PlaySoundatLocation :Sound "%(sonido)s" :Location (Transformation|GetActorLocation self)))
''' % {"cil": CILINDRO, "mi": MI_PILAR, "color": COLOR, "ancho": ANCHO,
       "radio": RADIO_LUZ, "sonido": SONIDO}

# UN SOLO LATIDO para la luz y el pilar. El factor es el que ya tenia `PulsarLuz`;
# no se cambia, se comparte.
PULSAR = '''(fn PulsarLuz ()
  (bind _p (+ 0.78 (* 0.22 (Math|Trig|Sin(Radians) (* (Utilities|Time|GetGameTimeInSeconds) 2.6)))))
  (bind _pilar (Variables|Default|GetPilar))
  (bind _alto (Variables|Default|GetAlturaPilar))
  (bind _mesh (Variables|Default|GetMesh))
  (bind (_min _max) (Components|StaticMesh|GetLocalBounds _mesh))
  (bind _centro (Math|Transform|TransformLocation (Transformation|GetWorldTransform _mesh) (Math|Vector|MakeVector (/ (+ (.x _min) (.x _max)) 2.0) (/ (+ (.y _min) (.y _max)) 2.0) (/ (+ (.z _min) (.z _max)) 2.0))))
  (bind _largo (Math|Float|Max(Float) (Math|Float|Max(Float) (- (.x _max) (.x _min)) (- (.y _max) (.y _min))) (- (.z _max) (.z _min))))
  (bind _ancho (* (Math|Float|Max(Float) (/ _largo 100.0) %(ancho)s) (+ 0.85 (* 0.15 _p))))
  (Rendering|Components|Light|SetIntensity (Variables|Default|GetLuz) (* 6000.0 _p))
  (Utilities|IsValid _pilar
    (:"Is Valid"
      (Transformation|SetWorldRotation _pilar (Math|Rotator|MakeRotator 0.0))
      (Transformation|SetWorldLocation _pilar (Math|Vector|MakeVector (.x _centro) (.y _centro) (+ (.z (Transformation|GetActorLocation self)) (* _alto 0.5))))
      (Transformation|SetRelativeScale3D _pilar (Math|Vector|MakeVector _ancho _ancho (* _alto 0.01))))))
''' % {"ancho": ANCHO}

VARIABLES = [
    ("Pilar", "StaticMeshComponent", "", ""),
    ("AlturaPilar", "double", "1200.0", ""),
]
FUNCIONES = [("MontarPilar", MONTAR), ("PulsarLuz", PULSAR)]

# La cirugia: colgar la llamada del pin libre de `Parent: BeginPlay`.
INJERTO_GRAFO = "EventGraph"
INJERTO_LLAMA = "MontarPilar"
INJERTO_TRAS = "Parent: BeginPlay"


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


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


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
        i = m.find("does not exist")
        vaciar(g)
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 70):i + 14]) if i > 0 else m[:200]


def pin(direccion, indice, nodo):
    return {"direction": direccion, "index_id": indice, "node": nodo}


def exec_pins(inf, clave):
    return [p for p in inf[clave] if str(p["type_id"]) == "Exec"]


def injertar():
    """Cuelga `MontarPilar` del pin libre de `Parent: BeginPlay`. Idempotente, y
    aborta sin tocar en cuanto el grafo no sea el que espera."""
    g = {"refPath": BPP + ":" + INJERTO_GRAFO}
    tipos = bt("find_node_types", {"graph": g, "type_id_filter": INJERTO_LLAMA,
                                   "context_pins": []})
    tipo = next((str(t) for t in tipos if INJERTO_LLAMA in str(t)), None)
    if tipo is None:
        return "ABORTADO: el editor no ofrece tipo de nodo para " + INJERTO_LLAMA

    # OJO: el type_id que se LEE de un nodo de funcion propia es "|MontarPilar",
    # con la categoria VACIA, y el que se pasa a `create_node` es
    # "CallFunction|MontarPilar". Comparar los dos en crudo NO casa nunca y la
    # segunda pasada se cree que no esta puesto. Se compara por el nombre.
    todos = bt("find_nodes", {"graph": g, "title": ""})
    for n in todos:
        if INJERTO_LLAMA in str(info(n)["type_id"]):
            return "ya estaba"

    padres = bt("find_nodes", {"graph": g, "title": INJERTO_TRAS})
    if len(padres) != 1:
        return "ABORTADO: %d nodos '%s', esperaba 1" % (len(padres), INJERTO_TRAS)
    padre = padres[0]
    inf_padre = info(padre)
    salidas = exec_pins(inf_padre, "output_pins")
    if len(salidas) != 1:
        return "ABORTADO: '%s' no tiene exactamente una salida exec" % INJERTO_TRAS
    if salidas[0]["connected_pins"]:
        return ("ABORTADO: la salida de '%s' YA esta conectada; alguien metio algo "
                "en BeginPlay y hay que mirar donde encaja esto" % INJERTO_TRAS)

    pos = inf_padre["position"]
    nuevo = bt("create_node", {"graph": g, "type_id": tipo,
                               "pos": {"x": int(pos["x"]) + 320, "y": int(pos["y"])}})
    inf_nuevo = info(nuevo)
    ent = exec_pins(inf_nuevo, "input_pins")
    if len(ent) != 1:
        bt("delete_node", {"node": nuevo})
        return "ABORTADO: el nodo nuevo no tiene un unico exec de entrada"
    bt("connect_pins", {
        "output_pin": pin("EGPD_Output", salidas[0]["pin_id"]["index_id"], padre),
        "input_pin": pin("EGPD_Input", ent[0]["pin_id"]["index_id"], nuevo)})
    return "cosido: %s -> %s" % (INJERTO_TRAS, INJERTO_LLAMA)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"variables": [], "prevuelo": {}, "escritas": [], "vaciados": {}}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto, cont in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
            continue
        vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                  "variableType": tipo, "defaultValue": defecto,
                                  "containerType": cont})
        out["variables"].append(nombre + " (creada)")

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    for nombre, codigo in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(codigo, nombre) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out

    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    out["injerto"] = injertar()
    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {}
    for nombre in [f[0] for f in FUNCIONES] + [INJERTO_GRAFO]:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
