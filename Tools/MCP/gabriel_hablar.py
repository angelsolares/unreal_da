import json

# Gabriel interactuable: en esta primera fase no ataca, es su presentacion, asi
# que lo unico que hace es dejarse hablar. Su linea es de la narrativa del juego:
#
#     "Quien eres?"
#
# La pregunta la hace EL, no el jugador: Gabriel no reconoce a Malakh.
#
# ### NO SE INVENTA NADA: MISMO PATRON QUE SARIEL Y CASSIEL
#
# Se suelta un `BP_DA_Interactuable` ENCIMA del personaje —no en su lugar—, que
# solo aporta caja e interfaz; el prop conserva su malla, su escala y su
# animacion. Se le ponen `Verbo` y `Dialogo1..3` en la instancia, igual que hace
# `dialogos_malkuth.py` con los otros dos. Un campo por llamada, que el setter se
# deja campos por el camino si van juntos.
#
# ### LA CAJA SE DIMENSIONA CON LAS MEDIDAS DE PIE, NO CON LAS DEL EDITOR
#
# `get_actor_bounds` sobre Gabriel en el editor devuelve 782 de alto bajando a
# z=-216, que es la pose rota de la previsualizacion (ver `gabriel_mirada.py`).
# Las buenas son las de PIE: **594 de alto**, de z=-19 a 575. Si se dimensiona con
# las del editor, la caja sale torcida y hundida.
#
# La `Zona` del blueprint mide 60/60/90 de SEMIEJES —o sea 120x120x180— asi que:
#     escala_xy = ancho_deseado / 120     escala_z = alto_deseado / 180
# Con 300 de ancho y 594 de alto salen 2,5 y 3,3. El actor va a los pies
# (z = z_de_Gabriel - 280) y la caja, con su `relativeLocation.z = 90` escalado,
# queda centrada en 283: cubre de z=-14 a z=580, de los pies a la cabeza.
#
# ### OJO CON EL ESPACIO DE COORDENADAS DEL SUBMAPA
#
# Editando el `_Sub` como nivel suelto —que es la unica forma que funciona, ver
# `gabriel_visible.py`— los actores estan en las coordenadas DEL SUBMAPA, no en
# las del mundo. Gabriel esta en (520, 0) aqui y en (-65480, -15000) en el
# maestro: la Level Instance suma (-66000, -15000, 0). Por eso este script copia
# la X/Y de Gabriel en vez de escribir numeros del maestro, y por eso hay que
# verificar la posicion final CON EL MAESTRO CARGADO.
#
# ### EL ENCUADRE
#
# Misma cuenta que `interaccion_encuadre.py`, que si no la camara de inspeccion se
# queda en los 220 por defecto y Gabriel no cabe ni de lejos:
#     d = max(ancho/2, alto*0,889) * 1,6
# Con 300x594 manda el vertical: 845. Dividido por la escala del actor da
# `RelativeLocation.x = -338`.
#
# ### EL YAW DEL INTERACTUABLE ES EL DEL PERSONAJE + 180
#
# La camara vive en el **-X local** del interactuable y mira hacia su +X, o sea que
# el frente del interactuable apunta AL CONTRARIO que la cara del personaje. Si se
# le copia el yaw al personaje —que fue el primer intento— la camara acaba
# **detras** y le encuadras la espalda.
#
# Se saco midiendo los que ya funcionaban: `Interact_Sariel` esta a yaw 0 y Sariel
# a 180. (`Interact_Cassiel` tambien esta a 0 pero Cassiel a 124,2, asi que **ese
# encuadre esta torcido desde antes** — 55 grados de lado. No se ha tocado, pero
# ahi queda.)
#
# ### Y COMO GABRIEL GIRA, EL ENCUADRE TIENE QUE GIRAR CON EL
#
# `MirarAlJugador` mantiene el interactuable a `yaw_de_Gabriel + 180` en cada tick,
# a traves de la variable `Encuadre` de `BP_DA_GiantBoss` (referencia a Actor,
# Instance Editable, **default null** para que ningun otro jefe se entere). Asi la
# camara esta bien mires cuando mires, no solo al hablar.
#
# Verificado en PIE: jugador detras, Gabriel gira a yaw -6,7 y el interactuable se
# pone a 173,3; la camara cae en (-64641, -15098), del mismo lado que el jugador.

SUBASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CLASE = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable_C"
ETIQUETA = "Interact_Gabriel"

ALTO = 594.0        # medido en PIE
ANCHO = 300.0
PIES = 280.0        # cuanto hay del origen del actor a sus pies
BASE = {"x": 60.0, "y": 60.0, "z": 90.0}
MARGEN = 1.6

# ### DOS MENSAJES QUE SE ALTERNAN ENTRE CONVERSACIONES
#
# Gabriel no dice lo mismo cada vez. La primera vez pregunta, y la segunda te
# corta por no haber respondido a lo que preguntaba:
#
#   A) "Que mensaje traes?"
#   B) "No te pregunte quien pareces ser. / Te pregunte que mensaje traes."
#
# Y vuelve a A. En bucle.
#
# **OJO: `Dialogo1..3` NO son tres turnos, son tres RENGLONES a la vez.** El HUD
# los pinta apilados en el mismo frame (`hud_dialogo.py`: `HUD|DrawText` no parte
# el texto, por eso hay tres campos y el corte lo decide quien escribe). Asi que
# alternar entre conversaciones no es encadenar lineas: hay que **reescribir** los
# tres campos al terminar cada charla. Por eso B ocupa dos renglones y A uno.
#
# ### DONDE VIVE LA ALTERNANCIA, Y POR QUE AHI
#
# En `BP_DA_GiantBoss`, no en `BP_DA_Interactuable`. El sitio "natural" seria el
# evento `Interact` del interactuable, pero **`interaccion_inspeccionar.py` lo
# reconstruye nodo a nodo y borra todo lo que no sea un evento**: cualquier cosa
# que se meta ahi se pierde al relanzarlo. Y es un blueprint compartido por siete
# interactuables, asi que tocarlo arriesga las otras seis zonas.
#
# Gabriel ya tiene Tick (`MirarAlJugador`) y ya guarda la referencia al
# interactuable en `Encuadre`, asi que la alternancia va ahi y no toca nada
# compartido. `AlternarDialogo` se llama desde el mismo Tick, detras de
# `MirarAlJugador`.
#
# **Detecta el FLANCO DE BAJADA de `Inspeccionando`**, o sea el momento en que
# cierras la conversacion, y escribe entonces el set de la proxima. Al salir, no
# al entrar: asi la primera vez que hablas ves A, no B. Como el HUD solo dibuja
# mientras `Inspeccionando` es true, el cambio nunca se ve en pantalla.
#
# Variables en el jefe: `MensajeA1`, `MensajeB1`, `MensajeB2` (String, Instance
# Editable, ahi se editan los textos) y `TurnoB` / `HablandoAntes` (estado de
# runtime, no editables). Con `Encuadre` a null —el jefe de la arena— la funcion
# no hace nada.

VERBO = "Hablar"
# El set A, que es con el que arranca. El B vive en las variables del jefe.
LINEAS = ["¿Qué mensaje traes?", "", ""]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    sc("load_level", {"level_path": SUBASSET})
    out = {"nivel": sc("get_current_level", {})}

    jefe = busca("GC2_Gabriel")
    if jefe is None:
        return {"error": "no esta GC2_Gabriel", "hecho": out}
    tj = at("get_actor_transform", {"actor": jefe})

    esc_xy = ANCHO / (BASE["x"] * 2.0)
    esc_z = ALTO / (BASE["z"] * 2.0)
    xform = {"location": {"x": tj["location"]["x"], "y": tj["location"]["y"],
                          "z": tj["location"]["z"] - PIES},
             "rotation": {"pitch": 0.0, "yaw": tj["rotation"]["yaw"], "roll": 0.0},
             "scale": {"x": esc_xy, "y": esc_xy, "z": esc_z}}

    a = busca(ETIQUETA)
    if a is None:
        a = sc("add_to_scene_from_class", {"actor_type": {"refPath": CLASE}, "name": ETIQUETA,
                                           "xform": xform, "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": a, "label": ETIQUETA})
        out["actor"] = "creado"
    else:
        out["actor"] = "ya estaba"
    at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xform})

    ot("set_properties", {"instance": a, "values": json.dumps({"Verbo": VERBO})})
    for i, linea in enumerate(LINEAS):
        ot("set_properties", {"instance": a,
                              "values": json.dumps({"Dialogo%d" % (i + 1): linea})})

    ancho = 2.0 * max(BASE["x"] * esc_xy, BASE["y"] * esc_xy)
    alto = 2.0 * BASE["z"] * esc_z
    d = max(ancho / 2.0, alto * 0.889) * MARGEN
    for c in at("get_components", {"actor": a}):
        if c["refPath"].endswith("Camara"):
            ot("set_properties", {"instance": c, "values": json.dumps(
                {"RelativeLocation": {"x": round(-d / esc_xy, 1)}})})
            ot("set_properties", {"instance": c, "values": json.dumps(
                {"RelativeLocation": {"z": BASE["z"]}})})
            out["camara"] = json.loads(ot("get_properties", {"instance": c,
                                                             "properties": ["RelativeLocation"]}))

    out["leido"] = json.loads(ot("get_properties", {"instance": a, "properties":
                                                    ["Verbo", "Dialogo1", "Dialogo2", "Dialogo3"]}))
    out["caja"] = {"ancho": round(ancho), "alto": round(alto), "distancia": round(d),
                   "esc": [round(esc_xy, 2), round(esc_z, 2)]}

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [SUBASSET]})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": SUBASSET})
    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = sc("get_current_level", {})
    return out
