# -*- coding: utf-8 -*-
import json
import math

# Coloca las dos mitades del beat de ORDEN. Lanzar DESPUES de
# `sariel_aparicion.py`.
#
#   Mirador  ->  `Aparicion_Sariel_Parte`   (Aparecer = false)
#   El Claro ->  `Aparicion_Sariel_Puerta`  (Aparecer = true) + su Sariel
#
# ### EL SARIEL DE LA PUERTA SE COPIA LEYENDO, NO A MANO
#
# No hay herramienta de duplicar actores entre niveles, asi que el de El Claro se
# construye leyendo del original: malla, modo de animacion, `AnimationData` y
# escala salen de `NPC_Sariel` y `Sariel_Alas` en el Mirador. Ningun numero de
# esos esta escrito aqui. Al final se comparan los **bounds** de la copia con los
# del original: si cuadran, la copia es la copia.
#
# **Las alas son otro actor, no un hijo.** En el Mirador estan a 37 uu y 17 de
# alto del cuerpo, pero ese desfase esta en coordenadas del mundo y con Sariel a
# yaw 180. Aqui se pasa a coordenadas LOCALES y se vuelve a rotar con el yaw
# nuevo; escribir el desfase tal cual pondria las alas de lado.
#
# ### DONDE SE PONE, Y POR QUE AHI
#
# En el rellano, al oeste del hueco de la puerta y mirando al sur, que es por
# donde subes la escalinata: lo primero que ves al coronar es a Sariel esperando.
# La cota **se mide con una traza**, no se escribe: el rellano no esta a la Z que
# dicen los bounds.
#
# **Aviso de reparto:** colocar personajes es de Angel. Esto es una posicion
# funcional para que el beat se pueda probar entero, no una puesta en escena.
#
# ### EL FLAG ES LO QUE ABRE LA PUERTA
#
# `Aparicion_Sariel_Puerta` marca `CLARO_PUERTA_ABIERTA` al materializarse, que es
# el mismo flag que deja forzar el sello. O sea que ORDEN abre la puerta por la
# via que ya existia, sin tocar `BP_DA_Paso`: Sariel aparece y, al aparecer, el
# cartel del paso pasa a decir "Cruzar".
#
# Y el del Mirador marca `MIRADOR_SARIEL_PARTIO`, que no lo lee nadie todavia
# pero es lo que hara falta el dia que alguien pregunte si Sariel sigue alli.

MIR = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"
CLARO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Claro_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CLASE = "/Game/DarkAngels/Blueprints/Level/BP_DA_Aparicion.BP_DA_Aparicion_C"
ESQUELETAL = "/Script/Engine.SkeletalMeshActor"

MARCA = "ORDEN"
FLAG_PARTIO = "MIRADOR_SARIEL_PARTIO"
FLAG_ABIERTA = "CLARO_PUERTA_ABIERTA"

# Rellano de El Claro, coordenadas del submapa. El eje del hueco es x=8245.
SARIEL_X, SARIEL_Y, SARIEL_YAW = 7980.0, 2900.0, -90.0

CAMPOS = ["SkeletalMeshAsset", "AnimationMode", "AnimationData"]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def apoyar(x, y):
    """Suelo pisable. Desde 600 y no desde arriba: los salientes de los
    acantilados devuelven un techo creyendo que es suelo."""
    d = sc("trace_world", {"start": {"x": x, "y": y, "z": 600.0},
                           "end": {"x": x, "y": y, "z": -800.0}})
    if d is None:
        raise RuntimeError("sin suelo bajo (%d, %d)" % (x, y))
    return round(600.0 - d, 1)


def poner(etiqueta, clase, x, y, z, yaw, escala):
    xf = {"location": {"x": x, "y": y, "z": z},
          "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
          "scale": escala}
    a = busca(etiqueta)
    nuevo = a is None
    if nuevo:
        a = sc("add_to_scene_from_class", {"actor_type": {"refPath": clase},
                                           "name": etiqueta, "xform": xf,
                                           "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": a, "label": etiqueta})
    # `set_actor_transform` RESETEA escala y rotacion si no se las pasas.
    at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
    return a, ("creado" if nuevo else "ya estaba")


def bounds(a):
    b = at("get_actor_bounds", {"actor": a, "only_colliding": False})
    if not b["isValid"]:
        return None
    return [round(b["max"][k] - b["min"][k]) for k in ("x", "y", "z")]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {}

    # --- 1. leer el original y montar la partida del Mirador ---
    sc("load_level", {"level_path": MIR})
    if sc("get_current_level", {}) != MIR:
        return {"error": "no se abrio el Mirador"}

    plantilla = {}
    for nombre in ("NPC_Sariel", "Sariel_Alas"):
        a = busca(nombre)
        if a is None:
            sc("load_level", {"level_path": MAESTRO})
            return {"error": "no aparece " + nombre}
        t = at("get_actor_transform", {"actor": a})
        comp = at("get_components", {"actor": a})[0]
        plantilla[nombre] = {
            "actor": a, "t": t, "bounds": bounds(a),
            "comp": json.loads(ot("get_properties",
                                  {"instance": comp, "properties": CAMPOS}))}

    # Desfase de las alas EN LOCAL: se deshace el yaw del cuerpo.
    cuerpo = plantilla["NPC_Sariel"]["t"]
    alas = plantilla["Sariel_Alas"]["t"]
    dx = alas["location"]["x"] - cuerpo["location"]["x"]
    dy = alas["location"]["y"] - cuerpo["location"]["y"]
    dz = alas["location"]["z"] - cuerpo["location"]["z"]
    r = math.radians(-cuerpo["rotation"]["yaw"])
    lx = dx * math.cos(r) - dy * math.sin(r)
    ly = dx * math.sin(r) + dy * math.cos(r)
    dyaw = alas["rotation"]["yaw"] - cuerpo["rotation"]["yaw"]
    out["desfase_alas_local"] = [round(lx, 1), round(ly, 1), round(dz, 1),
                                 round(dyaw, 1)]

    interact = busca("Interact_Sariel")
    objetivos = [plantilla["NPC_Sariel"]["actor"], plantilla["Sariel_Alas"]["actor"]]
    if interact is not None:
        objetivos.append(interact)
    out["objetivos_mirador"] = len(objetivos)

    a, estado = poner("Aparicion_Sariel_Parte", CLASE,
                      cuerpo["location"]["x"], cuerpo["location"]["y"],
                      cuerpo["location"]["z"], 0.0,
                      {"x": 1.0, "y": 1.0, "z": 1.0})
    out["Aparicion_Sariel_Parte"] = estado
    ot("set_properties", {"instance": a, "values": json.dumps(
        {"Objetivos": [{"refPath": o["refPath"]} for o in objetivos]})})
    for k, v in (("Requisito", MARCA), ("FlagAlPasar", FLAG_PARTIO),
                 ("Aparecer", False)):
        ot("set_properties", {"instance": a, "values": json.dumps({k: v})})
    out["leido_mirador"] = json.loads(ot("get_properties", {
        "instance": a, "properties": ["Requisito", "FlagAlPasar", "Aparecer"]}))
    out["objetivos_escritos"] = len(json.loads(ot("get_properties", {
        "instance": a, "properties": ["Objetivos"]}))["Objetivos"])
    ast("save_assets", {"asset_paths": [MIR]})

    # --- 2. el Sariel de la puerta, copiado ---
    sc("load_level", {"level_path": CLARO})
    if sc("get_current_level", {}) != CLARO:
        return dict(out, error="no se abrio El Claro")

    suelo = apoyar(SARIEL_X, SARIEL_Y)
    out["suelo_rellano"] = suelo
    # El pivote de Sariel esta en los pies: el original se apoya en el suelo del
    # Mirador sin correccion, asi que aqui igual.
    copias = {}
    for nombre, etiqueta in (("NPC_Sariel", "NPC_Sariel_Puerta"),
                             ("Sariel_Alas", "Sariel_Alas_Puerta")):
        p = plantilla[nombre]
        if nombre == "NPC_Sariel":
            x, y, z, yaw = SARIEL_X, SARIEL_Y, suelo, SARIEL_YAW
        else:
            rr = math.radians(SARIEL_YAW)
            x = SARIEL_X + lx * math.cos(rr) - ly * math.sin(rr)
            y = SARIEL_Y + lx * math.sin(rr) + ly * math.cos(rr)
            z, yaw = suelo + dz, SARIEL_YAW + dyaw
        a, estado = poner(etiqueta, ESQUELETAL, x, y, z, yaw, p["t"]["scale"])
        copias[etiqueta] = a
        out[etiqueta] = estado
        comp = at("get_components", {"actor": a})[0]
        # Un campo por llamada: el setter aplica el primero y aqui se mezclan
        # referencia de asset y enum.
        for campo in CAMPOS:
            valor = p["comp"][campo]
            if valor is None or str(valor) == "None":
                continue
            ot("set_properties", {"instance": comp,
                                  "values": json.dumps({campo: valor})})
        out["bounds_" + etiqueta] = {"original": p["bounds"], "copia": bounds(a)}

    a, estado = poner("Aparicion_Sariel_Puerta", CLASE,
                      SARIEL_X, SARIEL_Y, suelo, 0.0, {"x": 1.0, "y": 1.0, "z": 1.0})
    out["Aparicion_Sariel_Puerta"] = estado
    ot("set_properties", {"instance": a, "values": json.dumps(
        {"Objetivos": [{"refPath": copias[k]["refPath"]} for k in
                       ("NPC_Sariel_Puerta", "Sariel_Alas_Puerta")]})})
    for k, v in (("Requisito", MARCA), ("FlagAlPasar", FLAG_ABIERTA),
                 ("Aparecer", True)):
        ot("set_properties", {"instance": a, "values": json.dumps({k: v})})
    out["leido_claro"] = json.loads(ot("get_properties", {
        "instance": a, "properties": ["Requisito", "FlagAlPasar", "Aparecer"]}))

    for et in ("NPC_Sariel_Puerta", "Sariel_Alas_Puerta"):
        a2 = busca(et)
        t = at("get_actor_transform", {"actor": a2})
        out["sitio_" + et] = [round(t["location"][k]) for k in ("x", "y", "z")] + \
                             [round(t["rotation"]["yaw"], 1)]

    ast("save_assets", {"asset_paths": [CLARO]})
    out["sucio"] = {"claro": ast("is_dirty", {"asset_path": CLARO}),
                    "mirador": ast("is_dirty", {"asset_path": MIR})}
    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
