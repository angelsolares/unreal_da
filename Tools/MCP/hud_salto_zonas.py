import json

# Salto rapido de zona desde el HUD, con las teclas 1-9 y 0, y su leyenda
# dibujada pegada al borde derecho.
#
# Por que teclas y no botones de raton: las 13 zonas **no son mapas separados**,
# son Level Instances dentro de `L_DA_Malkuth_Master`, asi que no hay `OpenLevel`
# que valga: es teletransportar al pawn dentro del mismo mapa, y es instantaneo.
# Y para clicar harian falta `bShowMouseCursor` + `bEnableClickEvents`, que en un
# juego con camara al raton se pelean con mirar.
#
# Por que en dos FUNCIONES nuevas y no reescribiendo el EventGraph: el lector de
# DSL devuelve los pines literales como `(bind x 0.5)` y el escritor los rechaza,
# asi que reescribir el grafo entero obligaria a reconstruir a mano el dibujado
# del objetivo y del banner, con riesgo de romperlos. Estas dos funciones se
# escriben en limpio y solo se enganchan con dos conexiones.
#
# Se sondea con `WasInputKeyJustPressed` en vez de crear bindings de input: no
# toca la configuracion de entrada del proyecto. Quitarlo luego es borrar las dos
# funciones y sus dos llamadas.
#
# Las cotas salen de trazas verticales sobre cada zona, +120 para dejar caer al
# jugador un poco en vez de encajarlo en el suelo.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"

ZONAS = [
    ("One",   "1", "Jardin",     -59649.0, -60004.0,   138.0),
    ("Two",   "2", "Mirador",    -16000.0, -23800.0,   438.0),
    ("Three", "3", "El Claro",    44000.0, -13650.0,    84.0),
    ("Four",  "4", "Gazebo",      64000.0,  15400.0,   184.0),
    ("Five",  "5", "Santuario",   43940.0,  47600.0,   118.0),
    ("Six",   "6", "Puente",      16000.0,  60000.0,  1532.0),
    ("Seven", "7", "Yesod",      -92000.0,  16000.0, 13213.0),
    ("Eight", "8", "Anfiteatro", -73649.0,  41996.0,   136.0),
    ("Nine",  "9", "Elevador",   -74000.0,   8000.0,    94.0),
    ("Zero",  "0", "Gabriel",    -66000.0, -15000.0,   281.0),
]


def dsl_dibujar():
    alto = 44.0 + len(ZONAS) * 26.0
    l = ["(fn SaltoZonas_Dibujar ()",
         "  (bind (sx sy) (HUD|GetViewportSize))",
         '  (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.62)'
         ' (- sx 250.0) 90.0 235.0 %.1f)' % alto,
         '  (HUD|DrawText self "SALTO DE ZONA" (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0)'
         ' (- sx 236.0) 100.0 0 1.05)']
    for i, (_c, tecla, nombre, _x, _y, _z) in enumerate(ZONAS):
        l.append('  (HUD|DrawText self "%s   %s"'
                 ' (Utilities|Struct|MakeLinearColor 0.86 0.9 1.0 0.95)'
                 ' (- sx 236.0) %.1f 0 0.95)' % (tecla, nombre, 130.0 + i * 26.0))
    l.append("  (return))")
    return "\n".join(l)


def dsl_tick():
    l = ["(fn SaltoZonas_Tick ()",
         "  (bind pc (Game|GetPlayerController 0))",
         "  (bind pawn (Game|GetPlayerCharacter 0))"]
    for clave, _t, _n, x, y, z in ZONAS:
        # El pin de vector se rellena con su literal de struct: no hace falta
        # un nodo Make Vector.
        # El target va POSICIONAL: `:self` esta reservado en el DSL para el
        # propio blueprint y no conecta el pin Target.
        l.append('  (if (Game|Player|WasInputKeyJustPressed pc "%s")' % clave)
        l.append('    (Transformation|SetActorLocation pawn'
                 ' :NewLocation "(X=%.3f,Y=%.3f,Z=%.3f)" :bTeleport true))' % (x, y, z))
    l.append("  (return))")
    return "\n".join(l)


def escribir(nombre, code):
    return execute_tool(
        "editor_toolset.toolsets.blueprint.BlueprintTools.write_graph_dsl",
        json.dumps({"graph": {"refPath": BP + ":" + nombre}, "code": code}))


def run():
    salida = {}
    for nombre, code in [("SaltoZonas_Dibujar", dsl_dibujar()),
                          ("SaltoZonas_Tick", dsl_tick())]:
        try:
            escribir(nombre, code)
            salida[nombre] = "escrito"
        except Exception as e:
            salida[nombre] = "ERROR " + str(e)[:400]
    try:
        execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools.compile_blueprint",
                     json.dumps({"blueprint": {"refPath": BP}}))
        salida["compilado"] = "sin error"
    except Exception as e:
        salida["compilado"] = "ERROR " + str(e)[:400]
    return salida
