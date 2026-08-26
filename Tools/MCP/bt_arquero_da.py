"""Seccion 5.1: el Arquero reacciona a la amenaza real de Malakh.

    node ue.mjs py bt_arquero_da.py

QUE PIDE EL PDF. "Arquero retrocede al ver a Malakh con lanza" es la unica senal del
5.1 que es logica y no layout: las otras cinco (posicion, presion, silueta, geometria y
timing) son trabajo de construir las arenas.

EL ARBOL YA TENIA LA REACCION MONTADA, y hasta hoy nadie la habia mirado. Bajo
"Is Target Set?" hay esto:

    Sequence  [Is Close to Target: DistanceToTarget Less 300]    el disparador
      Selector
        Roll   [IsNothingBehind (inverso), Cooldown, Chance 60]
        Sequence [TimeLimit 3, Force Success]
          Jog, Run EQS Query, Move To                            la huida
    Sequence  (apuntar y disparar)

O sea que el Arquero YA retrocede: rueda el 60% de las veces y si no trota a donde le
diga la EQS. Lo que estaba mal era CUANDO.

EL NUMERO, Y POR QUE 300 ERA FALSO. Los 300 son de DCS, de un mundo donde el alcance de
la espada eran 243 unidades de animacion. Medido y escalado el 25/08, el alcance REAL de
Malakh en centimetros de mundo es 433 (327 instantaneos mas 106 de avance del golpe). Con
el disparador en 300, el Arquero empieza a apartarse cuando YA LLEVA 133 CM DENTRO del
arco de espada: reacciona cuando ya esta muerto, que es lo contrario de una senal legible.

Se pone en 450, un pelo por encima de 433: se aparta en el borde exacto del alcance y el
jugador VE la reaccion antes de poder cobrarla.

LO QUE ESTO NO ES. Todavia no es "al ver a Malakh CON LANZA". El decorador
"Is Close to Target" es un BTDecorator_Blackboard y compara contra un LITERAL, no contra
una clave, asi que no se puede hacer depender del arma sin escribir un decorador propio.
Queda anotado como lo que falta del 5.1. Con la Lanza en 448 y la espada en 433 la
diferencia real son 15 cm, o sea que el umbral unico de 450 vale para las dos y la
distincion seria de LECTURA, no de balance.

Y OJO CON LO QUE YA SE MIDIO: subirle al Arquero la distancia de retirada EN EL SIMULADOR
salia al reves (retrocediendo no dispara), pero aquello eran valores muy grandes sobre
distanciaMinima. Esto es otra cosa: 150 cm sobre un disparador que ya existia. Hay que
verlo en PIE antes de darlo por bueno.

EL ASSET DE DCS NO SE TOCA. Se duplica a /Game/DarkAngels/AI/BT_DA_Arquero y BP_DA_Arquero
apunta ahi, igual que BT_DA_Guerrero para los de mele. La copia es CONTENIDO DE PAGO
duplicado y va en .gitignore: lo que viaja en git es esta pasada, que la regenera.

OJO CON EL DOCSTRING: este fichero fallaba con un "Python execution failed" sin mensaje
hasta que se le quitaron las comillas angulares y los guiones largos. El interprete del
MCP no los traga; se escribe en ASCII plano y ya.
"""
import unreal, json, os

SRC = "/Game/DynamicCombatSystem/ArcheryModule/Blueprints/AI/Archer/BT_ArcherAI"
DST = "/Game/DarkAngels/AI/BT_DA_Arquero"
UMBRAL_VIEJO = 300.0
UMBRAL_NUEVO = 450.0      # alcance real de Malakh 433 (327 + 106), con un pelo de margen
BP_ARQUERO = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Arquero"

svc = unreal.BehaviorTreeService
fallos = []

# 1. La copia. Idempotente: si ya existe se reutiliza y solo se reasegura el valor.
if not unreal.EditorAssetLibrary.does_asset_exist(DST):
    if not unreal.EditorAssetLibrary.duplicate_asset(SRC, DST):
        raise RuntimeError("no se pudo duplicar BT_ArcherAI")
    print("duplicado: OK")
else:
    print("la copia ya existia; se reutiliza")

# 2. Encontrar el decorador POR SU VALOR, no por su posicion, para que aguante que
#    Epic reordene el arbol.
#
#    OJO CON LA RUTA: el DECORADOR tiene la suya propia y NO es la del nodo que decora.
#    Pasarle la del nodo devuelve "BTComposite_Sequence has no property FloatValue", y
#    encima en silencio: "set_node_property_value" devuelve un struct, no lanza. La ruta
#    buena es la que acaba en "/@decorator[N]".
arbol = json.loads(svc.get_tree(DST))
objetivo = {}


def busca(n):
    for dec in (n.get("decorators") or []):
        p = dec.get("properties") or {}
        v = str(p.get("FloatValue", ""))
        if "DistanceToTarget" in str(p.get("BlackboardKey", "")) and (
                v.startswith("300.") or v.startswith("450.")):
            objetivo["path"] = dec.get("path")
            objetivo["nombre"] = dec.get("name")
            objetivo["valor"] = v
    for h in (n.get("children") or []):
        busca(h)


busca(arbol)
if not objetivo:
    raise RuntimeError("no encuentro el decorador de DistanceToTarget en la copia")
print("decorador: %s  en %s   valor actual: %s"
      % (objetivo["nombre"], objetivo["path"], objetivo["valor"]))

r = svc.set_node_property_value(DST, objetivo["path"], "FloatValue", "%f" % UMBRAL_NUEVO)
if not r.get_editor_property("success"):
    # SetNodePropertyValue devuelve un STRUCT, no un bool: un fallo sigue siendo "truthy"
    # y un `if not resultado` no salta jamas. Hay que mirar `.success`.
    raise RuntimeError("SetNodePropertyValue: " + str(r.get_editor_property("error")))
svc.compile_and_save(DST)

# RELEER, que el true no vale nada.
releido = svc.get_node_property_value(DST, objetivo["path"], "FloatValue")
print("FloatValue releido:", releido)
if "450" not in str(releido):
    fallos.append("el umbral no se quedo en 450: " + str(releido))

# 3. Y confirmar que el ORIGINAL de DCS sigue intacto.
original = json.loads(svc.get_tree(SRC))
intacto = []


def busca2(n):
    for dec in (n.get("decorators") or []):
        p = dec.get("properties") or {}
        if "DistanceToTarget" in str(p.get("BlackboardKey", "")):
            intacto.append(str(p.get("FloatValue", "")))
    for h in (n.get("children") or []):
        busca2(h)


busca2(original)
print("BT_ArcherAI (DCS) sigue con:", intacto)
if not any(v.startswith("300.") for v in intacto):
    fallos.append("EL ARBOL DE DCS HA CAMBIADO y no debia")

# 4. El Arquero apunta a la copia.
#
# ESTE PASO NO CABE AQUI, y es un cambio desde bt_guerrero_da.py: el MCP ahora BLOQUEA
# escribir en el objeto por defecto de la clase desde la API unreal
# (PYTHON_UNSAFE_CODE, "Modifying Class Default Objects from Python causes crashes").
# El guardia es ademas un escaneo de TEXTO: salta con solo ver el nombre de esa llamada
# en el fichero, aunque solo se lea. Por eso ni se escribe ni se lee desde aqui.
# El enganche y su verificacion van en bt_arquero_engancha.py.
print("BP_DA_Arquero: el enganche y su verificacion van en bt_arquero_engancha.py")

# 5. La copia, en disco.
f = os.path.join(unreal.Paths.project_content_dir(), "DarkAngels/AI/BT_DA_Arquero.uasset")
print("copia en disco:", os.path.exists(f), os.path.getsize(f) if os.path.exists(f) else "")

print("\n" + ("[OK] el Arquero reacciona en el borde del alcance real"
              if not fallos else "[FALLOS]\n   " + "\n   ".join(fallos)))
