import json

# Comprobacion final del Gazebo: que los dos interactuables estan bien atados y
# que la colision nueva para donde tiene que parar.
#
# `trace_world` devuelve la DISTANCIA al impacto, o null si no toca nada. Las dos
# primeras trazas son controles contra piezas que ya bloqueaban de antes: si
# fallan, es la traza la que esta mal tirada y no la colision.

SUB = "L_DA_Malkuth_Gazebo_Sub"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def traza(a, b):
    return sc("trace_world", {"start": {"x": a[0], "y": a[1], "z": a[2]},
                              "end": {"x": b[0], "y": b[1], "z": b[2]}})


def run():
    out = {"trazas": {
        "control: abajo al suelo": traza((64000, 16550, 600), (64000, 16550, 100)),
        "control: al pedestal": traza((63880, 16650, 250), (63880, 16900, 250)),
        "costado este": traza((64000, 16545, 302), (64400, 16545, 302)),
        "costado oeste": traza((64000, 16545, 302), (63600, 16545, 302)),
        "a la tableta": traza((64000, 16700, 302), (64000, 17100, 302)),
        "pasillo central (espera nada)": traza((64000, 16300, 302), (64000, 16850, 302)),
    }, "interactuables": {}}

    for a in sc("find_actors", {"name": "Interact_", "tag": "", "collision_channels": []}):
        if SUB not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        etiqueta = at("get_label", {"actor": a})
        leido = json.loads(ot("get_properties", {"instance": a, "properties": [
            "Verbo", "ItemAlRecoger", "MallaMundo", "CantidadItem",
            "Dialogo1", "Dialogo2", "Dialogo3"]}))
        # `MallaMundo` guarda una ruta con el nombre interno del actor; se
        # traduce a su etiqueta para poder comprobarla de un vistazo.
        destino = str(leido["MallaMundo"])
        if destino != "None":
            for b in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
                if b["refPath"] in destino:
                    destino = at("get_label", {"actor": b})
                    break
        leido["MallaMundo"] = destino
        leido["ItemAlRecoger"] = str(leido["ItemAlRecoger"]).split("/")[-1].rstrip("'}")
        out["interactuables"][etiqueta] = leido
    return out
