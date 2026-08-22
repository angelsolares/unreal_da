# -*- coding: utf-8 -*-
import json
import math

# Viste el Jardin de Malkuth. Dos gradientes a la vez:
#
#   A LO LARGO (eje X)   cultivado -> transicion -> arboleda
#   A LO ANCHO (eje Y)   +Y cultivado y abierto  |  -Y bosque con sotobosque
#
# ### POR QUE GRADIENTE
#
# El PDF del recorrido pide "paraiso material: tierra, agua, roca, bosque y marmol
# marron... **evitar jardin artificial**". Pero la zona se llama "Jardin **Geometrico**"
# y es la parada 1, el tutorial: un espacio ordenado ENSENIA mejor, los parterres marcan
# por donde se va sin muros. El gradiente cumple las dos cosas y ademas cuenta algo:
# el jugador sale de lo construido hacia lo salvaje cuando el tutorial termina.
#
#     T1  -3000..4540    formal      filas simetricas, espaciado fijo, escala uniforme
#     T2   4540..12080   transicion  las filas se rompen en matas
#     T3  12080..19620   arboleda    matas irregulares, mezcladas, con huecos
#
# ### EL JARDIN YA ERA ASIMETRICO, Y HAY QUE RESPETARLO
#
# Medidos **93 arboles** (`SM_Arbol_Primer_Plano_*`, `SM_Arbol_Marco_*`) y **los 93
# estan en el lado -Y**: de y=-250 a y=-12.600, radio medio 1.459, a lo largo de todo
# el eje. Ese flanco **ya es un bosque**.
#
# La primera version plantaba rosales en bandas simetricas a ambos lados. Resultado:
# **663 descartes**, todos del lado -Y, porque caian dentro de la arboleda. Pelear
# contra eso habria sido rehacer el diseno que ya estaba.
#
# Asi que la asimetria se vuelve intencionada:
#
#   **+Y** (abierto)  rosales, arbustos en flor, huerto y manto de color.
#   **-Y** (bosque)   sotobosque: helechos, hiedra y vinca, que es lo que crece
#                     bajo copa. Nada de rosales, que ahi no pintan nada.
#
# ### LA TRAZA EMPIEZA POR DEBAJO DE LAS COPAS
#
# Con `bTraceToSurface: true` --o trazando desde z=6000-- la linea se para en **lo
# primero que encuentra**, que bajo arbol es la copa: rosales flotando a **z=3.591**,
# 36 metros en el aire. Y `instancesAdded` decia 400 de 400: la API no miente, pero
# tampoco dice DONDE acabaron. Solo aparecio al mirar una captura cenital y medir Z.
#
# **La cura:** trazar desde **z=600** --por encima del terreno del Jardin, cuyo maximo
# medido es 497, y por debajo de la copa mas baja, medida en 940-- quedarse solo con
# los impactos contra el `Landscape`, y colocar con `bTraceToSurface: false`.
# Asi se puede plantar DEBAJO de los arboles, que es justo lo que pide un sotobosque.
#
# ### SIN `random`: EL SANDBOX NO LO PERMITE
#
# Solo deja `time, math, re, json, datetime, copy`. LCG propio, resultado reproducible.
# Relanzarlo no acumula: **borra sus especies antes**. Las trazas van agrupadas por
# especie y en lotes de 200.

SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Jardin_Sub"
SUELO = "Landscape"
DESDE_Z = 600.0          # terreno max medido 497; copa mas baja medida 940

FS = "/Game/Flowering_Shrubs/Meshes/"
FT = "/Game/FruitTree_Collection/Meshes/"
NF = "/Game/NFlowerPack_1/Foliage/"
MS = "/Game/Megascans/3D_Plants/"

ROSAS = [FS + "SM_Rose_01_Red", FS + "SM_Rose_01_White", FS + "SM_Rose_01_Pink",
         FS + "SM_Rose_01_Yellow", FS + "SM_Rose_01_Purple", FS + "SM_Rose_02",
         FS + "SM_Rose_03"]
ARBUSTOS = [FS + "SM_Hydrangea_Paniculata_01", FS + "SM_Spiraea_Cinerea_01W",
            FS + "SM_Spiraea_Cinerea_01P", FS + "SM_Erica_Multiflora_01P",
            FS + "SM_Erica_Multiflora_01W", FS + "SM_Cistus_Albidus_01",
            FS + "SM_Myrtle_01", FS + "SM_Viburnum_Opulus_01"]
FRUTALES = [FT + "SM_Cherry_Tree_01", FT + "SM_Cherry_Tree_02",
            FT + "SM_Pomegranate_Tree_01", FT + "SM_Orange_Tree_01",
            FT + "SM_Orange_Tree_03", FT + "SM_Peach_Tree_01",
            FT + "SM_Peach_Tree_03", FT + "SM_Lemon_Tree_02", FT + "SM_Lemon_Tree_05"]

MANTO_ROSA = [NF + "Impatiens/Pink/Impatiens_Pink_Cluster_%d_F" % i for i in (1, 3, 5)]
MANTO_ROJO = [NF + "PetchoaSC/Red/PetchoaSC_Red_Cluster_%d_F" % i for i in (1, 3, 5)]
MANTO_BLANCO = [NF + "Vinca/White/Vinca_White_Cluster_%d_F" % i for i in (1, 3, 5)]
MANTO_AMARILLO = [NF + "PetchoaSC/Yellow/PetchoaSC_Yellow_Cluster_%d_F" % i
                  for i in (1, 3, 5)]
MANTO = MANTO_ROSA + MANTO_ROJO + MANTO_BLANCO + MANTO_AMARILLO

# Sotobosque: lo que de verdad crece bajo copa.
HELECHOS = [MS + "BeechFern/SM_BeechFern_%02d" % i for i in range(1, 13)] + \
           [MS + "BostonFern/SM_BostonFern_%02d" % i for i in (1, 2, 3)]
SOMBRA = [NF + "Vinca/White/Vinca_White_Cluster_%d_F" % i for i in (2, 4, 6)] + \
         [NF + "Vinca/Pink/Vinca_Pink_Cluster_%d_F" % i for i in (2, 4, 6)]
SOTOBOSQUE = HELECHOS + SOMBRA

TODAS = ROSAS + ARBUSTOS + FRUTALES + MANTO + SOTOBOSQUE
FLORIDAS = ROSAS + ARBUSTOS

T1 = (-3000.0, 4540.0)
T2 = (4540.0, 12080.0)
T3 = (12080.0, 19620.0)

_s = [20260821]
_desechadas = [0]


def rnd():
    _s[0] = (1103515245 * _s[0] + 12345) % 2147483648
    return _s[0] / 2147483648.0


def entre(a, b):
    return a + (b - a) * rnd()


def elige(lista):
    return lista[int(rnd() * len(lista)) % len(lista)]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def apoyar(puntos):
    """Z contra el LANDSCAPE, trazando POR DEBAJO de las copas."""
    buenos = []
    for i in range(0, len(puntos), 200):
        trozo = puntos[i:i + 200]
        res = call("VibeUE.LandscapeService.BatchLineTrace", {
            "startLocations": [{"x": p[0], "y": p[1], "z": DESDE_Z} for p in trozo],
            "endLocations": [{"x": p[0], "y": p[1], "z": -500.0} for p in trozo]})
        for k, r in enumerate(res):
            d = dict(r)
            if d["bHit"] and str(d["actorName"]) == SUELO:
                buenos.append((trozo[k][0], trozo[k][1], d["hitLocation"]["z"]))
            else:
                _desechadas[0] += 1
    return buenos


def poner(ruta, puntos, smin, smax):
    apoyados = apoyar(puntos)
    total = 0
    for i in range(0, len(apoyados), 200):
        trozo = apoyados[i:i + 200]
        r = call("VibeUE.FoliageService.AddFoliageInstances", {
            "meshOrFoliageTypePath": ruta,
            "locations": [{"x": p[0], "y": p[1], "z": p[2]} for p in trozo],
            "minScale": smin, "maxScale": smax,
            "bAlignToNormal": True, "bRandomYaw": True, "bTraceToSurface": False})
        total += dict(r)["instancesAdded"]
    return total


def sembrar(pares, smin, smax):
    return sum(poner(ruta, pts, smin, smax) for ruta, pts in pares.items())


def mata(cx, cy, radio, cuantas, especies, pares):
    for _ in range(cuantas):
        a = rnd() * 2.0 * math.pi
        r = radio * math.sqrt(rnd())
        pares.setdefault(elige(especies), []).append(
            (cx + r * math.cos(a), cy + r * math.sin(a)))


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE corriendo; parar antes"}
    volver = sc("get_current_level", {})
    if volver != SUB:
        sc("load_level", {"level_path": SUB})
    if "Jardin_Sub" not in str(sc("get_current_level", {})):
        return {"error": "no se abrio el submapa del Jardin"}

    out = {"borradas": 0}
    for ruta in TODAS:
        try:
            d = dict(call("VibeUE.FoliageService.RemoveAllFoliageOfType",
                          {"meshOrFoliageTypePath": ruta}))
            out["borradas"] += d["instancesRemoved"]
        except Exception:
            pass

    # ================= LADO +Y: CULTIVADO =================
    x0, x1 = T1
    ancho = (x1 - x0) / 3.0
    pares = {}
    for b in range(3):
        x = x0 + b * ancho
        while x < x0 + (b + 1) * ancho:
            pares.setdefault(ROSAS[b], []).append((x, 1300.0))
            x += 300.0
    for i in range(4):
        x = x0 + 450.0 + i * 400.0
        while x < x1:
            pares.setdefault(ARBUSTOS[i], []).append((x, 2600.0))
            pares.setdefault(ARBUSTOS[4 + i], []).append((x + 200.0, 3900.0))
            x += 1600.0
    for i, fila_y in enumerate((5200.0, 7200.0)):
        x = x0 + 900.0
        while x < x1:
            pares.setdefault(FRUTALES[i], []).append((x, fila_y))
            x += 1600.0
    out["T1_cultivado"] = sembrar(pares, 0.95, 1.05)

    pares = {}
    for lim, paleta in ((x0 + ancho, MANTO_ROSA), (x0 + 2 * ancho, MANTO_ROJO),
                        (x1, MANTO_BLANCO)):
        pass
    for j, paleta in enumerate((MANTO_ROSA, MANTO_ROJO, MANTO_BLANCO)):
        for _ in range(170):
            pares.setdefault(elige(paleta), []).append(
                (entre(x0 + j * ancho, x0 + (j + 1) * ancho), entre(830.0, 3000.0)))
    out["T1_manto"] = sembrar(pares, 0.9, 1.15)

    x0, x1 = T2
    pares = {}
    for _ in range(22):
        mata(entre(x0, x1), entre(1000.0, 3600.0),
             entre(500.0, 1200.0), 4 + int(rnd() * 6), FLORIDAS, pares)
    for _ in range(10):
        pares.setdefault(elige(FRUTALES), []).append(
            (entre(x0, x1), entre(4300.0, 8200.0)))
    out["T2_cultivado"] = sembrar(pares, 0.85, 1.3)
    pares = {}
    for _ in range(360):
        pares.setdefault(elige(MANTO_ROSA + MANTO_AMARILLO), []).append(
            (entre(x0, x1), entre(830.0, 3400.0)))
    out["T2_manto"] = sembrar(pares, 0.85, 1.25)

    x0, x1 = T3
    pares = {}
    for _ in range(14):
        mata(entre(x0, x1), entre(950.0, 4400.0),
             entre(900.0, 2600.0), 6 + int(rnd() * 9), FLORIDAS, pares)
    for _ in range(14):
        pares.setdefault(elige(FRUTALES), []).append(
            (entre(x0, x1), entre(3800.0, 10500.0)))
    out["T3_arboleda"] = sembrar(pares, 0.7, 1.6)
    pares = {}
    for _ in range(400):
        pares.setdefault(elige(MANTO), []).append(
            (entre(x0, x1), entre(830.0, 4200.0)))
    out["T3_manto"] = sembrar(pares, 0.75, 1.5)

    # ================= LADO -Y: SOTOBOSQUE BAJO LOS 93 ARBOLES =================
    # Helechos y vinca por todo el flanco, mas denso cerca del camino y raleando
    # hacia dentro del bosque. Sin rosales: ahi no pintan nada.
    pares = {}
    for _ in range(700):
        y = -(830.0 + 5200.0 * (rnd() ** 1.7))     # sesgado hacia el camino
        pares.setdefault(elige(SOTOBOSQUE), []).append((entre(-3000.0, 19620.0), y))
    out["sotobosque"] = sembrar(pares, 0.8, 1.5)
    # Matas de helecho al pie de los arboles, mas hacia el fondo.
    pares = {}
    for _ in range(26):
        mata(entre(-3000.0, 19620.0), -entre(3000.0, 9500.0),
             entre(700.0, 1800.0), 5 + int(rnd() * 8), HELECHOS, pares)
    out["sotobosque"] += sembrar(pares, 0.9, 1.6)

    out["desechadas"] = _desechadas[0]
    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": SUB})

    tipos = call("VibeUE.FoliageService.ListFoliageTypes", {})
    vivos = [t["instanceCount"] for t in tipos if t["instanceCount"] > 0]
    out["total_instancias"] = sum(vivos)
    out["especies_con_instancias"] = len(vivos)

    r = dict(call("VibeUE.FoliageService.GetFoliageInRadius", {
        "meshOrFoliageTypePath": HELECHOS[0], "worldCenterX": 8310.0,
        "worldCenterY": -3000.0, "radius": 30000.0, "maxResults": 100}))
    zs = [i["location"]["z"] for i in r["instances"]]
    ys = [i["location"]["y"] for i in r["instances"]]
    out["helecho_z"] = [round(min(zs)), round(max(zs))] if zs else None
    out["helecho_y"] = [round(min(ys)), round(max(ys))] if ys else None

    # VOLVER SIEMPRE al nivel de partida: dejar abierto el `_Sub` hace que un Play
    # arranque el submapa suelto --sin maestro, sin luz y sin PlayerStart-- y la
    # pantalla sale NEGRA. Paso el 21/08/2026.
    if volver != str(sc("get_current_level", {})):
        sc("load_level", {"level_path": volver})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
