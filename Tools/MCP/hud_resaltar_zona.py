import json

# Tres retoques al panel de salto de zona:
#   - mas grande, con la misma fuente y el mismo dorado del mensaje de objetivo
#     de arriba (fuente 0, que es la que usa `HUD|DrawText` en todo el HUD)
#   - resalta la zona a la que se acaba de saltar, con una barra detras y el
#     texto en dorado
#   - para saber cual es, se guarda el indice en una variable del blueprint
#
# Los `Set` de la variable se INSERTAN en el grafo ya montado, detras de cada
# `SetActorLocation`, en vez de reconstruir la funcion: si se borrase y se
# volviese a crear, el nodo de llamada del EventGraph se quedaria colgando.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = BP + ":SaltoZonas_Tick"
DIB = BP + ":SaltoZonas_Dibujar"
VAR = "ZonaActualDebug"

ZONAS = [("F1", "Jardin"), ("F2", "Mirador"), ("F3", "El Claro"), ("F4", "Gazebo"),
         ("F5", "Santuario"), ("F6", "Puente"), ("F7", "Yesod"), ("F8", "Anfiteatro"),
         ("F9", "Elevador"), ("F10", "Gabriel")]

FILA = 34.0      # alto de fila, antes 26
ANCHO = 330.0    # antes 235
ESC_TITULO = 1.35
ESC_FILA = 1.2


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
         ' x0 90.0 %.1f %.1f)' % (ANCHO, alto),
         '  (HUD|DrawText self "SALTO DE ZONA"'
         ' (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0)'
         ' (+ x0 14.0) 100.0 0 %.2f)' % ESC_TITULO,
         # La barra de resaltado va antes que los textos, para quedar detras.
         "  (if (>= z 0)",
         '    (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 0.22)'
         ' (+ x0 6.0) (- (+ 138.0 (* z %.1f)) 4.0) %.1f %.1f))' % (FILA, ANCHO - 12.0, FILA - 4.0)]
    for i, (tecla, nombre) in enumerate(ZONAS):
        # Dorado si es la zona actual, azulado si no.
        col = ('(Utilities|Struct|MakeLinearColor'
               ' (select (== z %d) 1.0 0.86)'
               ' (select (== z %d) 0.88 0.9)'
               ' (select (== z %d) 0.45 1.0) 1.0)' % (i, i, i))
        l.append('  (HUD|DrawText self "%s   %s" %s (+ x0 14.0) %.1f 0 %.2f)'
                 % (tecla, nombre, col, 138.0 + i * FILA, ESC_FILA))
    l.append("  (return))")
    return "\n".join(l)


def run():
    out = {}

    # --- La variable con la zona actual ---
    ya = [v["name"] if isinstance(v, dict) else str(v)
          for v in call("list_variables", {"blueprint": {"refPath": BP}})]
    if VAR not in str(ya):
        call("add_variable", {"blueprint": {"refPath": BP}, "name": VAR, "type_name": "int"})
    out["variable"] = VAR

    # --- Insertar un Set detras de cada SetActorLocation, en orden de fila ---
    movers = []
    for n in call("find_nodes", {"graph": {"refPath": TICK}, "title": ""}):
        info = call("get_node_infos", {"nodes": [n]})[0]
        nombres = [p["name"] for p in info["input_pins"]]
        if "NewLocation" in nombres:
            movers.append((info["position"]["y"], n, info))
    movers.sort(key=lambda t: t[0])

    puestos = 0
    for i, (_y, nodo, info) in enumerate(movers):
        # Si ya cuelga algo del `then`, es que este script ya se lanzo antes.
        ya_tiene = False
        for p in info["output_pins"]:
            if p["name"] == "then" and p["connected_pins"]:
                ya_tiene = True
        if ya_tiene:
            continue
        setter = call("create_node", {"graph": {"refPath": TICK},
                                      "type_id": "Variables|Default|Set" + VAR,
                                      "pos": {"x": 700, "y": i * 180}})
        call("connect_pins", {
            "output_pin": {"direction": "EGPD_Output", "index_id": 0,
                            "node": {"refPath": nodo["refPath"]}},
            "input_pin": {"direction": "EGPD_Input", "index_id": 0,
                           "node": {"refPath": setter["refPath"]}}})
        call("set_pin_value", {"pin": {"direction": "EGPD_Input", "index_id": 1,
                                        "node": {"refPath": setter["refPath"]}},
                                "value": str(i)})
        puestos += 1
    out["setters"] = puestos

    # --- El panel, mas grande y con resaltado ---
    call("write_graph_dsl", {"graph": {"refPath": DIB}, "code": dsl_dibujar()})
    call("compile_blueprint", {"blueprint": {"refPath": BP}})
    out["compila"] = "SI"
    return out
