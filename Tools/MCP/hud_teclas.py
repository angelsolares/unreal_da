import json

# Cambia las teclas del salto de zona y su leyenda de una sola vez.
#
# Historial de por que se acabo en el teclado numerico:
#   1-9 y 0  -> las coge DCS para los hechizos (IMC_Player)
#   F1-F10   -> las coge el VIEWPORT de Unreal para los modos de vista; F3 es
#               wireframe, asi que al saltar de zona te aparecia el escenario
#               nuevo en wireframe
#   NumPad   -> libres en los dos sitios
#
# Si el teclado no tiene bloque numerico, cambiar TECLAS y ETIQUETAS y relanzar.
# Otras familias libres, por si hiciera falta: LeftBracket / RightBracket /
# Semicolon / Quote / Comma / Period / Slash / Backslash / Hyphen / Equals.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = BP + ":SaltoZonas_Tick"
DIB = BP + ":SaltoZonas_Dibujar"
VAR = "ZonaActualDebug"

TECLAS = ["NumPadOne", "NumPadTwo", "NumPadThree", "NumPadFour", "NumPadFive",
          "NumPadSix", "NumPadSeven", "NumPadEight", "NumPadNine", "NumPadZero"]
ETIQUETAS = ["Num 1", "Num 2", "Num 3", "Num 4", "Num 5",
             "Num 6", "Num 7", "Num 8", "Num 9", "Num 0"]
NOMBRES = ["Jardin", "Mirador", "El Claro", "Gazebo", "Santuario",
           "Puente", "Yesod", "Anfiteatro", "Elevador", "Gabriel"]

FILA = 34.0
ANCHO = 330.0


def call(tool, args):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + tool,
                        json.dumps(args))["returnValue"]


def dsl_dibujar():
    alto = 56.0 + len(NOMBRES) * FILA
    l = ["(fn SaltoZonas_Dibujar ()",
         "  (bind sx (.x (Viewport|GetViewportSize)))",
         "  (bind z (Variables|Default|Get" + VAR + "))",
         "  (bind x0 (- sx %.1f))" % (ANCHO + 20.0),
         '  (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.72)'
         ' x0 90.0 %.1f %.1f)' % (ANCHO, alto),
         '  (HUD|DrawText self "SALTO DE ZONA"'
         ' (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0)'
         ' (+ x0 14.0) 100.0 0 1.35)',
         "  (if (>= z 0)",
         '    (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 0.22)'
         ' (+ x0 6.0) (- (+ 138.0 (* z %.1f)) 4.0) %.1f %.1f))' % (FILA, ANCHO - 12.0, FILA - 4.0)]
    for i, nombre in enumerate(NOMBRES):
        col = ('(Utilities|Struct|MakeLinearColor'
               ' (select (== z %d) 1.0 0.86)'
               ' (select (== z %d) 0.88 0.9)'
               ' (select (== z %d) 0.45 1.0) 1.0)' % (i, i, i))
        l.append('  (HUD|DrawText self "%s   %s" %s (+ x0 14.0) %.1f 0 1.2)'
                 % (ETIQUETAS[i], nombre, col, 138.0 + i * FILA))
    l.append("  (return))")
    return "\n".join(l)


def run():
    # Las teclas se cambian en su sitio, ordenando por la fila en la que se
    # coloco cada nodo al construir el grafo.
    lectores = []
    for n in call("find_nodes", {"graph": {"refPath": TICK}, "title": ""}):
        info = call("get_node_infos", {"nodes": [n]})[0]
        for p in info["input_pins"]:
            if p["name"] == "Key":
                lectores.append((info["position"]["y"], p["pin_id"]))
    lectores.sort(key=lambda t: t[0])

    puestas = []
    for i, (_y, pin_id) in enumerate(lectores):
        if i < len(TECLAS):
            call("set_pin_value", {"pin": pin_id, "value": TECLAS[i]})
            puestas.append(TECLAS[i])

    call("write_graph_dsl", {"graph": {"refPath": DIB}, "code": dsl_dibujar()})
    call("compile_blueprint", {"blueprint": {"refPath": BP}})
    return {"teclas": puestas, "compila": "SI"}
