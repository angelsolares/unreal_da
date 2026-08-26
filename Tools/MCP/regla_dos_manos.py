# -*- coding: utf-8 -*-
"""§4.1 del PDF: las armas a dos manos obligan a soltar el escudo.

    node ue.mjs script regla_dos_manos.py

EL PDF: «Definir explicitamente que armas a dos manos obligan a soltar el escudo.»
Hasta hoy no estaba definida NI EN UN SITIO NI EN OTRO: verificado en PIE, al dar la
Lanza —que es a dos manos— `BP_DI_WoodenShield_C` seguia equipado.

NO HACE FALTA INVENTAR NADA, y esa es la gracia. Las dos piezas ya existian:

  - El DATO. Los items de DA son data assets `BP_DA_Item_MeleeWeapon_C` y ya traen
    `TwoHanded`: Lanza True, Trompeta True, Espada False. Leido de los tres assets.
  - LA MECANICA. `BP_EquipmentComponent` de DCS tiene `IsTwoHandedWeaponEquipped`,
    `IsShieldEquipped` y `SetSlotHidden(Type, SlotIndex, IsHidden)`. La ranura del
    escudo es el valor `NewEnumerator6` de `E_ItemType` — sale de leer el propio
    `IsShieldEquipped`, que es quien manda, no de contar posiciones en el enum.

Lo unico que faltaba era la REGLA que las une, y va en nuestro lado: DCS no se toca.

POR QUE UN TEMPORIZADOR Y NO UNA LLAMADA DIRECTA. Equipar en DCS no es sincrono: el
item pasa por el inventario y la mano activa se actualiza despues. `CanjearTemporal` ya
lo sabia y por eso arma un `SetTimerbyFunctionName` de 0,6 s para `CorromperArmaTemporal`.
Se hace igual, a 0,7 s, para que la regla lea la mano YA cambiada. Preguntar antes
devuelve el arma vieja y la regla no dispara.

DONDE SE ENGANCHA. En `SustituirArmaTemporal`, que es el embudo unico: por ahi pasan el
canje del suelo (`BP_DA_DroppedWeapon.CanjearTemporal`) y el boton del Debug HUD
(`DarArmaTemporal`). La funcion tenia tres salidas —cast bueno, cast fallido, y sin arma
previa— y las tres acababan en `SetArmaTemporal`; se reescribe con una sola cola para que
el enganche sea uno y no tres.

DE PROPINA, EL SELLO DE TIEMPO DEL §8. En la misma cola se anota `TUltimoTemporal` con el
reloj de juego. Es lo que necesita el Mercy Drop del director de drops para saber cuanto
lleva el jugador sin herramienta, y no cuesta ni un nodo mas de recorrido.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter"
BPP = RUTA + ".BP_DA_PlayerCharacter"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeDosManos"

INV = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Inventory/"
       "BP_InventoryComponent.BP_InventoryComponent_C")
EQ = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Inventory/"
      "BP_EquipmentComponent.BP_EquipmentComponent_C")
RANURA_ESCUDO = "NewEnumerator6"      # E_ItemType, leido de IsShieldEquipped
AHORA = "(Utilities|Time|GetGameTimeinSeconds)"

VARIABLES = [
    # -1 quiere decir "nunca ha tocado un arma temporal". El director de drops lo
    # trata como "lleva sin arma desde que empezo la partida".
    ("TUltimoTemporal", "float", "-1.0"),
]

_EQCOMP = ('(Utilities|Casting|CastToBP_EquipmentComponent '
           '(Actor|GetComponentByClass self "%s"))' % EQ)
_INVCOMP = ('(Utilities|Casting|CastToBP_InventoryComponent '
            '(Actor|GetComponentByClass self "%s"))' % INV)

# LA REGLA ES SIMETRICA, Y ESO IMPORTA MAS DE LO QUE PARECE. Escribirla como "si es a
# dos manos, esconde el escudo" deja el escudo escondido PARA SIEMPRE en cuanto tocas una
# lanza: no hay nada que lo devuelva. Escrita como "la ranura del escudo esta escondida
# EXACTAMENTE CUANDO el arma en la mano es a dos manos", volver a un arma de una mano lo
# devuelve solo, y quedarse sin arma temporal —la rama "Is Not Valid"— tambien.
DOS_MANOS = """(fn AplicarReglaDosManos ()
  (bind _arma (Utilities|Casting|CastToBP_DA_Item_MeleeWeapon (Variables|Default|GetArmaTemporal)))
  (Utilities|IsValid _arma
    (:"Is Valid"
      (HiddenSlots|SetSlotHidden %(eq)s "%(ranura)s" 0
        (Class|BPDAItemMeleeWeapon|GetTwoHanded _arma)))
    (:"Is Not Valid"
      (HiddenSlots|SetSlotHidden %(eq)s "%(ranura)s" 0 false))))
""" % {"eq": _EQCOMP, "ranura": RANURA_ESCUDO}

# LA COLA VA DUPLICADA EN LAS DOS RAMAS A PROPOSITO, y no es descuido: el escritor del
# DSL no sabe continuar la ejecucion DESPUES de un nodo que ramifica —lo canta como
# "Unreachable code after branch"— asi que todo lo que tenga que pasar siempre hay que
# repetirlo en cada rama. Por eso el original ya duplicaba `SetArmaTemporal`.
# `RemoveItem` sigue llamandose solo si habia arma previa, igual que antes.
_COLA = """      (Variables|Default|SetArmaTemporal NuevaArma)
      (Variables|Default|SetTUltimoTemporal %(ahora)s)
      (Utilities|Time|SetTimerbyFunctionName self "AplicarReglaDosManos" 0.7)""" % {"ahora": AHORA}

SUSTITUIR = """(fn SustituirArmaTemporal (NuevaArma)
  (bind _vieja (Variables|Default|GetArmaTemporal))
  (Utilities|IsValid _vieja
    (:"Is Valid"
      (Modify|RemoveItem %(inv)s _vieja false 1)
%(cola)s)
    (:"Is Not Valid"
%(cola)s)))
""" % {"inv": _INVCOMP, "cola": _COLA}

# (nombre, codigo, parametros). El prevuelo escribe en un grafo suelto que NO tiene los
# parametros de la funcion real, asi que se los cambia por un local antes de probar: el
# banco tiene que comprobar el VOCABULARIO, no la firma.
FUNCIONES = [("AplicarReglaDosManos", DOS_MANOS, []),
             ("SustituirArmaTemporal", SUSTITUIR, ["NuevaArma"])]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(bt("get_node_infos", {"nodes": [nodo]})[0]["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})


def prevuelo(codigo, nombre, params):
    """El escritor del DSL tiene menos vocabulario que su lector, y `vaciar()` corre
    ANTES de escribir: sin prevuelo, un nodo que no existe deja la funcion en blanco.
    Y aqui una de las dos funciones YA EXISTE y funciona, o sea que perderla es peor."""
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    for p in params:
        cuerpo = cuerpo.replace("(" + p + ")", "()").replace(p, "_vieja")
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        i = m.find("does not exist")
        if i > 0:
            return "NO SE PUEDE ESCRIBIR: " + m[max(0, i - 90):i + 14]
        # El grafo de pruebas no tiene los parametros de la funcion real, asi que
        # ese error concreto NO dice nada del vocabulario: es del banco, no del codigo.
        if "Function parameter" in m:
            return None
        return m[:260]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"variables": [], "prevuelo": {}, "escritas": []}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
        else:
            vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                      "variableType": tipo, "defaultValue": defecto,
                                      "containerType": ""})
            out["variables"].append(nombre + " (creada)")
        # AddMemberVariable ignora el defaultValue en floats: se fija aparte.
        vue("SetVariableDefaultValue", {"blueprintPath": RUTA, "variableName": nombre,
                                        "defaultValue": defecto})

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    # GUARDAR LO QUE HAY ANTES DE TOCARLO: SustituirArmaTemporal ya funciona.
    out["copiaDeSeguridad"] = str(bt("read_graph_dsl",
                                     {"graph": {"refPath": BPP + ":SustituirArmaTemporal"}}))

    for nombre, codigo, params in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(codigo, nombre, params) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out

    for nombre, codigo, _p in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
        g = {"refPath": BPP + ":" + nombre}
        vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # RELEER, que el `true` del guardado no vale de nada.
    out["releido"] = {}
    for nombre, _c, _p in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
