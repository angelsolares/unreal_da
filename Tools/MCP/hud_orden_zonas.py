import json

# Reordena el panel de salto para que siga el orden del recorrido del PDF, con
# Yesod al final. Las teclas siguen siendo NumPad 1-9 y 0 en orden, y lo que
# cambia es a que zona apunta cada una.
#
# Numeracion de estaciones, de la tabla de beats de las notas:
#   01 Jardin  03 Mirador  04 El Claro  05 Gazebo  06 Santuario  07 Puente
#   08 Anfiteatro  09 Elevador  10-12 Gabriel C1/C2/C3  13 Yesod
#
# Solo hay que reescribir dos cosas: el pin `NewLocation` de cada fila y las
# etiquetas de la leyenda. Las teclas y los `SetZonaActualDebug` van por indice
# de fila y no se tocan.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = BP + ":SaltoZonas_Tick"
DIB = BP + ":SaltoZonas_Dibujar"
VAR = "ZonaActualDebug"

# (etiqueta, nombre, x, y, z) en el orden del recorrido
ZONAS = [
    ("Num 1", "Jardin",     -59649.0, -60004.0,   138.0),   # 01
    ("Num 2", "Mirador",    -16000.0, -23800.0,   438.0),   # 03
    ("Num 3", "El Claro",    44000.0, -13650.0,    84.0),   # 04
    ("Num 4", "Gazebo",      64000.0,  15400.0,   184.0),   # 05
    ("Num 5", "Santuario",   43940.0,  47600.0,   118.0),   # 06
    ("Num 6", "Puente",      16000.0,  60000.0,  1532.0),   # 07
    ("Num 7", "Anfiteatro", -73649.0,  41996.0,   136.0),   # 08
    ("Num 8", "Elevador",   -74000.0,   8000.0,    94.0),   # 09
    ("Num 9", "Gabriel",    -66000.0, -15000.0,   281.0),   # 10-12 (tramo C2)
    ("Num 0", "Yesod",      -92000.0,  16000.0, 13213.0),   # 13, el final
]

FILA = 34.0
ANCHO = 330.0
Y0 = 300.0


def call(tool, args):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + tool,
                        json.dumps(args))["returnValue"]


def dsl_dibujar():
    alto = 56.0 + len(ZONAS) * FILA
    l = ["(fn SaltoZonas_Dibujar ()",
         "  (bind sx (.x (Viewport|GetViewportSize)))",
         "  (bind z (Variables|Default|Get" + VAR + "))",
         "  (bind x0 (- sx %.1f))" % (ANCHO + 20.0),
         '  (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.72)'
         ' x0 %.1f %.1f %.1f)' % (Y0, ANCHO, alto),
         '  (HUD|DrawText self "SALTO DE ZONA"'
         ' (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0)'
         ' (+ x0 14.0) %.1f 0 1.35)' % (Y0 + 10.0),
         "  (if (>= z 0)",
         '    (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 0.22)'
         ' (+ x0 6.0) (- (+ %.1f (* z %.1f)) 4.0) %.1f %.1f))'
         % (Y0 + 48.0, FILA, ANCHO - 12.0, FILA - 4.0)]
    for i, (etiqueta, nombre, _x, _y, _z) in enumerate(ZONAS):
        col = ('(Utilities|Struct|MakeLinearColor'
               ' (select (== z %d) 1.0 0.86)'
               ' (select (== z %d) 0.88 0.9)'
               ' (select (== z %d) 0.45 1.0) 1.0)' % (i, i, i))
        l.append('  (HUD|DrawText self "%s   %s" %s (+ x0 14.0) %.1f 0 1.2)'
                 % (etiqueta, nombre, col, Y0 + 48.0 + i * FILA))
    l.append("  (return))")
    return "\n".join(l)


def run():
    # Las filas del grafo se identifican por la Y con la que se colocaron.
    filas = []
    for n in call("find_nodes", {"graph": {"refPath": TICK}, "title": ""}):
        info = call("get_node_infos", {"nodes": [n]})[0]
        for p in info["input_pins"]:
            if p["name"] == "NewLocation":
                filas.append((info["position"]["y"], p["pin_id"]))
    filas.sort(key=lambda t: t[0])

    puestas = []
    for i, (_y, pin_id) in enumerate(filas):
        if i >= len(ZONAS):
            break
        _e, nombre, x, y, z = ZONAS[i]
        call("set_pin_value", {"pin": pin_id,
                                "value": "(X=%.3f,Y=%.3f,Z=%.3f)" % (x, y, z)})
        puestas.append(nombre)

    call("write_graph_dsl", {"graph": {"refPath": DIB}, "code": dsl_dibujar()})
    call("compile_blueprint", {"blueprint": {"refPath": BP}})
    return {"orden": puestas, "compila": "SI"}
