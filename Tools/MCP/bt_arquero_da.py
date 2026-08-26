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

Se puso en 450, un pelo por encima de 433... Y SE REVIRTIO A 300 EL MISMO DIA. Lo de abajo
es el porque, y es el motivo de que esta pasada exista tal cual esta.

=========================  POR QUE VOLVIO A 300  =========================

El 450 no solo no entregaba la senal del 5.1: la EMPEORABA. Leida la forma del arbol:

    Selector
    +- Sequence [Is Close to Target < UMBRAL]              HUIR
    |    +- Selector
    |         +- Roll [IsNothingBehind invertido, Cooldown, Chance 60]
    |         +- Sequence [TimeLimit 3, Force Success]     <- SIEMPRE triunfa
    |              +- Jog, Run EQS Query, Move To
    +- Sequence  (Walk, apuntar, Can Shoot Arrow, Bow Attack)      DISPARAR

El `Force Success` de la secuencia interior hace que la rama de HUIR triunfe SIEMPRE, asi
que el Selector nunca cae a la de DISPARAR mientras el jugador este dentro del umbral. O
sea que este numero no dice "a partir de aqui retrocede": dice "a partir de aqui SE CALLA".

Y MIDE EN HORIZONTAL, no en 3D. Medido en PIE con el arquero en su balcon (328 cm de alto):
a 480 cm reales el blackboard decia 317, y a 1364 decia 1315, que es clavada la distancia
2D. Asi que 450 horizontales son 557 cm REALES desde el balcon, contra 443 con el 300.
Subirlo agrandaba la burbuja de silencio un 26%.

Encima la huida ni siquiera ocurre: el balcon mide 400x550, mas pequeño que el propio
umbral, o sea que la EQS no tiene adonde mandarlo. Se queda quieto Y callado. Verificado
jugandolo: Malakh entro a 424 cm y el Arquero no se movio un centimetro en toda la oleada.

CONCLUSION: cualquier umbral aqui solo compra silencio. La senal del 5.1 —"retrocede al
ver la lanza"— pide un PASO ATRAS con animacion propia, no una reubicacion por EQS que
ademas apaga el disparo. Se deja el 300 de DCS hasta que eso exista.

=========================================================================

LO QUE FALTA DEL 5.1, ADEMAS. Nunca fue "al ver a Malakh CON LANZA": el decorador
"Is Close to Target" es un BTDecorator_Blackboard y compara contra un LITERAL, no contra
una clave, asi que no puede depender del arma sin un decorador propio.

EL ASSET DE DCS NO SE TOCA. Se duplica a /Game/DarkAngels/AI/BT_DA_Arquero y BP_DA_Arquero
apunta ahi, igual que BT_DA_Guerrero para los de mele. La copia es CONTENIDO DE PAGO
duplicado y va en .gitignore: lo que viaja en git es esta pasada, que la regenera.

OJO CON LA CABECERA: este fichero NO puede llevar la linea "# -*- coding: utf-8 -*-". El
MCP hace exec() del codigo como CADENA y Python prohibe ahi la declaracion de codificacion;
sale un "Python execution failed" SIN mensaje. Primero le eche la culpa al docstring y era
falso: aislado despues caracter a caracter, es solo esa linea.
"""
import unreal, json, os

SRC = "/Game/DynamicCombatSystem/ArcheryModule/Blueprints/AI/Archer/BT_ArcherAI"
DST = "/Game/DarkAngels/AI/BT_DA_Arquero"
UMBRAL_VIEJO = 300.0
UMBRAL_NUEVO = 300.0      # REVERTIDO al de DCS: ver "POR QUE VOLVIO A 300" en el docstring
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
if str(int(UMBRAL_NUEVO)) not in str(releido):
    fallos.append("el umbral no se quedo en %d: %s" % (UMBRAL_NUEVO, releido))

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

print("\n" + (("[OK] umbral del Arquero en %d, y el arbol de DCS intacto" % UMBRAL_NUEVO)
              if not fallos else "[FALLOS]\n   " + "\n   ".join(fallos)))
