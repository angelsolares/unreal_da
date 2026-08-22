# -*- coding: utf-8 -*-
import json

# Abre ventanas en el seto del pasillo Claro -> Santuario, para que el Santuario
# **se anticipe** desde el camino.
#
# ### POR QUE
#
# El Atlas de Esferas lo pide por escrito: *"Ruta critica legible: **el landmark y la
# salida se anticipan**; los desvios vuelven a conectar."*
#
# Medido: `Conn_CS_HedgeL` y `Conn_CS_HedgeR`, **38 piezas por lado de 253 uu de alto**
# a lo largo de 526 m. La capsula del jugador mide 192 y el ojo va sobre los 160, o sea
# que el seto **tapa la vista entera**: 2 min 11 s de tunel sin ver a donde vas.
#
# ### SE BAJAN, NO SE BORRAN
#
# Quitar piezas dejaria huecos por los que salirse del camino, y el seto tambien
# cumple la funcion de contener. Bajarlos a ~114 uu --por debajo de la linea del ojo--
# **abre la vista sin abrir el paso**, y es reversible con solo devolver la escala.
#
# ### CADENCIA
#
# 38 piezas en 526 m = una cada ~13,8 m. Se bajan **dos consecutivas de cada seis**,
# lo que da **ventanas de ~28 m cada ~83 m**: seis asomos a lo largo del pasillo.
# Ni tan seguidas que el seto pierda sentido, ni tan raras que el jugador no vea nunca
# el Santuario.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
LADOS = ("Conn_CS_HedgeL", "Conn_CS_HedgeR")
CICLO = 6          # de cada seis piezas...
BAJAS = 2          # ...se bajan dos consecutivas
FACTOR = 0.45      # 253 uu * 0.45 = ~114, por debajo del ojo (160)


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def piezas(pref):
    """find_actors filtra por ETIQUETA; el refPath lleva el nombre de objeto."""
    fuera = {}
    for a in sc("find_actors", {"name": pref, "tag": "", "collision_channels": []}):
        rp = a["refPath"]
        if "UEDPIE" in rp or "L_DA_Malkuth_Master" not in rp:
            continue
        try:
            e = at("get_label", {"actor": a})
        except Exception:
            continue
        if e.startswith(pref + "_"):
            try:
                fuera[int(e.rsplit("_", 1)[1])] = a
            except ValueError:
                pass
    return fuera


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE corriendo; parar antes"}
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {"ventanas": [], "bajadas": 0, "ya_bajas": 0}

    for pref in LADOS:
        pz = piezas(pref)
        out[pref + "_encontradas"] = len(pz)
        for i in sorted(pz):
            baja = (i % CICLO) < BAJAS
            t = at("get_actor_transform", {"actor": pz[i]})
            esc = t["scale"]
            if not baja:
                # Restaurar por si una pasada anterior la dejo baja.
                if abs(esc["z"] - 1.0) > 0.01 and esc["z"] < 0.9:
                    at("set_actor_transform", {"actor": pz[i], "worldspace": True,
                        "xform": {"location": t["location"], "rotation": t["rotation"],
                                  "scale": {"x": esc["x"], "y": esc["y"], "z": 1.0}}})
                continue
            if esc["z"] < 0.9:
                out["ya_bajas"] += 1
                continue
            # set_actor_transform RESETEA lo que no le pases: van los tres.
            at("set_actor_transform", {"actor": pz[i], "worldspace": True,
                "xform": {"location": t["location"], "rotation": t["rotation"],
                          "scale": {"x": esc["x"], "y": esc["y"], "z": FACTOR}}})
            out["bajadas"] += 1
            if pref == LADOS[0]:
                out["ventanas"].append(i)

    ast("save_assets", {"asset_paths": [MAESTRO]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})

    # --- releer del actor y medir la altura real, no la escala ---
    comprobado = []
    pz = piezas(LADOS[0])
    for i in sorted(pz)[:14]:
        b = at("get_actor_bounds", {"actor": pz[i]})
        alto = round(b["max"]["z"] - b["min"]["z"])
        comprobado.append({"i": i, "alto": alto, "tapa_la_vista": alto > 160})
    out["alturas"] = comprobado
    return out
