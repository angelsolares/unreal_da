import json

# Sonda: que colision tiene puesta cada pieza de las Ruinas del Gazebo.
#
# DOS COSAS QUE HAY QUE SABER PARA LEER ESTO:
#   1. Fuera del modo edicion de un Level Instance, sus actores NO cuelgan de
#      `/Game/...` sino de `/Temp/Game/...<nombre>_LevelInstance_<hash>_0`.
#      Filtrar por la ruta del asset no encuentra nada; hay que buscar el nombre.
#   2. `find_actors` devuelve tambien los actores del mundo de PIE, con
#      `UEDPIE_0_` en la ruta, y siguen apareciendo un rato despues de parar la
#      sesion —ya invalidos: `get_label` revienta con ellos—. Hay que colarlos.
#   3. Las propiedades van en **camelCase** (`bodyInstance`,
#      `bEnablePerPolyCollision`), y la colision NO es un campo suelto: vive
#      dentro de `bodyInstance`. `ObjectTools.list_properties` da los nombres
#      buenos; pedir varios a la vez revienta entero si uno no existe en ese
#      tipo de componente.

SUB = "L_DA_Malkuth_Gazebo_Sub"
SALTAR = ("Monte", "Mata", "Arbol", "Abeto", "Roca", "Hiedra", "Ladera",
          "Cascada", "Relleno", "Luz_")


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def leer(comp, k):
    try:
        return json.loads(ot("get_properties", {"instance": comp, "properties": [k]})).get(k)
    except Exception:
        return None


def run():
    out = {"piezas": []}
    for a in sc("find_actors", {"name": "Gazebo_", "tag": "", "collision_channels": []}):
        if SUB not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        etiqueta = at("get_label", {"actor": a})
        if any(x in etiqueta for x in SALTAR):
            continue
        for c in at("get_components", {"actor": a,
                                       "component_type": {"refPath": "/Script/Engine.MeshComponent"}}) or []:
            # Se pregunta solo lo que existe en cada tipo: cada propiedad que no
            # esta escupe un error largo, y con doscientos actores la respuesta
            # se pasa de tamanio y se pierde el resultado entero.
            hueso = "Skeletal" in c["refPath"]
            cuerpo = leer(c, "bodyInstance") or {}
            malla = leer(c, "skeletalMeshAsset" if hueso else "staticMesh")
            out["piezas"].append({
                "n": etiqueta,
                "tipo": "SK" if hueso else "SM",
                "col": cuerpo.get("collisionEnabled"),
                "perfil": cuerpo.get("collisionProfileName"),
                "perpoly": leer(c, "bEnablePerPolyCollision") if hueso else "-",
                "malla": str(malla).split("/")[-1].rstrip("'}"),
            })
    return out
