# -*- coding: utf-8 -*-
#
# AGOTAR EL RECURSO NATURAL DEVUELVE LA ESPADA (§3 y §12, criterio 1).
#
# ### EL AGUJERO
#
# El PDF dice, con estas palabras, que Malakh vuelve a su espada principal cuando
# una temporal «se cambia, se sacrifica, AGOTA SU RECURSO NATURAL o es purgada al
# romperse el sello». Las otras tres estaban:
#
#   SustituirArmaTemporal -> SWAP        ArrojarArmaTemporal -> DISCARD
#   PurgarTemporales      -> SEAL BREAK
#
# La cuarta no. Con el arco robado a cero flechas te quedabas con un arco inutil
# en la mano hasta que cambiaras de arma o se rompiera el sello — y el §5.2 del
# PDF («cualquier encuentro se completa sin depender de un drop») se cae justo
# ahi: el arma que te habia dado ventaja pasa a ser un lastre del que no puedes
# soltarte. Verificado antes de tocar nada: el EventGraph del jugador son 16
# nodos y NINGUNO mira las flechas.
#
# Este es el unico de los doce criterios de aceptacion que estaba en rojo.
#
# ### COMO SE VIGILA, Y POR QUE NO EN EL TICK
#
# Un temporizador que corre SOLO mientras llevas un arma temporal:
#
#   - `SustituirArmaTemporal` —el embudo unico por el que pasa TODA adquisicion
#     de arma temporal— arranca `VigilarMunicion` cada 0,5 s, en sus dos ramas.
#     Ya arrancaba ahi el de `AplicarReglaDosManos`, asi que el sitio es el mismo
#     y el patron tambien.
#   - `VigilarMunicion` se APAGA SOLA: en cuanto no hay arma temporal —o en cuanto
#     acaba de devolver la espada— se limpia su propio temporizador.
#
# Media pulsacion de retraso como mucho, y cero coste mientras llevas la espada
# sola, que es la mayor parte de la partida. En el Tick seria al reves: pagarlo
# siempre para usarlo casi nunca.
#
# ### COMO SE SABE QUE EL ARMA GASTA FLECHAS
#
# Por el nombre del objeto, `DA_ElvenBow`, que es EXACTAMENTE como ya clasifica
# las cinco familias `ArrojarLanza` para elegir el montaje de descarte
# (`Utilities|GetObjectName` + `EqualExactly(String)`). No se estrena idioma.
#
# Hoy el arco es la unica familia con recurso natural — el PDF solo le da uno a
# el—. Cuando haya otra, se anade su nombre a la condicion y su recurso al conteo.
#
# ### LAS TRES DECISIONES QUE HAY DENTRO
#
#   1. **El carcaj NO se toca.** Se quita el arco y nada mas. Las flechas son
#      equipo BASE de Malakh (30 al empezar), no del arco robado: si mas tarde
#      roba otro arco, las que haya recogido siguen ahi.
#   2. **Con MUNICION INFINITA puesta, no dispara.** Es un boton de debug, y
#      `ReponerFlechas` rellena a 1 Hz: sin esta guarda habria una ventana en la
#      que el debug te desarma. El motivo de existir del boton es lo contrario.
#   3. **Un arco recogido con cero flechas se cae solo a los 0,5 s.** No es un
#      efecto colateral, es lo correcto: un arco sin munición es exactamente la
#      trampa que el §5.2 no quiere que exista, y asi el drop no te empeora.
#      El motivo queda escrito, asi que la pestaña WEAPON del Debug HUD lo dice
#      en vez de dejarte adivinando por que se fue.
#
# ### EL MOTIVO NUEVO: `AMMO OUT`
#
# `MotivoSalidaArma` tenia tres valores y ahora tiene cuatro. Se escribe en el
# mismo sitio que los otros tres y sale en la pestaña WEAPON sin tocar el HUD,
# porque el panel pinta la cadena tal cual.
#
# ### LA TRAMPA QUE CASI SE COLA
#
# **Lo que va detras de un `if` NO queda detras: queda dentro de su rama `else`.**
# Por eso `SetArmaTemporal 0` y la limpieza del temporizador van ANTES del
# `if _hayespada`, y ese `if` es la ULTIMA sentencia de su rama. Escrito al
# derecho, devolver la espada solo habria pasado cuando NO se encuentra la
# espada. Ver [[unreal-mcp-limites-blueprint]].

import json

BPP = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter.BP_DA_PlayerCharacter"
RUTA = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeDosManos"

FLECHA = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
          "Instances/DA_ElvenArrow.DA_ElvenArrow")
ARCO = "DA_ElvenBow"
INV = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Inventory/"
       "BP_InventoryComponent.BP_InventoryComponent_C")
CADA = 0.5

# Devolver la espada, calcado de `PurgarTemporales`: quitar el arma del
# inventario, buscar la EspadaBase y meterla en la ranura de mele.
VOLVER = '''        (Variables|Default|SetMotivoSalidaArma "AMMO OUT")
        (Modify|RemoveItem _inv _arma false 1)
        (Variables|Default|SetArmaTemporal 0)
        (Utilities|Time|ClearTimerbyFunctionName _self "VigilarMunicion")
        (bind (_hayespada _iespada) (Getters|FindItem _inv (Variables|Default|GetEspadaBase)))
        (if _hayespada
          (Equipment|UpdateItemInSlot (Variables|Components|GetEquipment) "NewEnumerator18" 0 0 (Getters|GetItemAtIndex _inv _iespada) "NewEnumerator1"))'''

VIGILAR = '''(fn VigilarMunicion ()
  (bind _self self)
  (bind _inv (Variables|Components|GetInventory))
  (bind _arma (Variables|Default|GetArmaTemporal))
  (bind (_hayflechas _iflecha) (Getters|FindItem _inv "%(flecha)s"))
  (bind (_fid _fit _fam) (Utilities|Struct|BreakFStoredItem (Getters|GetItemAtIndex _inv _iflecha)))
  (bind _quedan (select _hayflechas _fam 0))
  (Utilities|IsValid _arma
    (:"Is Valid"
      (if (and (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _arma) "%(arco)s")
               (and (< _quedan 1) (not (Variables|Default|GetMunicionInfinita))))
%(volver)s))
    (:"Is Not Valid"
      (Utilities|Time|ClearTimerbyFunctionName _self "VigilarMunicion"))))
''' % {"flecha": FLECHA, "arco": ARCO, "volver": VOLVER}

# El embudo del canje, TAL CUAL ESTABA mas una linea por rama: arrancar el
# vigilante. La linea de `AplicarReglaDosManos` no se toca.
SUSTITUIR = '''(fn SustituirArmaTemporal (NuevaArma)
  (bind _self self)
  (bind _armatemporal (Variables|Default|GetArmaTemporal))
  (Variables|Default|SetMotivoSalidaArma "SWAP")
  (Utilities|IsValid _armatemporal
    (:"Is Valid"
      (bind _asbp_inventory_component (Utilities|Casting|CastToBP_InventoryComponent (Actor|GetComponentByClass _self "%(inv)s")))
      (Modify|RemoveItem _asbp_inventory_component _armatemporal false 1)
      (Variables|Default|SetArmaTemporal NuevaArma)
      (Variables|Default|SetTUltimoTemporal (Utilities|Time|GetGameTimeInSeconds))
      (Utilities|Time|SetTimerbyFunctionName _self "AplicarReglaDosManos" 0.7)
      (Utilities|Time|SetTimerbyFunctionName _self "VigilarMunicion" %(cada)s true))
    (:"Is Not Valid"
      (Variables|Default|SetArmaTemporal NuevaArma)
      (Variables|Default|SetTUltimoTemporal (Utilities|Time|GetGameTimeInSeconds))
      (Utilities|Time|SetTimerbyFunctionName _self "AplicarReglaDosManos" 0.7)
      (Utilities|Time|SetTimerbyFunctionName _self "VigilarMunicion" %(cada)s true))))
''' % {"inv": INV, "cada": CADA}

FUNCIONES = [("VigilarMunicion", VIGILAR), ("SustituirArmaTemporal", SUSTITUIR)]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


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
    """Si esto falla, el MCP devuelve la llamada ENTERA como error y sin
    `returnValue` — el except de aqui no lo evita. Da igual para lo que importa:
    la pasada buena no llega a correr."""
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


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"prevuelo": {}, "escritas": [], "vaciados": {}}

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    # `SustituirArmaTemporal` tiene un PARAMETRO. El prevuelo lo escribe en un
    # grafo que no lo tiene, asi que ahi `NuevaArma` no existe: se sustituye por
    # la propia variable, que es del mismo tipo. Lo que se esta probando es que
    # los NODOS se puedan crear, no el cableado del parametro.
    for nombre, codigo in FUNCIONES:
        prueba = codigo.replace("(fn SustituirArmaTemporal (NuevaArma)",
                                "(fn SustituirArmaTemporal ()")
        prueba = prueba.replace("NuevaArma", "(Variables|Default|GetArmaTemporal)")
        out["prevuelo"][nombre] = prevuelo(prueba, nombre) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out

    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
