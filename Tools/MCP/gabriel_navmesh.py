import json
import math

# Navegacion para las camaras de Gabriel: sin `NavMeshBoundsVolume` no hay malla de
# navegacion, y sin ella el `MoveTo` de los Behaviour Trees no va a ningun lado.
# Es decir: los enemigos aparecen y se quedan plantados.
#
# EL VOLUMEN VA EN EL MAESTRO, no dentro del `_Sub` de la camara. La geometria de
# un Level Instance se funde en el mundo, asi que la malla se construye sobre ella
# igual, y de paso nos ahorramos un ciclo de edit/commit de la LI.
#
# ### HAY UN `SM_Piso_Camara` POR CAMARA, Y TODOS SE LLAMAN IGUAL
#
# La primera version buscaba `SM_Piso_Camara` a secas y se quedaba con el primero
# que apareciera. Le toco el de la Camara III y **planto la navegacion a 26 km de
# donde hacia falta**: el volumen `Nav_GabrielC3` quedo en (-92000, -15000) y la
# sala de los espejos, en (-66000, -15000), se quedo sin nada. Se tardo en ver
# porque el volumen estaba perfectamente construido: solo estaba en otra sala.
#
# Ahora se desambigua por CERCANIA a la Level Instance de la zona: de todos los
# pisos que se llamen igual, gana el que tenga su centro mas cerca de la LI.
#
# ### DOS AGENTES DE NAVEGACION, NO UNO
#
# El proyecto tiene `RecastNavMesh-Default` y `RecastNavMesh-Giant`. La malla se
# genera para los dos sobre el mismo volumen, asi que esto sirve igual a los
# enemigos pequenios y al jefe. Por eso arreglarlo ahora paga dos veces: lo
# necesita el punto 2 (los enemigos de la ronda) y el punto 4 (Gabriel
# persiguiendo).
#
# ### LA MALLA SE COMPRUEBA PROYECTANDO PUNTOS, NO MIRANDO EL VIEWPORT
#
# La sala tiene lamina de agua y nichos elevados. Que el volumen exista no
# significa que la malla cubra el suelo: hay que pedirle a la navegacion que
# proyecte varios puntos del anillo y ver si contesta. Eso lo hace
# `gabriel_navmesh_probar.py`.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
SUELO = "SM_Piso_Camara"

# zona -> (etiqueta del volumen, etiqueta de la Level Instance)
ZONAS = {
    "C2": ("Nav_GabrielC2", "LI_11_GabrielC2"),
    "C3": ("Nav_GabrielC3", "LI_12_GabrielC3"),
}
CUAL = "C2"

# El volumen por defecto mide 200x200x200, asi que la escala es la medida que se
# quiere entre 200. Se le da aire de sobra por arriba: la malla solo se genera
# donde hay suelo, pero si el volumen no llega al techo no cubre los escalones.
LADO_BASE = 200.0
MARGEN = 600.0     # cuanto se pasa del suelo por cada lado
ALTO = 1500.0


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def por_etiqueta(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    if not sc("get_current_level", {}).startswith(MAESTRO):
        sc("load_level", {"level_path": MAESTRO})

    etiqueta, li_nombre = ZONAS[CUAL]
    out = {"zona": CUAL}

    li = por_etiqueta(li_nombre)
    if li is None:
        return {"error": "no encuentro " + li_nombre}
    centro_li = at("get_actor_transform", {"actor": li})["location"]

    # --- el piso de ESTA camara, no el primero que aparezca ---
    piso, mejor = None, None
    candidatos = []
    for a in sc("find_actors", {"name": SUELO, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) != SUELO:
            continue
        b = at("get_actor_bounds", {"actor": a})
        cx = (b["max"]["x"] + b["min"]["x"]) / 2.0
        cy = (b["max"]["y"] + b["min"]["y"]) / 2.0
        d = math.hypot(cx - centro_li["x"], cy - centro_li["y"])
        candidatos.append([round(cx), round(cy), round(d)])
        if mejor is None or d < mejor:
            piso, mejor = a, d
    if piso is None:
        return {"error": "no encuentro " + SUELO}
    out["candidatos"] = candidatos
    out["elegido_a"] = round(mejor)

    b = at("get_actor_bounds", {"actor": piso})
    ancho = (b["max"]["x"] - b["min"]["x"]) + MARGEN * 2
    fondo = (b["max"]["y"] - b["min"]["y"]) + MARGEN * 2
    xform = {"location": {"x": (b["max"]["x"] + b["min"]["x"]) / 2.0,
                          "y": (b["max"]["y"] + b["min"]["y"]) / 2.0,
                          "z": b["min"]["z"] + ALTO / 2.0 - 200.0},
             "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
             "scale": {"x": ancho / LADO_BASE, "y": fondo / LADO_BASE,
                       "z": ALTO / LADO_BASE}}

    vol = por_etiqueta(etiqueta)
    if vol is None:
        vol = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": "/Script/NavigationSystem.NavMeshBoundsVolume"},
            "name": etiqueta, "xform": xform, "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": vol, "label": etiqueta})
        out["estado"] = "creado"
    else:
        out["estado"] = "ya estaba"
    # `set_actor_transform` resetea escala y rotacion si no se las pasas.
    at("set_actor_transform", {"actor": vol, "worldspace": True, "xform": xform})

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [MAESTRO]})
    t = at("get_actor_transform", {"actor": vol})
    bv = at("get_actor_bounds", {"actor": vol})
    out["piso"] = {"min": [round(b["min"][k]) for k in ("x", "y", "z")],
                   "max": [round(b["max"][k]) for k in ("x", "y", "z")]}
    out["volumen"] = {"pos": [round(t["location"][k]) for k in ("x", "y", "z")],
                      "esc": [round(t["scale"][k], 2) for k in ("x", "y", "z")],
                      "min": [round(bv["min"][k]) for k in ("x", "y", "z")],
                      "max": [round(bv["max"][k]) for k in ("x", "y", "z")]}
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": MAESTRO})
    return out
