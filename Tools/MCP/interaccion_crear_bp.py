import json

# Crea `BP_DA_Interactuable`, el actor que hace que un prop nuestro entre en el
# sistema de interaccion QUE YA TIENE DCS. No montamos nada paralelo.
#
# COMO DETECTA DCS (leido de `BP_CombatCharacter`, grafo colapsado
# "Interaction Events", 34 nodos):
#   CheckForInteractable ->
#     start = GetActorLocation, end = start + ForwardVector * dist
#     tipos  = DCS|Utility|GetInteractableObjectTypes
#     Collision|CapsuleTraceForObjects  ->  BreakHitResult  ->  SetInteractionActor
#     Interaction|GetInteractionMessage (por interfaz)  ->  WB_InteractionMessage.UpdateWidget
#   Y con la tecla:  EnhancedInputActionIA_Interact -> CanOpenUI? -> Interaction|Interact
#
# O sea: **traza de capsula hacia delante contra el TIPO DE OBJETO
# `Interactable`**. No es solape ni es traza a la malla. De ahi salen los dos
# requisitos del volumen:
#   - ObjectType = ECC_GameTraceChannel2, que en `DefaultEngine.ini` se llama
#     "Interactable" (bTraceType=False, o sea canal de OBJETO, no de traza)
#   - CollisionEnabled = QueryOnly
# La malla no necesita colision: la traza pega en la caja, no en el mesh. Menos
# mal, porque las mallas de Tripo vienen sin colision.
#
# El tamanio del volumen es el "blanco" al que hay que apuntar, no un radio de
# proximidad: la distancia la pone la traza del personaje.
#
# POR QUE NO SE DUPLICA `BP_PickupActor`: seria la via facil para heredar la
# interfaz ya implementada, pero es un asset de DCS, de pago, y este repo es
# publico. Un duplicado suyo dentro de /Game/DarkAngels/ acabaria subido a
# GitHub. Se crea limpio y punto.

CARPETA = "/Game/DarkAngels/Blueprints/Interaccion"
NOMBRE = "BP_DA_Interactuable"
BP = CARPETA + "/" + NOMBRE + "." + NOMBRE
IFAZ = "/Game/DynamicCombatSystem/DCS/Blueprints/Interfaces/I_IsInteractable.I_IsInteractable_C"

CAJA = {"x": 60.0, "y": 60.0, "z": 90.0}


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def at(t, a):
    return execute_tool("editor_toolset.toolsets.actor.ActorTools." + t, json.dumps(a))["returnValue"]


def ot(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t, json.dumps(a))["returnValue"]


def st(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t, json.dumps(a))["returnValue"]


def run():
    out = {}
    st("create_folder", {"path": CARPETA})

    # Idempotente: estas herramientas abortan el script entero al primer fallo,
    # asi que hay que poder relanzarlo sobre lo ya creado.
    if st("exists", {"path": CARPETA + "/" + NOMBRE}):
        bp = {"refPath": BP}
        out["blueprint"] = "reutilizado"
    else:
        bp = bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                           "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = str(bp)

    # --- componentes ---
    tenia = {}
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": bp})}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c

    def componente(nombre, tipo):
        if nombre in tenia:
            return tenia[nombre]
        return at("add_component", {"owner": bp, "name": nombre,
                                    "component_type": {"refPath": tipo}})

    raiz = componente("Raiz", "/Script/Engine.SceneComponent")
    malla = componente("Malla", "/Script/Engine.SkeletalMeshComponent")
    zona = componente("Zona", "/Script/Engine.BoxComponent")
    at("set_parent_component", {"component": malla, "parent": raiz})
    at("set_parent_component", {"component": zona, "parent": raiz})

    # --- el volumen que ve la traza de DCS ---
    ot("set_properties", {"instance": zona, "values": json.dumps({
        "BoxExtent": CAJA,
        "RelativeLocation": {"x": 0.0, "y": 0.0, "z": CAJA["z"]},
        "BodyInstance": {"objectType": "ECC_GameTraceChannel2",
                          "collisionEnabled": "QueryOnly",
                          "collisionProfileName": "Custom"},
    })})
    # La malla no estorba a la traza.
    ot("set_properties", {"instance": malla, "values": json.dumps({
        "BodyInstance": {"collisionEnabled": "NoCollision"}})})

    # --- el verbo que saldra en el cartel ---
    if "Verbo" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "Verbo", "type_name": "string"})
    bt("set_variable_instance_editable",
       {"blueprint": bp, "variable_name": "Verbo", "instance_editable": True})

    # --- la interfaz: A MANO, el MCP no puede ---
    # No hay herramienta para declarar interfaces, y `set_properties` sobre el
    # blueprint no vale: resuelve al CDO (`Default__BP_DA_Interactuable_C`), y
    # `ImplementedInterfaces` vive en el UBlueprint, no en el CDO. Responde
    # "the following properties could not be set: ImplementedInterfaces".
    # Hay que marcarla en Class Settings > Implemented Interfaces > Add.
    out["interfaz"] = "PENDIENTE a mano: " + IFAZ

    bt("compile_blueprint", {"blueprint": bp})
    out["zona"] = json.loads(ot("get_properties", {"instance": zona,
                                                   "properties": ["BoxExtent", "RelativeLocation"]}))
    out["cuerpo"] = json.loads(ot("get_properties", {"instance": zona, "properties": ["BodyInstance"]}))["BodyInstance"]
    out["cuerpo"] = {k: out["cuerpo"][k] for k in ("objectType", "collisionEnabled", "collisionProfileName")}
    out["funciones"] = [str(f) for f in bt("list_functions", {"blueprint": bp})]
    return out
