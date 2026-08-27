# -*- coding: utf-8 -*-
#
# LAS FLECHAS, EN LA INSTANTANEA PREVIA AL SELLO (§7.2 y §11.3 del PDF).
#
# ### EL AGUJERO
#
# `TomarInstantanea` guardaba vida, stamina, pociones, la posicion de entrada y
# los transforms de los enemigos. NO guardaba las flechas. Y el carcaj de 30 es
# EQUIPO BASE de Malakh —no un arma temporal—, asi que era el unico recurso del
# jugador que se filtraba entre intentos: morir con 8 flechas y darle a reintentar
# te metia otra vez con 8, contra la misma pelea de siempre. Con la vida sí se
# restauraba, y con las pociones tambien; con las flechas no.
#
# El §7.2 pide "restaurar el snapshot definido para el encuentro; idealmente el
# estado exacto al entrar", y el §11.3 lo dice con todas las letras: "ammo natural
# si aplica". Aplica.
#
# ### POR QUE ES UN CALCO DE LAS POCIONES, Y NO UN INVENTO
#
# Todo lo que hace falta ya estaba escrito dos veces en este proyecto:
#
#   - Guardar:    `TomarInstantanea` lo hace con `DA_HealthPotion`.
#   - Restaurar:  `ReiniciarEncuentro` lo hace con `DA_HealthPotion`.
#   - El item:    `BP_DA_PlayerCharacter.ReponerFlechas` (el INFINITE AMMO del
#                 Debug HUD) ya usa `DA_ElvenArrow` con este mismo par
#                 FindItem -> GetItemAtIndex -> BreakFStoredItem.
#
# Asi que esto no estrena ningun nodo: copia la forma de las pociones cambiando
# el item. Si algun dia el carcaj deja de ser `DA_ElvenArrow`, este fichero y
# `ReponerFlechas` cambian juntos.
#
# ### LO QUE **NO** ENTRA, Y NO ES OLVIDO
#
# El §11.3 pide ocho cosas. Con esto quedan seis. Las dos que faltan se dejan
# fuera a proposito:
#
#   - **Arma temporal + off-hand + su corrupcion.** El propio §7.2 dice que "si
#     el checkpoint es el estandar previo al sello, normalmente solo habra equipo
#     base", y aqui SIEMPRE lo es: el Seal Break purga al salir de la arena
#     anterior, asi que a la siguiente se entra limpio. Guardar y devolver un arma
#     que nunca hay serian nodos muertos.
#   - **Cooldowns.** El PDF los condiciona a "si DCS lo expone de forma estable",
#     y hoy no hay una via leida y verificada para eso. Cuando la haya, se anade
#     aqui con la misma forma.
#
# ### POR QUE LA RESTAURACION ES UNA FUNCION APARTE Y NO UNA LINEA MAS
#
# Porque **`ReiniciarEncuentro` NO SE PUEDE REESCRIBIR**. Lo dijo el prevuelo:
#
#     AssertionError: The node could not be created / Game|SpawnActor does not exist
#
# El lector imprime `Game|SpawnActor` y el escritor no sabe crearlo — el mismo
# desajuste catalogo-lector/catalogo-escritor de `oleadas_arena.py`, ahora con
# nombre y apellidos. Y `ReiniciarEncuentro` respawnea a cada enemigo, asi que
# ese nodo es el corazon de la funcion: no hay version sin el.
#
# De ahi la forma que tiene esto:
#
#   - `TomarInstantanea` SI se puede reescribir entera (el prevuelo pasa), y se
#     reescribe.
#   - La restauracion vive en **`RestaurarFlechas`**, una funcion nueva escrita
#     desde cero, donde no hay ningun nodo prohibido.
#   - En `ReiniciarEncuentro` se injerta **un solo nodo** por cirugia: la llamada
#     a `RestaurarFlechas`, cosida entre el `RemoveItem` de las pociones y el
#     `Branch` que las repone. Ese punto se elige porque es la unica arista de
#     ese tramo con UN emisor y UN receptor: mas adelante el Branch abre dos
#     caminos que vuelven a juntarse en el `IsValid` del HUD, y coser ahi serian
#     dos aristas en vez de una.
#
# Va en `ReiniciarEncuentro` y no en `AlMorirElJugador` —que si es reescribible—
# porque el Debug HUD llama a `ReiniciarEncuentro` directamente desde RESTART
# FIGHT: colgarlo de la muerte dejaria ese boton sin reponer flechas.
#
# ### LAS OTRAS TRAMPAS
#
#   1. **El catalogo del escritor es mas corto que el del lector.** Releer un
#      grafo y volver a escribirlo NO es seguro (ver la cabecera de
#      `oleadas_arena.py`). Por eso hay PREVUELO: lo que se va a escribir se
#      escribe antes en `ZZProbeCol`, el grafo de usar y tirar. Si falla, no se
#      toca NADA.
#   2. **Nada puede ir detras de un `IsValid`.** Por eso `RestaurarFlechas`
#      TERMINA en su `IsValid`, sin `(return)` detras — igual que termina hoy
#      `TomarInstantanea`.
#   3. **`write_graph_dsl` sobre una funcion con cuerpo no lo reemplaza**: anade
#      otra copia y deja la vieja huerfana. Hay que vaciar primero.
#   4. **EL `Break` HAY QUE DESTRUCTURARLO, Y ESTO COSTO LA PRIMERA PASADA.**
#      `read_graph_dsl` imprime la lectura del `Amount` colapsada, en corto:
#
#          (Variables|Default|SetPocionesAlSellar (Utilities|Struct|BreakFStoredItem X))
#
#      Copiar ESO al escritor NO reproduce el grafo: conecta el PRIMER pin del
#      Break —el `Id`, que es un struct— y revienta con "Could not connect pin
#      Id_14_... to PocionesAlSellar". El `Break FStoredItem` tiene tres salidas
#      (Id, Item, Amount) y el escritor no adivina cual quieres. La cura es
#      nombrarlas:
#
#          (bind (_id _it _am) (Utilities|Struct|BreakFStoredItem X))
#          (Variables|Default|SetPocionesAlSellar _am)
#
#      Probado en `ZZProbeCol`: escribe bien, y al releerlo vuelve a salir en la
#      forma corta. Por eso la linea de POCIONES tambien se reescribe asi aunque
#      no cambie de comportamiento: reescribirla como se leia la habria roto.
#      Se probaron ademas `(bind _amount_4_f8900... )` —el nombre del pin, que es
#      lo que imprime el lector en `ReponerFlechas`— y `(.amount X)`: las dos
#      fallan.

import json

BPP = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena"
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeCol"

POCION = ("/Game/DynamicCombatSystem/DCS/Blueprints/Items/ObjectItems/"
          "Instances/DA_HealthPotion.DA_HealthPotion")
FLECHA = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
          "Instances/DA_ElvenArrow.DA_ElvenArrow")
STATS = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/StatsManager/"
         "BP_StatsManagerComponent.BP_StatsManagerComponent_C")
INV = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Inventory/"
       "BP_InventoryComponent.BP_InventoryComponent_C")

# El punto de entrada: el jugador, empujado hacia el borde de la arena. Sale tal
# cual de lo que ya habia; no se toca ni un numero.
_J = "_returnvalue"
_LOCJ = "(Transformation|GetActorLocation %s)" % _J
_LOCA = "(Transformation|GetActorLocation self)"
_DX = "(- (.x %s) (.x %s))" % (_LOCJ, _LOCA)
_DY = "(- (.y %s) (.y %s))" % (_LOCJ, _LOCA)
_LARGO = ("(Math|Float|Max(Float) (Math|Float|Max(Float)"
          " (Math|Float|Absolute(Float) %s) (Math|Float|Absolute(Float) %s)) 1.0)"
          % (_DX, _DY))
_ESCALA = ("(/ (+ (* (Variables|Default|GetRadioArena) 0.85) 150.0) %s)" % _LARGO)
_ENTRADA = ("(Math|Transform|MakeTransform (Math|Vector|MakeVector"
            " (+ (.x %s) (* %s %s)) (+ (.y %s) (* %s %s)) (.z %s))"
            " (Transformation|GetActorRotation %s))"
            % (_LOCA, _DX, _ESCALA, _LOCA, _DY, _ESCALA, _LOCJ, _J))

TOMAR = '''(fn TomarInstantanea ()
  (bind %(j)s (Game|GetPlayerCharacter 0))
  (Variables|Default|SetJugadorAlSellar %(j)s)
  (Variables|Default|SetPuntoEntrada %(entrada)s)
  (Utilities|Array|Clear (Variables|Default|GetTransformsEnemigos))
  (for _array_element (Variables|Default|GetEnemigos)
    (Utilities|Array|Add (Variables|Default|GetTransformsEnemigos) (Transformation|GetActorTransform _array_element)))
  (bind _asbp_stats_manager_component (Utilities|Casting|CastToBP_StatsManagerComponent (Actor|GetComponentByClass %(j)s "%(stats)s")))
  (bind _asbp_inventory_component (Utilities|Casting|CastToBP_InventoryComponent (Actor|GetComponentByClass %(j)s "%(inv)s")))
  (Utilities|IsValid _asbp_stats_manager_component
    (:"Is Valid"
      (Variables|Default|SetVidaAlSellar (Interface|GetStatValue _asbp_stats_manager_component (GameplayTags|MakeLiteralGameplayTag "(TagName=\\"Stat.Health.Current\\")")))
      (Variables|Default|SetStaminaAlSellar (Interface|GetStatValue _asbp_stats_manager_component (GameplayTags|MakeLiteralGameplayTag "(TagName=\\"Stat.Stamina.Current\\")")))
      (Utilities|IsValid _asbp_inventory_component
        (:"Is Valid"
          (bind (_itemfound _index) (Getters|FindItem _asbp_inventory_component "%(pocion)s"))
          (if _itemfound
            (bind (_pid _pit _pam) (Utilities|Struct|BreakFStoredItem (Getters|GetItemAtIndex _asbp_inventory_component _index)))
            (Variables|Default|SetPocionesAlSellar _pam)
            (else
              (Variables|Default|SetPocionesAlSellar 0)))
          (bind (_flechasfound _flechasindex) (Getters|FindItem _asbp_inventory_component "%(flecha)s"))
          (if _flechasfound
            (bind (_fid _fit _fam) (Utilities|Struct|BreakFStoredItem (Getters|GetItemAtIndex _asbp_inventory_component _flechasindex)))
            (Variables|Default|SetFlechasAlSellar _fam)
            (else
              (Variables|Default|SetFlechasAlSellar 0))))))))
''' % {"j": _J, "entrada": _ENTRADA, "stats": STATS, "inv": INV,
       "pocion": POCION, "flecha": FLECHA}

# `RestaurarFlechas`: quitar el carcaj entero y devolver el del snapshot. Termina
# en el `IsValid` a proposito — detras de un IsValid no puede ir nada, ni un
# `(return)`.
RESTAURAR = '''(fn RestaurarFlechas ()
  (bind _jug (Game|GetPlayerCharacter 0))
  (bind _inv (Utilities|Casting|CastToBP_InventoryComponent (Actor|GetComponentByClass _jug "%(inv)s")))
  (Utilities|IsValid _inv
    (:"Is Valid"
      (Modify|RemoveItem _inv "%(flecha)s" true)
      (if (> (Variables|Default|GetFlechasAlSellar) 0)
        (Modify|AddItem _inv "%(flecha)s" (Variables|Default|GetFlechasAlSellar))))))
''' % {"inv": INV, "flecha": FLECHA}

VARIABLES = [("FlechasAlSellar", "int", "0", "")]
FUNCIONES = [("TomarInstantanea", TOMAR), ("RestaurarFlechas", RESTAURAR)]

# La cirugia sobre `ReiniciarEncuentro`: donde cortar y que coser.
INJERTO_GRAFO = "ReiniciarEncuentro"
INJERTO_LLAMA = "RestaurarFlechas"
# El receptor de la arista que se corta se busca POR TITULO — y ojo, que
# `find_nodes` compara el titulo ENTERO: "Branch" encuentra, "Remove Item" NO,
# porque el suyo es "Remove Item\nTarget is BP Inventory Component".
#
# El emisor no se busca: se lee de quien alimenta HOY al Branch y se comprueba
# que sea el que esperamos. Si el grafo cambia y deja de serlo, esto aborta sin
# tocar nada en vez de coser a ciegas.
INJERTO_A = "Branch"
INJERTO_DE = "Modify|RemoveItem"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def prevuelo(codigo, nombre):
    """OJO CON EL `except`: atrapa el error en Python, pero el MCP acumula los
    fallos de escritura y devuelve la llamada ENTERA como error, sin `returnValue`.
    O sea que un prevuelo que falla no te da este informe bonito: te da el texto
    del RuntimeError y se acabo. Da igual para lo que importa —si el prevuelo
    falla, la pasada buena no llega a correr y no se toca ningun grafo—, pero no
    te sorprendas de no ver el diccionario."""
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        i = m.find("does not exist")
        vaciar(g)
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 70):i + 14]) if i > 0 else m[:200]


def pin(direccion, indice, nodo):
    return {"direction": direccion, "index_id": indice, "node": nodo}


def exec_pins(inf, clave):
    return [p for p in inf[clave] if str(p["type_id"]) == "Exec"]


def injertar():
    """Cose `CallFunction|RestaurarFlechas` en `ReiniciarEncuentro`, entre el
    `RemoveItem` de las pociones y el `Branch` que las repone. Idempotente: si el
    nodo ya esta, no hace nada. Y ABORTA —sin tocar— en cuanto el grafo no sea el
    que espera, que es preferible a coser en el sitio equivocado."""
    g = {"refPath": BPP + ":" + INJERTO_GRAFO}

    tipos = bt("find_node_types", {"graph": g, "type_id_filter": INJERTO_LLAMA,
                                   "context_pins": []})
    tipo = next((str(t) for t in tipos if INJERTO_LLAMA in str(t)), None)
    if tipo is None:
        return "ABORTADO: el editor no ofrece ningun tipo de nodo para " + INJERTO_LLAMA

    todos = bt("find_nodes", {"graph": g, "title": ""})
    for n in todos:
        if str(bt("get_node_infos", {"nodes": [n]})[0]["type_id"]) == tipo:
            return "ya estaba"

    ramas = bt("find_nodes", {"graph": g, "title": INJERTO_A})
    if len(ramas) != 1:
        return "ABORTADO: %d nodos '%s' en %s, esperaba 1" % (
            len(ramas), INJERTO_A, INJERTO_GRAFO)
    rama = ramas[0]
    inf_rama = bt("get_node_infos", {"nodes": [rama]})[0]
    entradas = exec_pins(inf_rama, "input_pins")
    if len(entradas) != 1 or len(entradas[0]["connected_pins"]) != 1:
        return "ABORTADO: el Branch no tiene exactamente una entrada exec conectada"
    destino = pin("EGPD_Input", entradas[0]["pin_id"]["index_id"], rama)
    origen_c = entradas[0]["connected_pins"][0]
    inf_origen = bt("get_node_infos", {"nodes": [origen_c["node"]]})[0]
    if str(inf_origen["type_id"]) != INJERTO_DE:
        return "ABORTADO: al Branch le entra %s, esperaba %s" % (
            inf_origen["type_id"], INJERTO_DE)
    origen = pin("EGPD_Output", origen_c["index_id"], origen_c["node"])

    pos = inf_rama["position"]
    nuevo = bt("create_node", {"graph": g, "type_id": tipo,
                               "pos": {"x": int(pos["x"]) - 380,
                                       "y": int(pos["y"]) + 260}})
    inf_nuevo = bt("get_node_infos", {"nodes": [nuevo]})[0]
    ent_n = exec_pins(inf_nuevo, "input_pins")
    sal_n = exec_pins(inf_nuevo, "output_pins")
    if len(ent_n) != 1 or len(sal_n) != 1:
        bt("delete_node", {"node": nuevo})
        return "ABORTADO: el nodo nuevo no tiene un exec de entrada y otro de salida"

    bt("break_pins", {"output_pin": origen, "input_pin": destino})
    bt("connect_pins", {"output_pin": origen,
                        "input_pin": pin("EGPD_Input", ent_n[0]["pin_id"]["index_id"], nuevo)})
    bt("connect_pins", {"output_pin": pin("EGPD_Output", sal_n[0]["pin_id"]["index_id"], nuevo),
                        "input_pin": destino})
    return "cosido: %s -> %s -> %s" % (INJERTO_DE, INJERTO_LLAMA, INJERTO_A)


def run(solo_prevuelo=False):
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"variables": [], "prevuelo": {}, "escritas": [], "vaciados": {}}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto, cont in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
            continue
        vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                  "variableType": tipo, "defaultValue": defecto,
                                  "containerType": cont})
        out["variables"].append(nombre + " (creada)")

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    # 1. PREVUELO ENTERO.
    for nombre, codigo in FUNCIONES:
        fallo = prevuelo(codigo, nombre)
        out["prevuelo"][nombre] = fallo or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out
    if solo_prevuelo:
        out["abortado"] = "solo prevuelo, por peticion"
        return out

    # 2. La pasada buena.
    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    # `RestaurarFlechas` tiene que existir y estar compilada ANTES de poder
    # crear el nodo que la llama.
    bt("compile_blueprint", {"blueprint": BP})
    out["injerto"] = injertar()

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # 3. Releer siempre: el `true` de estas APIs solo dice que acepto la llamada.
    out["releido"] = {}
    for nombre in [f[0] for f in FUNCIONES] + [INJERTO_GRAFO]:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
