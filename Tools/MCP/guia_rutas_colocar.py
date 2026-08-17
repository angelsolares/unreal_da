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

PUNTOS = json.loads(r"""{"JC":[[-25010.6,-59484.5,-40],[-24031.7,-58853.6,-40],[-23052.8,-58222.6,-40],[-22073.9,-57591.6,-40],[-21095.1,-56960.6,-40],[-20116.2,-56329.6,-40],[-19137.3,-55698.6,-40],[-18158.5,-55067.6,-40],[-17179.6,-54436.7,-40],[-16200.7,-53805.7,-40],[-15221.8,-53174.7,-40],[-14243,-52543.7,-40],[-13264.1,-51912.7,-40],[-12285.2,-51281.7,-40],[-11306.3,-50650.7,-40],[-10327.5,-50019.8,-40],[-9348.6,-49388.8,-40],[-8369.7,-48757.8,-40],[-7390.8,-48126.8,-40],[-6412,-47495.8,-40],[-5433.1,-46864.8,-40],[-4454.2,-46233.8,-40],[-3475.3,-45602.8,-40],[-2496.5,-44971.8,-40],[-1517.6,-44340.8,-40],[-538.7,-43709.8,-40],[440.1,-43078.8,-40],[1419,-42447.8,-40],[2397.9,-41816.9,-40],[3376.8,-41185.9,-40],[4355.6,-40554.9,-40],[5334.5,-39923.9,-40],[6313.4,-39292.9,-40],[7292.3,-38661.9,-40],[8271.1,-38030.9,-40],[9250,-37400,-40],[10228.9,-36769.1,-40],[11207.7,-36138.1,-40],[12186.6,-35507.1,-40],[13165.5,-34876.1,-40],[14144.4,-34245.1,-40],[15123.2,-33614.1,-40],[16102.1,-32983.1,-40],[17081,-32352.2,-40],[18059.9,-31721.2,-40],[19038.7,-31090.2,-40],[20017.6,-30459.2,-40],[20996.5,-29828.2,-40],[21975.3,-29197.2,-40],[22954.2,-28566.2,-40],[23933.1,-27935.2,-40],[24912,-27304.2,-40],[25890.8,-26673.2,-40],[26869.7,-26042.2,-40],[27848.6,-25411.2,-40],[28827.5,-24780.2,-40],[29806.3,-24149.3,-40],[30785.2,-23518.3,-40],[31764.1,-22887.3,-40],[32743,-22256.3,-40],[33721.8,-21625.3,-40],[34700.7,-20994.3,-40],[35679.6,-20363.3,-40],[36658.4,-19732.4,-40],[37637.3,-19101.4,-40],[38616.2,-18470.4,-40],[39595.1,-17839.4,-40],[40573.9,-17208.4,-40],[41552.8,-16577.5,-40],[42531.7,-15946.5,-40],[43510.6,-15315.5,-40]],"CS":[[43984.9,-6089.5,-40],[43954.6,-4668.4,-40],[43924.4,-3247.4,-40],[43894.1,-1826.3,-40],[43863.8,-405.2,-40],[43833.6,1015.8,-40],[43803.3,2436.8,-40],[43773.1,3857.9,-40],[43742.8,5279,-40],[43712.5,6700,-40],[43682.2,8121,-40],[43651.9,9542.1,-40],[43621.7,10963.1,-40],[43591.4,12384.2,-40],[43561.2,13805.2,-40],[43530.9,15226.3,-40],[43500.6,16647.4,-40],[43470.4,18068.4,-40],[43440.1,19489.5,-40],[43409.9,20910.5,-40],[43379.6,22331.6,-40],[43349.4,23752.6,-40],[43319.1,25173.7,-40],[43288.8,26594.8,-40],[43258.6,28015.8,-40],[43228.3,29436.8,-40],[43198.1,30857.9,-40],[43167.8,32278.9,-40],[43137.5,33700,-40],[43107.2,35121.1,-40],[43076.9,36542.1,-40],[43046.7,37963.2,-40],[43016.4,39384.2,-40],[42986.2,40805.2,-40],[42955.9,42226.3,-40],[42925.6,43647.4,-40],[42895.4,45068.4,-40],[42865.1,46489.5,-40]],"JardinMirador":[[-14700,-50000,-38],[-14818.2,-47909.1,-38],[-14936.4,-45818.2,-38],[-15054.5,-43727.3,-38],[-15172.7,-41636.4,-38],[-15290.9,-39545.5,-38],[-15409.1,-37454.5,-38],[-15527.3,-35363.6,-38],[-15645.5,-33272.7,-38],[-15763.6,-31181.8,-38],[-15881.8,-29090.9,-38],[-16000,-27000,-38]],"ClaroGazebo":[[41000,16500,-38],[43000,16272.7,-38],[45000,16045.5,-38],[47000,15818.2,-38],[49000,15590.9,-38],[51000,15363.6,-38],[53000,15136.4,-38],[55000,14909.1,-38],[57000,14681.8,-38],[59000,14454.5,-38],[61000,14227.3,-38],[63000,14000,-38]],"SantuarioPuente":[[44000,49500,-38],[42054.5,50454.5,-38],[40109.1,51409.1,-38],[38163.6,52363.6,-38],[36218.2,53318.2,-38],[34272.7,54272.7,-38],[32327.3,55227.3,-38],[30381.8,56181.8,-38],[28436.4,57136.4,-38],[26490.9,58090.9,-38],[24545.5,59045.5,-38],[22600,60000,-38]],"PuenteAnfiteatro":[[9000,60000,-38],[6000,59407.4,-38],[3000,58814.8,-38],[0,58222.2,-38],[-3000,57629.6,-38],[-6000,57037,-38],[-9000,56444.4,-38],[-12000,55851.9,-38],[-15000,55259.3,-38],[-18000,54666.7,-38],[-21000,54074.1,-38],[-24000,53481.5,-38],[-27000,52888.9,-38],[-30000,52296.3,-38],[-33000,51703.7,-38],[-36000,51111.1,-38],[-39000,50518.5,-38],[-42000,49925.9,-38],[-45000,49333.3,-38],[-48000,48740.7,-38],[-51000,48148.1,-38],[-54000,47555.6,-38],[-57000,46963,-38],[-60000,46370.4,-38],[-63000,45777.8,-38],[-66000,45185.2,-38],[-69000,44592.6,-38],[-72000,44000,-38]],"AnfiteatroElevador":[[-74000,40500,-38],[-74000,38381.2,-38],[-74000,36262.5,-38],[-74000,34143.8,-38],[-74000,32025,-38],[-74000,29906.2,-38],[-74000,27787.5,-38],[-74000,25668.8,-38],[-74000,23550,-38],[-74000,21431.2,-38],[-74000,19312.5,-38],[-74000,17193.8,-38],[-74000,15075,-38],[-74000,12956.2,-38],[-74000,10837.5,-38],[-74000,8718.8,-38],[-74000,6600,-38]],"ElevadorGabrielC1":[[-74000,5000,-38],[-72210.5,3973.7,-38],[-70421.1,2947.4,-38],[-68631.6,1921.1,-38],[-66842.1,894.7,-38],[-65052.6,-131.6,-38],[-63263.2,-1157.9,-38],[-61473.7,-2184.2,-38],[-59684.2,-3210.5,-38],[-57894.7,-4236.8,-38],[-56105.3,-5263.2,-38],[-54315.8,-6289.5,-38],[-52526.3,-7315.8,-38],[-50736.8,-8342.1,-38],[-48947.4,-9368.4,-38],[-47157.9,-10394.7,-38],[-45368.4,-11421.1,-38],[-43578.9,-12447.4,-38],[-41789.5,-13473.7,-38],[-40000,-14500,-38]],"GabrielC1C2":[[-42000,-16000,-38],[-44000,-16000,-38],[-46000,-16000,-38],[-48000,-16000,-38],[-50000,-16000,-38],[-52000,-16000,-38],[-54000,-16000,-38],[-56000,-16000,-38],[-58000,-16000,-38],[-60000,-16000,-38],[-62000,-16000,-38],[-64000,-16000,-38]],"GabrielC2C3":[[-68000,-16000,-38],[-70000,-16045.5,-38],[-72000,-16090.9,-38],[-74000,-16136.4,-38],[-76000,-16181.8,-38],[-78000,-16227.3,-38],[-80000,-16272.7,-38],[-82000,-16318.2,-38],[-84000,-16363.6,-38],[-86000,-16409.1,-38],[-88000,-16454.5,-38],[-90000,-16500,-38]],"GabrielC3Yesod":[[-92000,-13500,-38],[-92000,-11400,-38],[-92000,-9300,-38],[-92000,-7200,-38],[-92000,-5100,-38],[-92000,-3000,-38],[-92000,-900,-38],[-92000,1200,-38],[-92000,3300,-38],[-92000,5400,-38],[-92000,7500,-38],[-92000,9600,-38],[-92000,11700,-38],[-92000,13800,-38]]}""")


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
