import json

# Ruinas del Gazebo: colision en los modelos de Tripo y las dos interacciones de
# la zona —leer la tableta y recoger el Fragmento—.
#
# LA COLISION: los StaticMeshActor de la zona (plataforma, muros, escaleras,
# columnas, escombro, pedestal) YA la tienen, `QueryAndPhysics` con perfil
# `BlockAll`. Los que no colisionan son los tres de Tripo: un
# `SkeletalMeshComponent` sin PhysicsAsset y sin `bEnablePerPolyCollision` **no
# tiene geometria de colision ninguna**, por mucho que el perfil diga
# `PhysicsActor`. Es lo que ya se anoto al colocar el Fragmento: "las trazas no
# sirven aqui porque un SkeletalMesh no colisiona".
#
# LA ROTONDA SE QUEDA FUERA A PROPOSITO: tiene **1.014.955 vertices**, y
# `bEnablePerPolyCollision` cocina una malla de colision desde el LOD0 entero.
# Son ~2 millones de triangulos de trimesh para un adorno. El arreglo bueno es
# remesharla en Tripo a los 45k que fija la norma del proyecto y volver a
# importar; entonces esto vale para ella tambien. Ver `ROTONDA` mas abajo.
#
# LAS ZONAS SE DIMENSIONAN CON LAS MEDIDAS REALES, no a ojo. La caja `Zona` mide
# (60,60,90) en el blueprint y quien la ajusta es **la escala del actor**, que es
# como estan hechas las cinco que ya funcionan:
#     escala = medio_ancho_que_quiero / extension_de_la_caja
# y como la caja va a z relativo +90, el centro cae en base + 90*escalaZ, o sea
# que con escalaZ = alto/180 la caja va justo del suelo del objeto a su remate.
#
# LA CAMARA se aleja **1,4 veces el alto** del objeto, que es la proporcion de
# las que ya estan aprobadas (la llave: 70 de alto, camara a 100).

SUB = "L_DA_Malkuth_Gazebo_Sub"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gazebo_Sub"
CLASE = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable_C"

CAJA = 60.0      # medias extensiones X/Y de `Zona` en el blueprint
CAJA_Z = 90.0
LEJOS = 1.4      # cuanto se aleja la camara, en alturas del objeto

# Los tres de Tripo. La rotonda a False hasta que se remeshee.
COLISION = [
    {"actor": "Gazebo_Tableta", "poner": True},
    {"actor": "Gazebo_Fragmento", "poner": True},
    {"actor": "Gazebo_Rotonda", "poner": False},   # 1.014.955 vertices
]

# Cada interactuable: sobre que actor va, que verbo sale en el cartel, cuanto
# margen se le da a la caja por encima del objeto, y que dice al leerlo.
#
# EL TEXTO DE LA TABLETA ES LITERAL DE LA BIBLIA NARRATIVA, pasado por Angel. Se
# reparte en tres lineas porque el panel del HUD dibuja una barra de fondo por
# linea; los cortes van donde la cita respira, no por longitud.
#
# El PDF no se pudo leer desde aqui: esta hecho con XeLaTeX y sus paginas llevan
# 11.825 cadenas hexadecimales y cero literales de texto —son identificadores de
# glifo de fuentes subconjunto, sin tabla `ToUnicode`—. Se decodifica invirtiendo
# la `cmap` de las fuentes empotradas, que es trabajo aparte y hara falta para el
# laberinto de Gabriel.
#
# **Los acentos van como `ó`, no como caracter.** El resto de dialogos del
# proyecto estan sin acentuar, pero esto es una cita literal y se respeta. Al
# escribirlos directos llegaban DESCOMPUESTOS al .umap —una "o" seguida del
# acento combinante U+0301 en vez de la "o" acentuada de un solo codigo, U+00F3—
# porque algo del camino los normaliza a NFD. Se lee igual en un editor, pero al
# canvas de Unreal no tiene por que darle igual, y ademas hace que buscar el
# texto en el binario para verificarlo de un falso negativo. Con el escape
# explicito no hay ambiguedad posible.
OA = chr(243)   # "o" acentuada precompuesta, U+00F3

INTERACTUABLES = [
    {
        "nombre": "Interact_Tableta",
        "sobre": "Gazebo_Tableta",
        "verbo": "Leer",
        "margen": 10.0,
        "dialogo": [
            "\"Antes de ti, hubo otros. Antes de otros, hubo uno.",
            "El uno no subi" + OA + ". El uno baj" + OA + ".",
            "Y al bajar, se convirti" + OA + " en ti.\"",
        ],
    },
    {
        "nombre": "Interact_Fragmento",
        "sobre": "Gazebo_Fragmento",
        "verbo": "Recoger",
        # Mas aire que en la tableta: el Fragmento es pequenio y va sobre un
        # pedestal que no deja acercarse, asi que la caja tiene que salir a
        # buscar al jugador.
        "margen": 28.0,
        "dialogo": ["", "", ""],
    },
]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def en_la_zona(nombre):
    """El actor con esa etiqueta dentro del sublevel del Gazebo.

    Se filtra `UEDPIE`: `find_actors` devuelve tambien el mundo de PIE, y esos
    actores siguen saliendo un rato despues de parar la sesion, ya invalidos.
    """
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if SUB not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def componente(actor, nombre):
    """Un componente por su nombre.

    OJO: en una INSTANCIA de blueprint el refPath lleva el nombre pelado
    (`...Zona`), pero en el CDO lleva `Zona_GEN_VARIABLE`. Filtrar por el nombre
    exacto falla en el CDO y al reves; aqui siempre son instancias.
    """
    for c in at("get_components", {"actor": actor}):
        if c["refPath"].split(".")[-1] == nombre:
            return c
    return None


def traza(x, y, z, dx, dy, largo):
    """`trace_world` devuelve la DISTANCIA al impacto, o None si no toca nada."""
    return sc("trace_world", {"start": {"x": x, "y": y, "z": z},
                              "end": {"x": x + dx * largo, "y": y + dy * largo,
                                      "z": z}})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    out = {}

    # --- entrar a editar el Level Instance ---
    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if "UEDPIE" in a["refPath"]:
                continue
            if "Gazebo" in at("get_label", {"actor": a}):
                li = a
                break
        if li is None:
            return {"error": "no encuentro el Level Instance del Gazebo"}
        out["li"] = at("get_label", {"actor": li})
        sc("edit_level_instance", {"level_instance": li})

    # --- 1. colision en los modelos de Tripo ---
    out["colision"] = []
    for c in COLISION:
        a = en_la_zona(c["actor"])
        if a is None:
            out["colision"].append({c["actor"]: "no esta"})
            continue
        if not c["poner"]:
            out["colision"].append({c["actor"]: "saltado a proposito (demasiados vertices)"})
            continue
        comp = None
        for x in at("get_components", {"actor": a,
                                       "component_type": {"refPath": "/Script/Engine.MeshComponent"}}) or []:
            comp = x
        if comp is None:
            out["colision"].append({c["actor"]: "sin componente de malla"})
            continue
        # Un campo por llamada, que el setter de structs se deja los demas.
        ot("set_properties", {"instance": comp, "values": json.dumps({"bEnablePerPolyCollision": True})})
        ot("set_properties", {"instance": comp, "values": json.dumps(
            {"bodyInstance": {"collisionProfileName": "BlockAll"}})})
        ot("set_properties", {"instance": comp, "values": json.dumps(
            {"bodyInstance": {"collisionEnabled": "QueryOnly"}})})
        leido = json.loads(ot("get_properties", {"instance": comp,
                                                 "properties": ["bEnablePerPolyCollision"]}))
        cuerpo = json.loads(ot("get_properties", {"instance": comp,
                                                  "properties": ["bodyInstance"]}))["bodyInstance"]
        out["colision"].append({c["actor"]: {
            "perpoly": leido["bEnablePerPolyCollision"],
            "col": cuerpo.get("collisionEnabled"),
            "perfil": cuerpo.get("collisionProfileName")}})

    # --- 2. los interactuables ---
    out["interactuables"] = []
    for it in INTERACTUABLES:
        obj = en_la_zona(it["sobre"])
        if obj is None:
            out["interactuables"].append({it["nombre"]: "no esta " + it["sobre"]})
            continue
        b = at("get_actor_bounds", {"actor": obj})
        base = b["min"]["z"]
        alto = b["max"]["z"] - base
        medio = {k: (b["max"][k] - b["min"][k]) / 2.0 + it["margen"] for k in ("x", "y")}
        centro = {k: (b["max"][k] + b["min"][k]) / 2.0 for k in ("x", "y")}
        escala = {"x": medio["x"] / CAJA,
                  "y": medio["y"] / CAJA,
                  "z": (alto / 2.0 + it["margen"]) / CAJA_Z}

        a = en_la_zona(it["nombre"])
        if a is None:
            a = sc("add_to_scene_from_class", {
                "actor_type": {"refPath": CLASE}, "name": it["nombre"],
                "xform": {"location": {"x": centro["x"], "y": centro["y"], "z": base},
                          "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                          "scale": escala},
                "parent": None, "snap_to_ground": False})
            at("set_label", {"actor": a, "label": it["nombre"]})
            creado = "creado"
        else:
            creado = "ya estaba"
        # `set_actor_transform` RESETEA escala y rotacion si no se le pasan las
        # tres: siempre el transform entero.
        at("set_actor_transform", {"actor": a, "worldspace": True, "xform": {
            "location": {"x": centro["x"], "y": centro["y"], "z": base},
            "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
            "scale": escala}})

        # La camara: se aleja 1,4 alturas, en unidades de mundo, y su X relativa
        # va dividida por la escala del actor porque la hereda.
        cam = componente(a, "Camara")
        if cam is not None:
            ot("set_properties", {"instance": cam, "values": json.dumps(
                {"relativeLocation": {"x": -(alto * LEJOS) / escala["x"]}})})

        ot("set_properties", {"instance": a, "values": json.dumps({"Verbo": it["verbo"]})})
        for i, linea in enumerate(it["dialogo"]):
            ot("set_properties", {"instance": a,
                                  "values": json.dumps({"Dialogo%d" % (i + 1): linea})})

        t = at("get_actor_transform", {"actor": a})
        leido = json.loads(ot("get_properties", {"instance": a,
                                                 "properties": ["Verbo", "Dialogo1"]}))
        out["interactuables"].append({it["nombre"]: {
            "estado": creado,
            "pos": [round(t["location"][k], 1) for k in ("x", "y", "z")],
            "esc": [round(t["scale"][k], 3) for k in ("x", "y", "z")],
            "caja_mundo": [round(medio["x"], 1), round(medio["y"], 1),
                           round(escala["z"] * CAJA_Z, 1)],
            "cam_x": round(-(alto * LEJOS) / escala["x"], 1),
            "verbo": leido["Verbo"], "dialogo1": leido["Dialogo1"]}})

    # --- 3. guardar y comprobar contra el disco ---
    if directo:
        ast("save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = ast("is_dirty", {"asset_path": ASSET})

    # --- 4. medir: ¿para de verdad la traza en la tableta? ---
    # De sur a norte a la altura del pecho del jugador, contra la cara grabada.
    out["traza_tableta"] = traza(64000.0, 16700.0, 302.0, 0.0, 1.0, 400.0)
    out["traza_fragmento"] = traza(63880.0, 16650.0, 337.0, 0.0, 1.0, 250.0)
    return out
