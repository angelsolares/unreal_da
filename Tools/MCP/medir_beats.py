# -*- coding: utf-8 -*-
import json
import math
import re

# Cuanto se tarda en recorrer cada camino de Malkuth, en metros y en SEGUNDOS.
# La pregunta que responde: "de aqui a aqui, cuanto rato voy andando sin que pase
# nada", que es con lo que se colocan los beats.
#
# ### EL EDITOR MIDE DISTANCIA, PERO NO TIEMPO
#
# En un viewport ortografico (Top/Front/Right), **Ctrl + arrastrar con el boton
# central** dibuja una regla con la distancia. Eso y la barra de escala de la
# esquina es todo lo que trae Unreal. Para tiempo no hay nada nativo: hace falta
# la velocidad del jugador, y en este proyecto **no esta donde uno la busca**.
#
# ### LA VELOCIDAD NO ESTA EN `MaxWalkSpeed`
#
# Malakh hereda de `BP_CombatCharacter`, y DCS **no usa el `MaxWalkSpeed` del
# CharacterMovement**: lo pisa en runtime desde `BP_MovementSpeedComponent`, que
# guarda tres velocidades y un estado. Leidas del CDO:
#
#     WalkSpeed    200 uu/s     (2,0 m/s)
#     JogSpeed     400 uu/s     (4,0 m/s)   <- DefaultMovementState = Jog
#     SprintSpeed  550 uu/s     (5,5 m/s)
#
# O sea que **lo normal es el trote**, no el paseo. La regla de bolsillo que sale
# de ahi: **1.000 uu = 2,5 s**, o **4 metros por segundo**.
#
# Es una cota OPTIMISTA: no cuenta la aceleracion (`SpeedChangeInterpSpeed` 6),
# ni las curvas, ni que nadie camina en linea recta. El tiempo real de un pasillo
# largo sale un 10-20% por encima.
#
# ### LOS CAMINOS SE MIDEN POR SU POLILINEA, NO EN LINEA RECTA
#
# Cada carretera son piezas `SM_MGK_Path_Straight_600` numeradas (`Conn_JC_Path_0`,
# `_1`, ...). El numero **es el orden del trazado**, porque se generaron seguidas,
# asi que ordenando por el sufijo y sumando distancias 3D sale el largo de verdad,
# curvas y cuestas incluidas.
#
# Un `salto_raro` (dos piezas consecutivas a mas de 3.000 uu) significa que **falta
# camino en medio**: o se borro una pieza, o la numeracion tiene un hueco.
#
# ### SOLO VE EL MAESTRO
#
# Las sendas internas de cada zona viven dentro de su Level Instance y desde el
# maestro **no se ven**. Esto mide la red que une zonas, que es la que produce los
# minutos muertos. Para medir dentro de una zona hay que abrir su `_Sub`.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"

WALK, JOG, SPRINT = 200.0, 400.0, 550.0
SALTO_RARO = 3000.0

# Cuanto aguanta un tramo sin nada antes de cansar. No es una ley, es el listón
# que usamos aqui: por encima de 45 s de camino vacio, toca meter un beat.
LIMITE_SEG = 45.0


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def es_pieza(etiqueta):
    return any(k in etiqueta for k in ("Path", "Senda", "Enlace", "Camino"))


def run():
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {"nivel": str(sc("get_current_level", {})),
           "velocidades": {"walk": WALK, "jog": JOG, "sprint": SPRINT}}

    tramos = {}
    hitos = {}
    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        try:
            et = at("get_label", {"actor": a})
            loc = at("get_actor_transform", {"actor": a})["location"]
        except Exception:
            continue
        m = re.match(r"^(.*?)_(\d+)$", et)
        if m and es_pieza(et):
            tramos.setdefault(m.group(1), []).append(
                (int(m.group(2)), loc["x"], loc["y"], loc["z"]))
        if any(k in et for k in ("PS_Master", "PlayerStart", "LI_", "Hito_")):
            hitos[et] = [round(loc[k]) for k in ("x", "y", "z")]

    res = {}
    for nombre, pts in tramos.items():
        pts.sort()
        largo = 0.0
        saltos = []
        for i in range(1, len(pts)):
            d = math.dist(pts[i - 1][1:], pts[i][1:])
            largo += d
            if d > SALTO_RARO:
                saltos.append({"entre": [pts[i - 1][0], pts[i][0]], "uu": round(d)})
        seg = largo / JOG
        res[nombre] = {"piezas": len(pts), "uu": round(largo),
                       "m": round(largo / 100.0, 1),
                       "seg_paseo": round(largo / WALK, 1),
                       "seg_trote": round(seg, 1),
                       "seg_carrera": round(largo / SPRINT, 1),
                       "pasa_del_limite": seg > LIMITE_SEG,
                       "beats_que_pediria": max(0, int(seg // LIMITE_SEG)),
                       "desde": [round(v) for v in pts[0][1:]],
                       "hasta": [round(v) for v in pts[-1][1:]],
                       "saltos_raros": saltos}
    out["tramos"] = res
    out["hitos"] = hitos
    out["total_seg_trote"] = round(sum(v["seg_trote"] for v in res.values()), 1)
    return out
