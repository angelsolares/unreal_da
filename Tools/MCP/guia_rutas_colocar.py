import json

# Crea `BP_DA_Ruta` y planta una instancia por corredor en el Master, cada una
# con la polilinea de su camino metida en un array de vectores.
#
# LOS PUNTOS LOS SACA `guia_rutas_extraer.py` DEL PROPIO NIVEL, de las losas
# `Conn_*`. Aqui van pegados como constante para que el montaje sea
# reproducible sin depender del orden en que se lancen los scripts: si el nivel
# cambia, se relanza el extractor y se pega la tabla nueva.
#
# PARA ESCRIBIR EL ARRAY HAY QUE LLAMARLO `puntos`, EN MINUSCULA. El setter
# encuentra las variables sueltas sin mirar mayusculas —`Corredor`, `Orden` y
# `EsPrincipal` entran tal cual— pero con el array no: con `Puntos` responde
# "the following properties could not be set". `ObjectTools.list_properties`
# canta el nombre y la forma exactos que quiere, y ahi salen todos en camelCase
# con la inicial en minuscula. Preguntarle a el antes de probar formatos a
# ciegas; el texto de Unreal "((X=..,Y=..,Z=..))" que si vale para un vector
# suelto **no vale para arrays**, quiere la lista de objetos JSON.
#
# Aun asi se comprueba cuantos elementos llegan y si el ultimo es el bueno,
# porque por MCP los arrays de structs se han dejado el ultimo por el camino
# otras veces.

RUTA_BP = "/Game/DarkAngels/Blueprints/Level"
NOMBRE_BP = "BP_DA_Ruta"
CLASE = RUTA_BP + "/" + NOMBRE_BP + "." + NOMBRE_BP
CARPETA = "Guidance/Rutas"

# corredor -> (es principal, orden de progresion)
META = {
    "JC": (True, 1),
    "CS": (True, 2),
    "SantuarioPuente": (True, 3),
    "PuenteAnfiteatro": (True, 4),
    "AnfiteatroElevador": (True, 5),
    "ElevadorGabrielC1": (True, 6),
    "GabrielC1C2": (True, 7),
    "GabrielC2C3": (True, 8),
    "GabrielC3Yesod": (True, 9),
    "JardinMirador": (False, 0),
    "ClaroGazebo": (False, 0),
}

# A QUE ZONA LLEGA CADA EXTREMO, dicho a mano. La primera version lo resolvia
# buscando el trigger de zona mas cercano a cada punta y se equivocaba en tres:
# `GabrielC2C3` se anclaba al Elevador y `PuenteAnfiteatro` a Yesod, porque su
# punta cae cerca de una zona que no conectan. `None` = ese extremo no entra en
# ninguna zona (los ramales salen a mitad de otro corredor, y el Anfiteatro y la
# Camara II no tienen trigger).
ANCLAS = {
    "JC": ("Jardin Geometrico", "El Claro"),
    "CS": ("El Claro", "Santuario de Malkuth"),
    "JardinMirador": (None, "Mirador de Sariel"),
    "ClaroGazebo": (None, "Ruinas del Gazebo"),
    "SantuarioPuente": ("Santuario de Malkuth", "Puente Ascendente"),
    "PuenteAnfiteatro": ("Puente Ascendente", None),
    "AnfiteatroElevador": (None, "Elevador del Trono"),
    "ElevadorGabrielC1": ("Elevador del Trono", "Gabriel - Camara I"),
    "GabrielC1C2": ("Gabriel - Camara I", None),
    "GabrielC2C3": (None, "Gabriel - Camara III"),
    "GabrielC3Yesod": ("Gabriel - Camara III", "Portal a Yesod"),
}

PASO_ANCLA = 1200.0   # cada cuanto se pone un punto en el tramo de anclaje

# Extraido del nivel el 2026-08-27 (mundo compactado). PuenteAnfiteatro y
# JardinMirador quedan FUERA: sus carreteras estan rotas y sin ruta que colocar.
PUNTOS = json.loads(r"""{"JC": [[13154.9, -28878.1, -38.0], [14744.7, -28096.3, -38.0], [16307.5, -27262.0, -38.0], [17839.9, -26373.0, -38.0], [19374.2, -25487.5, -38.0], [20959.3, -24697.4, -38.0], [22618.3, -24078.6, -38.0], [24332.0, -23631.1, -38.0], [25487.6, -23387.0, -38.0]], "CS": [[26212.0, -16200.0, -38.0], [26718.6, -14514.9, -38.0], [27228.3, -12830.7, -38.0], [27744.0, -11148.3, -38.0], [28268.3, -9468.6, -38.0], [28803.5, -7792.4, -38.0], [29351.6, -6120.3, -38.0], [29913.6, -4452.9, -38.0], [30490.5, -2790.5, -38.0], [31082.0, -1133.3, -38.0], [31687.6, 518.8, -38.0], [32306.0, 2166.2, -38.0], [32935.2, 3809.5, -38.0], [33572.6, 5449.6, -38.0], [34215.3, 7087.7, -38.0], [34859.7, 8725.1, -38.0], [35501.9, 10363.3, -38.0], [36137.6, 12004.1, -38.0], [36762.5, 13649.0, -38.0], [37372.0, 15299.7, -38.0], [37961.6, 16957.6, -38.0], [38526.7, 18624.0, -38.0], [39063.1, 20299.8, -38.0], [39567.1, 21985.7, -38.0], [40035.3, 23681.9, -38.0], [40465.1, 25388.1, -38.0], [40854.7, 27104.1, -38.0], [41203.1, 28828.8, -38.0], [41510.4, 30561.3, -38.0], [41777.7, 32300.5, -38.0], [42006.9, 34045.1, -38.0], [42200.9, 35794.0, -38.0], [42363.3, 37546.1, -38.0], [42498.5, 39300.5, -38.0], [42611.2, 41056.5, -38.0], [42706.8, 42813.5, -38.0], [42790.8, 44571.1, -38.0], [42869.0, 46329.0, -38.0]], "SantuarioPuente": [[44000.0, 49500.0, -38.0], [42297.0, 49923.5, -38.0], [40604.6, 50387.3, -38.0], [38934.7, 50926.0, -38.0], [37299.5, 51562.0, -38.0], [35708.3, 52301.4, -38.0], [34163.0, 53132.7, -38.0], [32656.2, 54031.9, -38.0], [31172.8, 54969.5, -38.0], [29695.3, 55916.3, -38.0], [28208.2, 56848.1, -38.0], [26702.4, 57749.1, -38.0], [25175.8, 58614.5, -38.0], [23633.1, 59450.9, -38.0], [22600.0, 60000.0, -38.0]], "AnfiteatroElevador": [[-18127.0, 49684.0, -38.0], [-18502.4, 47960.2, -38.0], [-18857.0, 46232.1, -38.0], [-19171.1, 44496.1, -38.0], [-19427.4, 42750.7, -38.0], [-19612.6, 40996.4, -38.0], [-19719.1, 39235.6, -38.0], [-19745.7, 37471.8, -38.0], [-19698.1, 35708.3, -38.0], [-19587.8, 33947.7, -38.0], [-19430.1, 32190.6, -38.0], [-19242.3, 30436.4, -38.0], [-19041.7, 28683.7, -38.0], [-18844.2, 26930.6, -38.0], [-18662.6, 25175.8, -38.0], [-18506.0, 23418.5, -38.0], [-18378.8, 21659.0, -38.0], [-18280.3, 19897.5, -38.0], [-18205.5, 18134.9, -38.0], [-18145.5, 16371.8, -38.0], [-18127.0, 15784.0, -38.0]], "ElevadorGabrielC1": [[-18127.0, 15784.0, -38.0], [-16508.1, 15088.6, -38.0], [-14886.7, 14398.9, -38.0], [-13260.7, 13720.2, -38.0], [-11628.3, 13057.1, -38.0], [-9988.4, 12412.6, -38.0], [-8340.7, 11788.5, -38.0], [-6685.4, 11184.7, -38.0], [-5023.6, 10599.2, -38.0], [-3356.7, 10028.1, -38.0], [-1686.7, 9466.2, -38.0], [-16.1, 8906.3, -38.0], [1652.6, 8340.5, -38.0], [3316.2, 7760.2, -38.0], [4971.5, 7156.4, -38.0], [6614.7, 6520.5, -38.0], [8241.9, 5844.9, -38.0], [9849.3, 5123.3, -38.0], [11433.2, 4351.6, -38.0], [12990.5, 3527.6, -38.0], [14519.5, 2652.0, -38.0], [16019.4, 1727.6, -38.0], [17491.4, 759.3, -38.0], [18938.1, -246.4, -38.0], [20363.8, -1281.6, -38.0], [21774.0, -2338.0, -38.0], [23174.9, -3406.7, -38.0], [23641.0, -3764.0, -38.0]], "GabrielC1C2": [[23500.0, -4396.0, -38.0], [21738.2, -4333.1, -38.0], [19976.8, -4257.7, -38.0], [18216.6, -4159.2, -38.0], [16458.4, -4030.9, -38.0], [14702.6, -3871.6, -38.0], [12949.5, -3685.7, -38.0], [11198.3, -3482.8, -38.0], [9447.3, -3277.5, -38.0], [7694.6, -3087.5, -38.0], [5938.6, -2932.2, -38.0], [4178.6, -2830.5, -38.0], [2416.1, -2798.5, -38.0], [654.0, -2847.3, -38.0], [-1103.8, -2980.6, -38.0], [-2853.6, -3194.2, -38.0], [-4593.7, -3476.5, -38.0], [-6324.8, -3810.3, -38.0], [-8049.6, -4174.7, -38.0], [-8624.0, -4299.0, -38.0]], "GabrielC2C3": [[-12230.4, -5277.1, -38.0], [-13968.1, -5369.6, -38.0], [-15704.2, -5486.9, -38.0], [-17437.1, -5645.3, -38.0], [-19165.6, -5846.0, -38.0], [-20890.8, -6073.7, -38.0], [-22616.3, -6298.9, -38.0], [-24346.5, -6483.3, -38.0], [-26083.3, -6588.4, -38.0], [-27823.1, -6584.5, -38.0], [-29558.5, -6460.8, -38.0], [-31283.0, -6229.7, -38.0], [-32995.9, -5923.2, -38.0], [-34133.9, -5698.3, -38.0]], "GabrielC3Yesod": [[-36240.0, -2749.7, -38.0], [-36182.2, -1001.4, -38.0], [-36107.5, 746.3, -38.0], [-36002.9, 2492.5, -38.0], [-35862.4, 4236.1, -38.0], [-35688.7, 5976.8, -38.0], [-35493.6, 7715.2, -38.0], [-35296.1, 9453.3, -38.0], [-35120.7, 11193.8, -38.0], [-34993.7, 12938.4, -38.0], [-34939.3, 14686.7, -38.0], [-34975.5, 16435.4, -38.0], [-35109.4, 18179.4, -38.0], [-35335.9, 19913.8, -38.0], [-35638.1, 21636.7, -38.0], [-35991.1, 23350.0, -38.0], [-36240.0, 24489.3, -38.0]], "ClaroGazebo": [[41000.0, 16500.0, -38.0], [42750.2, 16673.1, -38.0], [44504.3, 16798.0, -38.0], [46262.5, 16833.4, -38.0], [48019.0, 16753.2, -38.0], [49766.0, 16553.4, -38.0], [51498.7, 16252.7, -38.0], [53218.5, 15885.1, -38.0], [54932.3, 15490.2, -38.0], [56648.1, 15103.9, -38.0], [58371.1, 14751.2, -38.0], [60102.4, 14442.2, -38.0], [61839.9, 14170.2, -38.0], [63000.0, 14000.0, -38.0]]}""")


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


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


def vectores(puntos):
    return [{"x": p[0], "y": p[1], "z": p[2]} for p in puntos]


def escribir_array(actor, clave, puntos):
    """Rellena un array de vectores punto a punto.

    EL SETTER DE ARRAYS APLICA DIFERENCIAS, NO ASIGNA. Compara el array nuevo
    con el que hay y, si la lista crece **y ademas** cambia algun elemento que ya
    estaba, se planta:
        "ArrayAdd: elements changed alongside the size change;
         insertion points are ambiguous."
    Y aunque el array este vacio tampoco vale mandar la lista entera de golpe:
    de una tacada de tres solo entro el primer elemento.

    Asi que: **se vacia primero** —encoger no cambia nada, eso si lo traga— y
    luego se manda el prefijo de longitud i+1 en cada llamada, que anade
    exactamente uno al final sin tocar los anteriores. Una llamada por punto,
    248 para las once rutas. Si lo que ya hay coincide con el principio de lo que
    se quiere, se sigue desde ahi y no se repite trabajo.

    La clave va en **minuscula inicial** (`puntos`): con `Puntos` el setter no
    encuentra la propiedad. `ObjectTools.list_properties` canta el nombre exacto.
    """
    minuscula = clave[0].lower() + clave[1:]
    ya = json.loads(ot("get_properties", {"instance": actor,
                                          "properties": [clave]}))[clave]
    ya = ya if isinstance(ya, list) else []

    def igual(a, b):
        return all(abs(a[k] - b[i]) < 0.5 for i, k in enumerate(("x", "y", "z")))

    # ¿Lo que hay es el principio de lo que se quiere?
    sirve = len(ya) <= len(puntos) and all(igual(ya[i], puntos[i]) for i in range(len(ya)))
    if not sirve:
        ot("set_properties", {"instance": actor, "values": json.dumps({minuscula: []})})
        ya = []
    for i in range(len(ya), len(puntos)):
        ot("set_properties", {"instance": actor,
                              "values": json.dumps({minuscula: vectores(puntos[:i + 1])})})
    return len(puntos)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    out = {}

    # --- 1. el blueprint ---
    if not ast("exists", {"path": RUTA_BP + "/" + NOMBRE_BP}):
        bt("create", {"folder_path": RUTA_BP, "asset_name": NOMBRE_BP,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"
    else:
        out["blueprint"] = "ya estaba"
    bp = {"refPath": CLASE}

    variables = str(bt("list_variables", {"blueprint": bp}))
    for nombre, tipo, contenedor in (("Corredor", "name", None),
                                     ("Puntos", "vector", "ARRAY"),
                                     ("EsPrincipal", "bool", None),
                                     ("Orden", "int", None)):
        if nombre not in variables:
            a = {"blueprint": bp, "name": nombre, "type_name": tipo}
            if contenedor:
                a["container_type"] = contenedor
            bt("add_variable", a)
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": nombre, "instance_editable": True})
    bt("compile_blueprint", {"blueprint": bp})
    ast("save_assets", {"asset_paths": [RUTA_BP + "/" + NOMBRE_BP]})
    out["variables"] = bt("list_variables", {"blueprint": bp})

    # --- 2. una instancia por corredor, en el Master ---
    # LOS CORREDORES NO ENTRAN EN LAS ZONAS. Sus losas van de la salida de una a
    # la entrada de la otra, asi que desde el centro de una zona el camino queda
    # lejos: en el Jardin, a 34.642. Con el fuego descartandose a 12.000 de su
    # ruta, alli no salia nada.
    #
    # Se le cose a cada extremo un punto de anclaje en el centro de la zona que
    # tiene mas cerca, si es que no lo pisa ya. El tramo del ancla al corredor si
    # es recto —dentro de una zona no hay losas que seguir— pero es campo abierto
    # y lo que importa es que el fuego arranque donde estas.
    zonas = {}
    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "ZoneTrigger" not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        t = at("get_actor_transform", {"actor": a})["location"]
        n = json.loads(ot("get_properties", {"instance": a, "properties": ["ZoneName"]}))
        zonas[str(n["ZoneName"])] = [t["x"], t["y"], t["z"]]

    def tramo(desde, hasta):
        """Puntos intermedios entre dos posiciones, al paso del corredor.

        **SIN ESTO EL FUEGO SE VA HACIA ATRAS.** Un ancla suelta a 34 km de su
        corredor deja un hueco sin un solo punto, y si el jugador esta dentro de
        ese hueco su punto mas cercano es el ancla, que le queda detras: el fuego
        sale a buscarla y parece que te manda de vuelta al principio. Rellenando
        el tramo, el punto mas cercano cae siempre donde estas y el siguiente
        siempre es hacia delante.
        """
        d = ((hasta[0] - desde[0]) ** 2 + (hasta[1] - desde[1]) ** 2) ** 0.5
        n = int(d // PASO_ANCLA)
        return [[desde[0] + (hasta[0] - desde[0]) * i / (n + 1.0),
                 desde[1] + (hasta[1] - desde[1]) * i / (n + 1.0),
                 desde[2] + (hasta[2] - desde[2]) * i / (n + 1.0)]
                for i in range(n + 1)]

    out["rutas"] = []
    out["anclas"] = []
    for corredor in sorted(PUNTOS):
        puntos = list(PUNTOS[corredor])
        za, zb = ANCLAS.get(corredor, (None, None))
        if za and za in zonas:
            p = [zonas[za][0], zonas[za][1], puntos[0][2]]
            puntos = tramo(p, puntos[0]) + puntos
            out["anclas"].append([corredor, "inicio", za])
        if zb and zb in zonas:
            p = [zonas[zb][0], zonas[zb][1], puntos[-1][2]]
            puntos = puntos + tramo(puntos[-1], p)[1:] + [p]
            out["anclas"].append([corredor, "fin", zb])
        etiqueta = "Ruta_" + corredor
        actor = None
        for a in sc("find_actors", {"name": etiqueta, "tag": "", "collision_channels": []}):
            if "UEDPIE" in a["refPath"]:
                continue
            if at("get_label", {"actor": a}) == etiqueta:
                actor = a
                break
        if actor is None:
            actor = sc("add_to_scene_from_class", {
                "actor_type": {"refPath": CLASE + "_C"}, "name": etiqueta,
                "xform": {"location": {"x": puntos[0][0], "y": puntos[0][1],
                                       "z": puntos[0][2]},
                          "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                          "scale": {"x": 1.0, "y": 1.0, "z": 1.0}},
                "parent": None, "snap_to_ground": False})
            at("set_label", {"actor": actor, "label": etiqueta})
        sc("set_actor_folder", {"actor": actor, "folder_path": CARPETA})

        principal, orden = META.get(corredor, (False, 0))
        ot("set_properties", {"instance": actor, "values": json.dumps({"Corredor": corredor})})
        ot("set_properties", {"instance": actor, "values": json.dumps({"EsPrincipal": principal})})
        ot("set_properties", {"instance": actor, "values": json.dumps({"Orden": orden})})
        escribir_array(actor, "Puntos", puntos)

        leido = json.loads(ot("get_properties", {"instance": actor,
                                                 "properties": ["Puntos", "Corredor",
                                                                "EsPrincipal", "Orden"]}))
        guardados = leido["Puntos"] if isinstance(leido["Puntos"], list) else []
        out["rutas"].append({
            "ruta": etiqueta,
            "esperados": len(puntos),
            "guardados": len(guardados),
            "primero_ok": (bool(guardados)
                           and abs(guardados[0]["x"] - puntos[0][0]) < 1.0),
            "ultimo_ok": (bool(guardados)
                          and abs(guardados[-1]["x"] - puntos[-1][0]) < 1.0),
            "principal": leido["EsPrincipal"], "orden": leido["Orden"],
        })

    ast("save_assets", {"asset_paths": ["/Game/DarkAngels/Maps/L_DA_Malkuth_Master"]})
    out["mapa_sucio"] = ast("is_dirty",
                            {"asset_path": "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"})
    return out
