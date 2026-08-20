# -*- coding: utf-8 -*-
import json

# `BP_DA_Aparicion`: hace que un actor se desvanezca o se materialice segun lo
# que lleves apuntado en el GameState. Es la cuarta y ultima salida del nudo de
# Sariel: **ORDEN**.
#
# El beat: le pides a Sariel que abra la puerta el, porque es su oficio. Se
# deshace en el Mirador -- y cuando llegas a El Claro esta alli, junto a la
# puerta, que ya no esta sellada.
#
# ### POR QUE NO SIRVE LA RECETA DEL FINISHER TAL CUAL
#
# `ApartarVecinos` de `BP_DA_HUD` saca el `BP_DissolveComponent` **del actor que
# va a disolver**, porque alli son `BP_BaseAI` y lo traen de serie. Sariel no:
# `NPC_Sariel` es un **`SkeletalMeshActor` pelado**, con un unico
# `SkeletalMeshComponent0` y ningun componente de DCS. Y sus alas son OTRO actor
# suelto (`Sariel_Alas`), ni siquiera un hijo pegado.
#
# La vuelta es que **el disolvedor no tiene por que vivir en el actor que se
# disuelve**: `StartDissolve` toma el componente a disolver como argumento
# (`self` = el `BP_DissolveComponent`, `Component` = la malla). Asi que este
# blueprint trae el suyo propio y se lo aplica a quien le digas, sin tocar los
# actores del nivel. La documentacion de DCS confirma la pieza que faltaba: el
# componente **sustituye los materiales** por el suyo, o sea que no exige nada
# de la malla de origen.
#
# ### `Objetivos` ES UN ARRAY PORQUE SARIEL SON TRES ACTORES
#
# El cuerpo, las alas y su caja de dialogo (`Interact_Sariel`). Los tres se van
# juntos: si la caja se quedara, seguirias hablando con el aire. `add_object_variable`
# acepta `container_type: ARRAY`, asi que la referencia a Actor sí puede ser lista.
#
# La colision se apaga o se enciende **a la vez que empieza el disolver**, no al
# terminarlo. Es a proposito: durante los 2,5 s que tarda, un Sariel medio
# transparente al que no puedes atravesar es peor que uno que ya no estorba. Y
# apagarla es justo lo que quita la caja de dialogo de en medio, porque la traza
# de DCS deja de encontrarla.
#
# ### EL QUE APARECE SE DISUELVE PRIMERO
#
# `StartDissolve` con `Reverse = true` **trae de vuelta algo que se fue**, asi que
# para materializar a alguien hay que haberlo desvanecido antes. Por eso el
# `BeginPlay` de las instancias con `Aparecer = true` lo disuelve nada mas
# arrancar: quedan en un estado conocido. Pasa a kilometros del jugador y detras
# de un anillo de acantilados, en los primeros 2,5 s de partida.
#
# ### LOS NOMBRES DE LAS FUNCIONES LLEVAN APELLIDO A PROPOSITO
#
# `VigilarAparicion` y no `Vigilar`; `AplicarDisolver` y no `Aplicar`. `Vigilar`
# ya existe en `BP_DA_Decision` y en `BP_DA_MarcarFlag`, y con un nombre repetido
# el lector del DSL le cuelga la llamada al blueprint equivocado --y, cuando de
# verdad hay dos nodos, el escritor elige mal en silencio--. Es la misma pega que
# obligo a llamar `CruzarPaso` a lo que iba a ser `Cruzar`.

CARPETA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Aparicion"
BPP = CARPETA + "/" + NOMBRE + "." + NOMBRE
BP = {"refPath": BPP}
DISOLVEDOR = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Dissolve/"
              "BP_DissolveComponent.BP_DissolveComponent_C")

# Ni el blanco del finisher (5,5,5,0) ni el rojo de la muerte (5,0,0,0): los dos
# estan cogidos y significan otra cosa. Oro, que es el color con el que Malkuth
# habla de lo divino. Es decision de arte, o sea de Angel: se cambia aqui.
COLOR = (5.0, 3.2, 1.2, 0.0)

APLICAR = """(fn AplicarDisolver (Mostrar)
  (Class|BPDissolveComponent|SetDissolveColor :self (Variables|Default|GetDisolver)
    :DissolveColor (Utilities|Struct|MakeLinearColor :R %s :G %s :B %s :A %s))
  (for _o (Variables|Default|GetObjetivos)
    (Collision|SetActorEnableCollision :self _o :bNewActorEnableCollision Mostrar)
    (for _c (Actor|GetComponentsByClass :self _o
              :ComponentClass "/Script/Engine.MeshComponent")
      (Interface|StartDissolve :self (Variables|Default|GetDisolver)
        :Component (Utilities|Casting|CastToPrimitiveComponent _c)
        :Reverse Mostrar))))
""" % COLOR

# UN SOLO `if`, y el `Hecho` se escribe DENTRO. La condicion se evalua una vez en
# el Branch, asi que da igual que `SetHecho` la invalide despues. Partirlo en dos
# `if` hermanos habria sido el error clasico: un `bind` sobre nodos puros no
# cachea nada, el segundo `if` reevaluaria `Hecho` --ya cambiado-- y no entraria.
VIGILAR = """(fn VigilarAparicion ()
  (bind _gs (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState)))
  (if (and (not (Variables|Default|GetHecho))
           (and (not (Utilities|String|IsEmpty (Variables|Default|GetRequisito)))
                (Class|BPDAGameState|Lleva :self _gs
                  :Nombre (Variables|Default|GetRequisito))))
    (Variables|Default|SetHecho true)
    (Class|BPDAGameState|MarcarFlag :self _gs
      :Nombre (Variables|Default|GetFlagAlPasar))
    (CallFunction|AplicarDisolver :Mostrar (Variables|Default|GetAparecer))))
"""

EVENTOS = """(event EventBeginPlay ()
  (if (Variables|Default|GetAparecer)
    (CallFunction|AplicarDisolver :Mostrar false)))

(event EventTick (DeltaSeconds)
  (CallFunction|VigilarAparicion))
"""


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g, todo):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        if not todo and tid.startswith("AddEvent|"):
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def params_puestos(g):
    nombres = set()
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        i = info(nodo)
        tid = str(i["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            for lado in ("output_pins", "input_pins"):
                if lado not in i:
                    continue
                for p in i[lado]:
                    nombres.add(p["name"])
    return nombres


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}

    if ast("exists", {"path": CARPETA + "/" + NOMBRE}):
        out["blueprint"] = "reutilizado"
    else:
        bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"

    # --- el disolvedor propio ---
    tenia = {}
    for c in at("get_components", {"actor": bt("get_default_object", {"blueprint": BP})}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c
    if "Disolver" not in tenia:
        at("add_component", {"owner": BP, "name": "Disolver",
                             "component_type": {"refPath": DISOLVEDOR}})
        out["disolver"] = "anadido"
    else:
        out["disolver"] = "ya estaba"

    # --- variables ---
    ya = str(bt("list_variables", {"blueprint": BP}))
    for n, t in (("Requisito", "string"), ("FlagAlPasar", "string"),
                 ("Aparecer", "bool"), ("Hecho", "bool")):
        if "'" + n + "'" not in ya:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": t})
    if "'Objetivos'" not in ya:
        bt("add_object_variable", {"blueprint": BP, "name": "Objetivos",
                                   "object_class": {"refPath": "/Script/Engine.Actor"},
                                   "container_type": "ARRAY"})
    for n in ("Objetivos", "Requisito", "FlagAlPasar", "Aparecer"):
        bt("set_variable_instance_editable",
           {"blueprint": BP, "variable_name": n, "instance_editable": True})

    # --- grafos ---
    # El EventGraph se vacia lo PRIMERO: si una pasada anterior dejo llamadas a
    # las funciones, borrarlas o reescribirlas con alguien llamandolas deja el
    # blueprint sin compilar y el script muere a mitad.
    eg = {"refPath": BPP + ":EventGraph"}
    out.setdefault("vaciados", {})["EventGraph"] = vaciar(eg, True)

    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
    for n in ("AplicarDisolver", "VigilarAparicion"):
        if n not in grafos:
            bt("add_function_graph", {"blueprint": BP, "graph_name": n})
    g = {"refPath": BPP + ":AplicarDisolver"}
    if "Mostrar" not in params_puestos(g):
        bt("add_function_param", {"graph": g, "param_name": "Mostrar",
                                  "param_type": "bool", "input_param": True})
    bt("compile_blueprint", {"blueprint": BP})

    for n, codigo in (("AplicarDisolver", APLICAR), ("VigilarAparicion", VIGILAR)):
        gg = {"refPath": BPP + ":" + n}
        out["vaciados"][n] = vaciar(gg, True)
        bt("write_graph_dsl", {"graph": gg, "code": codigo})
    bt("write_graph_dsl", {"graph": eg, "code": EVENTOS})

    bt("compile_blueprint", {"blueprint": BP})
    ast("save_assets", {"asset_paths": [CARPETA + "/" + NOMBRE]})

    # --- releer: el `true` de estas APIs solo dice que acepto la llamada ---
    for n in ("AplicarDisolver", "VigilarAparicion"):
        out[n] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + n}}))
    out["EventGraph"] = str(bt("read_graph_dsl", {"graph": eg}))
    out["variables"] = [str(v) for v in bt("list_variables", {"blueprint": BP})]
    # A quien apuntan de verdad las dos llamadas propias: el `type_id` de una
    # funcion propia es `|Nombre`, con la categoria VACIA.
    for n in bt("find_nodes", {"graph": eg, "title": ""}):
        tid = str(info(n)["type_id"])
        if "Aplicar" in tid or "Vigilar" in tid:
            out.setdefault("a_quien_llama", []).append(tid)
    return out
