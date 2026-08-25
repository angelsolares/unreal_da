# -*- coding: utf-8 -*-
"""El arbol de guerrero propio de DA: BT_DA_Guerrero, con el compromiso alineado.

    node ue.mjs py bt_guerrero_da.py

POR QUE EXISTE. Tras escalar los alcances (la espada llega a 444 en el mundo, no a
243), el compromiso de la IA se quedo donde estaba: el MoveTo de mele de BT_WarriorAI
para a 150 cm de superficie (242 centro a centro) y el enemigo cruzaba unos 250 cm de
arco de espada RECIBIENDO GOLPES GRATIS. Medido en la Forja: dos Lanceros pasaron de
costar 84 de daño a costar 7.

EL NUMERO NO ES UNA PROPORCION, ES UN BARRIDO. Escalar el compromiso en proporcion al
alcance (preferida 366) MATA el encuentro: 0%% de victorias, porque la defensa del
jugador (esquiva, pociones) no escalo con el. El acantilado esta entre 300 y 310, y el
valor que deja el veredicto de «Romper la linea» sin ningun rojo es **parada 240 /
decision 250** (VV~V~VVVV, 94%% a espada sola, hp 74, cero atascos). En el motor eso es
**AcceptableRadius 190** en el MoveTo de mele: 240 = 190 + 50 de capsula del enemigo.

EL ASSET DE DCS NO SE TOCA. Se duplica BT_WarriorAI a /Game/DarkAngels/AI/BT_DA_Guerrero
y los cuatro BP_DA_* de mele apuntan su `BehaviorTreeAsset` (variable heredada de
BP_BaseAI) a la copia. El Arquero sigue con BT_ArcherAI: se barrio subirle la
distanciaMinima y sale al reves — retrocediendo no dispara.

OJO CON EL REPOSITORIO: la copia es CONTENIDO DE PAGO duplicado y va en .gitignore.
Lo que viaja en git es esta pasada, que la regenera.

Los otros tres umbrales del arbol se quedan como estan a proposito:
  - "Is In Attack Range?" < 500: la puerta de combate; la pelea nueva vive en 240-500.
  - "Distance Check" > 250: el ataque especial desde lejos. Con la parada nueva en 282
    de centro, ahora puede dispararse desde la posicion de reposo — MAS ataques a
    distancia, que es justo la direccion buena.
  - El MoveTo agresivo de radio 50: es sabor (presion), no compromiso.
"""
import unreal, json, os

SRC = "/Game/DynamicCombatSystem/DCS/Blueprints/AI/Warrior/BT_WarriorAI"
DST = "/Game/DarkAngels/AI/BT_DA_Guerrero"
RADIO_NUEVO = 190.0
BPS = ["BP_DA_Lancero", "BP_DA_Vigilante", "BP_DA_Heraldo", "BP_DA_Inspector"]
BASE_BP = "/Game/DarkAngels/Blueprints/Enemies/"

svc = unreal.BehaviorTreeService
fallos = []

# 1. La copia. Idempotente: si ya existe se reutiliza y solo se reasegura el valor.
if not unreal.EditorAssetLibrary.does_asset_exist(DST):
    ok = unreal.EditorAssetLibrary.duplicate_asset(SRC, DST)
    print("duplicado:", "OK" if ok else "FALLO")
    if not ok:
        raise RuntimeError("no se pudo duplicar BT_WarriorAI")
else:
    print("la copia ya existia; se reutiliza")

# 2. Encontrar el MoveTo de mele EN LA COPIA por su valor, no por su posicion.
#    DOS TRAMPAS DE ESTE SERVICIO, ambas costaron una pasada:
#      - SetNodePropertyValue quiere la ruta CON INDICES ("Sequence[2]"), y NO acepta
#        el guid. El propio JSON de get_tree la trae hecha en el campo `path`.
#      - Devuelve un STRUCT (BTPropertySetResult), no un bool: un fallo sigue siendo
#        "truthy" y un `if not resultado` no salta jamas. Hay que mirar `.success`.
arbol = json.loads(svc.get_tree(DST))
objetivo = {}
def busca(n):
    v = str((n.get("properties") or {}).get("AcceptableRadius", ""))
    if "DefaultValue=150." in v or "DefaultValue=190." in v:
        objetivo["path"] = n.get("path")
        objetivo["valor"] = v
    for h in n.get("children") or []:
        busca(h)
busca(arbol)
if not objetivo:
    raise RuntimeError("no encuentro el MoveTo de AcceptableRadius 150/190 en la copia")
print("MoveTo de mele:", objetivo["path"], " valor actual:", objetivo["valor"])

ruta = objetivo["path"]
r = svc.set_node_property_value(DST, ruta, "AcceptableRadius",
                                '(DefaultValue=%f,Key="")' % RADIO_NUEVO)
if not r.get_editor_property("success"):
    raise RuntimeError("SetNodePropertyValue: " + str(r.get_editor_property("error")))
svc.compile_and_save(DST)

# RELEER, que el true no vale nada.
releido = svc.get_node_property_value(DST, ruta, "AcceptableRadius")
print("AcceptableRadius releido:", releido)
if "190" not in str(releido):
    fallos.append("el AcceptableRadius no se quedo en 190: " + str(releido))

# Y confirmar que el ORIGINAL de DCS sigue intacto.
original = json.loads(svc.get_tree(SRC))
intacto = []
def busca2(n):
    p = n.get("properties") or {}
    v = str(p.get("AcceptableRadius", ""))
    if "DefaultValue=" in v:
        intacto.append(v)
    for h in n.get("children") or []:
        busca2(h)
busca2(original)
print("BT_WarriorAI (DCS) sigue con:", intacto)
if not any("150." in v for v in intacto):
    fallos.append("EL ARBOL DE DCS HA CAMBIADO y no debia")

# 3. Los cuatro BP de mele apuntan a la copia.
bt = unreal.load_asset(DST)
for nombre in BPS:
    ruta_bp = BASE_BP + nombre
    cls = unreal.load_class(None, ruta_bp + "." + nombre + "_C")
    cdo = unreal.get_default_object(cls)
    cdo.set_editor_property("BehaviorTreeAsset", bt)
    bp = unreal.load_asset(ruta_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(ruta_bp)
    # releer del CDO recargado
    v = unreal.get_default_object(unreal.load_class(None, ruta_bp + "." + nombre + "_C")) \
        .get_editor_property("BehaviorTreeAsset")
    marca = "OK" if (v and "BT_DA_Guerrero" in v.get_path_name()) else "FALLO"
    print("%-16s BehaviorTreeAsset -> %s  %s" % (nombre, v.get_name() if v else None, marca))
    if marca == "FALLO":
        fallos.append(nombre + " no apunta a la copia")

# 4. El arquero NO se toca, pero se deja constancia de que sigue en el suyo.
arq = unreal.get_default_object(unreal.load_class(None, BASE_BP + "BP_DA_Arquero.BP_DA_Arquero_C")) \
    .get_editor_property("BehaviorTreeAsset")
print("BP_DA_Arquero    BehaviorTreeAsset -> %s (sin cambios, a proposito)" % (arq.get_name() if arq else None))

# 5. La copia, guardada y comprobada en disco.
f = os.path.join(unreal.Paths.project_content_dir(), "DarkAngels/AI/BT_DA_Guerrero.uasset")
print("copia en disco:", os.path.exists(f), os.path.getsize(f) if os.path.exists(f) else "")

print("\n" + ("[OK] arbol propio montado y enchufado" if not fallos else "[FALLOS]\n   " + "\n   ".join(fallos)))
