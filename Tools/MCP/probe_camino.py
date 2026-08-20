# -*- coding: utf-8 -*-
import json

# Busca si existe un CAMINO PISABLE entre dos puntos del mundo. No es un NavMesh
# —el MCP no sabe hornear— pero es lo mas cerca que se puede llegar midiendo, y
# sobre todo **no miente en la direccion peligrosa**: si dice que no hay camino
# es que no lo hay con este paso de rejilla; si dice que si, hay una cadena de
# celdas en las que el jugador cabe de pie y entre las que puede pasar.
#
# POR QUE HACE FALTA. Un rayo suelto no vale para esto, y ya me engano dos veces
# midiendo El Claro:
#   - Traza hacia abajo desde muy arriba: devuelve el primer TECHO, no el suelo.
#     Un pasillo de roca se lee como "suelo a 2600" durante 2000 uu.
#   - Traza hacia abajo desde poco arriba: pasa por DEBAJO de los salientes y el
#     mismo pasillo se lee como llanura abierta.
#   - Rayo horizontal: no distingue un muro de un canto rodado.
#
# LO QUE MIDE CADA CELDA
#   1. Suelo: traza desde `ALTO_SONDA` hacia abajo. Si no hay, celda muerta.
#   2. Que quepa de pie: traza vertical desde el suelo hasta `ALTO_JUGADOR`.
#      Si choca, hay techo bajo y no se puede estar ahi.
# Y CADA ARISTA (solo entre vecinas vivas)
#   3. Escalon: la diferencia de suelo no puede pasar de `ESCALON` (45 es el
#      maximo que sube un Character de serie sin saltar).
#   4. Que no haya muro: traza horizontal de centro a centro a la altura del
#      pecho.
#
# Despues, un recorrido en anchura de origen a destino. Devuelve el mapa dibujado
# —para leerlo de un vistazo— y la lista de celdas del camino si lo encuentra.
#
# LIMITES QUE HAY QUE TENER PRESENTES: con paso de rejilla `PASO` no ve un hueco
# mas estrecho que eso, asi que puede decir "no hay camino" donde hay una rendija
# por la que si se cuela el jugador. Y no sabe nada de rampas: mide escalon entre
# centros de celda, asi que una cuesta continua muy inclinada la da por buena.

CX0, CY0 = 42250.0, -8750.0      # esquina de la rejilla, en el MUNDO
ANCHO, ALTO = 19, 14             # celdas en x, en y
PASO = 250.0

ORIGEN = (44675.0, -8250.0)      # donde aterrizas al cruzar la puerta de El Claro
DESTINO = (44305.0, -6083.0)     # donde nace el corredor Claro -> Santuario

ALTO_SONDA = 600.0               # desde donde se busca el suelo
HONDO = -800.0
ALTO_JUGADOR = 190.0             # capsula de pie
PECHO = 90.0
ESCALON = 45.0                   # lo que sube un Character sin saltar


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def traza(x0, y0, z0, x1, y1, z1):
    return sc("trace_world", {"start": {"x": x0, "y": y0, "z": z0},
                              "end": {"x": x1, "y": y1, "z": z1}})


def centro(i, j):
    return CX0 + i * PASO, CY0 + j * PASO


def celda_de(x, y):
    i = int(round((x - CX0) / PASO))
    j = int(round((y - CY0) / PASO))
    return max(0, min(ANCHO - 1, i)), max(0, min(ALTO - 1, j))


def run():
    suelo = {}
    viva = {}
    for j in range(ALTO):
        for i in range(ANCHO):
            x, y = centro(i, j)
            d = traza(x, y, ALTO_SONDA, x, y, HONDO)
            if d is None:
                viva[(i, j)] = False
                continue
            z = ALTO_SONDA - d
            suelo[(i, j)] = z
            # cabe de pie?
            viva[(i, j)] = traza(x, y, z + 15.0, x, y, z + ALTO_JUGADOR) is None

    def pasa(a, b):
        if not viva[a] or not viva[b]:
            return False
        if abs(suelo[a] - suelo[b]) > ESCALON:
            return False
        ax, ay = centro(a[0], a[1])
        bx, by = centro(b[0], b[1])
        z = max(suelo[a], suelo[b]) + PECHO
        return traza(ax, ay, z, bx, by, z) is None

    ini = celda_de(ORIGEN[0], ORIGEN[1])
    fin = celda_de(DESTINO[0], DESTINO[1])

    # recorrido en anchura
    previo = {ini: None}
    cola = [ini]
    cabeza = 0
    while cabeza < len(cola):
        c = cola[cabeza]
        cabeza += 1
        if c == fin:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (c[0] + dx, c[1] + dy)
            if v[0] < 0 or v[0] >= ANCHO or v[1] < 0 or v[1] >= ALTO:
                continue
            if v in previo:
                continue
            if not pasa(c, v):
                continue
            previo[v] = c
            cola.append(v)

    camino = []
    if fin in previo:
        c = fin
        while c is not None:
            camino.append(list(centro(c[0], c[1])) + [round(suelo[c])])
            c = previo[c]
        camino.reverse()

    enCamino = set()
    for p in camino:
        enCamino.add(celda_de(p[0], p[1]))

    mapa = []
    for j in range(ALTO - 1, -1, -1):
        fila = ""
        for i in range(ANCHO):
            c = (i, j)
            if c == ini:
                fila += "O"
            elif c == fin:
                fila += "D"
            elif c in enCamino:
                fila += "*"
            elif not viva[c]:
                fila += "#"
            elif c in previo:
                fila += "+"
            else:
                fila += "."
        mapa.append("y=%6d %s" % (int(CY0 + j * PASO), fila))

    return {
        "origen": {"celda": list(ini), "vive": viva[ini],
                   "suelo": round(suelo[ini]) if ini in suelo else None},
        "destino": {"celda": list(fin), "vive": viva[fin],
                    "suelo": round(suelo[fin]) if fin in suelo else None},
        "hay_camino": fin in previo,
        "celdas_del_camino": len(camino),
        "alcanzables_desde_origen": len(previo),
        "camino": camino,
        "leyenda": ("O origen  D destino  * camino  + alcanzable  "
                    ". pisable pero no alcanzable  # no se puede estar"),
        "x_de_izquierda_a_derecha": [int(CX0), int(CX0 + (ANCHO - 1) * PASO)],
        "mapa": mapa,
    }
