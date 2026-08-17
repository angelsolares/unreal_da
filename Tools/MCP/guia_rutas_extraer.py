import json

# Saca la polilinea de cada corredor a partir de sus losas `Conn_*`, y la deja
# lista para montar la guia encima.
#
# LA RUTA YA ESTA EN EL NIVEL. Los `Conn_*` de la carpeta `Conexiones` son las
# piezas de suelo de cada pasillo. Sus centros trazan el camino real —curvas
# incluidas— asi que no hace falta ni navmesh ni splines a mano.
#
# DOS COSAS QUE NO SON OBVIAS Y COSTARON UNA VUELTA CADA UNA:
#
# 1. **El indice va al FINAL del nombre, no en una posicion fija.** Los nueve
#    corredores cortos son `Conn_<Corredor>_<n>`, pero los dos largos son
#    `Conn_JC_Path_<n>` y `Conn_CS_Path_<n>`. Y hay un `Conn_Claro_Floor` y un
#    `Conn_CS_Ground` sueltos, sin numero, que no son corredores.
#
# 2. **Un corredor son VARIAS HILERAS de losas compartiendo numeracion.** El JC
#    tiene 190 piezas pero solo 71 posiciones: dos hileras a z=-40 que forman la
#    calzada, mas otra a z=-38 con distinto paso. Ordenar los 190 por indice daba
#    una polilinea de 1.301.385 de largo para un trayecto de 81.500 en linea
#    recta, porque el indice saltaba de una hilera a otra. La solucion es
#    **agrupar por altura primero** y promediar por indice dentro de cada grupo:
#    eso da el eje de la calzada. De los grupos resultantes se elige el que mas
#    puntos tenga sin saltos rotos.

SALTO_SOSPECHOSO = 3.0   # veces la mediana
SEPARACION = 900.0       # submuestreo: un punto cada tantas unidades


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def polilinea(piezas):
    """Promedia las losas que comparten indice: el eje de la calzada."""
    por_indice = {}
    for idx, p in piezas:
        por_indice.setdefault(idx, []).append(p)
    salida = []
    for idx in sorted(por_indice):
        grupo = por_indice[idx]
        salida.append([round(sum(p[k] for p in grupo) / len(grupo), 1) for k in range(3)])
    return salida


def calidad(puntos):
    if len(puntos) < 2:
        return {"largo": 0, "rotos": 99}
    saltos = [dist(puntos[i], puntos[i + 1]) for i in range(len(puntos) - 1)]
    mediana = sorted(saltos)[len(saltos) // 2]
    return {"largo": round(sum(saltos)),
            "paso": round(mediana),
            "rotos": sum(1 for s in saltos if s > mediana * SALTO_SOSPECHOSO)}


def submuestrear(puntos):
    """Deja un punto cada `SEPARACION`, conservando siempre los dos extremos."""
    if len(puntos) < 3:
        return puntos
    salida = [puntos[0]]
    for p in puntos[1:-1]:
        if dist(salida[-1], p) >= SEPARACION:
            salida.append(p)
    salida.append(puntos[-1])
    return salida


def run():
    bruto = {}
    for a in sc("find_actors", {"name": "Conn_", "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        n = at("get_label", {"actor": a})
        trozos = n.split("_")
        if not n.startswith("Conn_") or len(trozos) < 3 or not trozos[-1].isdigit():
            continue
        t = at("get_actor_transform", {"actor": a})["location"]
        p = [round(t["x"], 1), round(t["y"], 1), round(t["z"], 1)]
        # La altura redondeada separa las hileras: cada superficie va a su cota.
        bruto.setdefault(trozos[1], {}).setdefault(round(p[2]), []).append(
            (int(trozos[-1]), p))

    out = {"rutas": {}, "descartados": {}}
    for corredor in bruto:
        candidatos = []
        for cota in bruto[corredor]:
            puntos = polilinea(bruto[corredor][cota])
            c = calidad(puntos)
            candidatos.append({"cota": cota, "puntos": puntos, **c})
        # Se queda el grupo sin saltos rotos con mas puntos; si todos tienen
        # rotos, el que menos.
        candidatos.sort(key=lambda c: (c["rotos"], -len(c["puntos"])))
        elegido = candidatos[0]
        out["descartados"][corredor] = [
            {"cota": c["cota"], "puntos": len(c["puntos"]), "rotos": c["rotos"]}
            for c in candidatos[1:]]
        fino = submuestrear(elegido["puntos"])
        out["rutas"][corredor] = {
            "cota": elegido["cota"],
            "puntos_originales": len(elegido["puntos"]),
            "puntos": fino,
            "largo": elegido["largo"],
            "paso": elegido["paso"],
            "rotos": elegido["rotos"],
        }
    return out
