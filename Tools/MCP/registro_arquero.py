"""Toma UNA muestra de la partida y la anota. Pensado para llamarse en bucle.

    node ue.mjs py registro_arquero.py

POR QUE EXISTE. El 26/08 se probo el umbral nuevo del Arquero (450 en vez de 300) moviendo
a Malakh por Python, y NO SE PUDO MEDIR SI DISPARA: el teleport le tira el blanco -Target
vacio en el blackboard- y toda la rama de apuntar cuelga de "Is Target Set?". Asi que el
Arquero patrullaba en vez de combatir, y salieron tres tandas seguidas con 100 de vida.

La unica forma de medirlo es que alguien lo JUEGUE. Esto anota lo que pasa mientras.

COMO SE SEPARA EL DAÑO DE FLECHA DEL DE ESPADA, que es la gracia: la receta "Romper la
linea" entra DE UNO EN UNO. La oleada 3 es el Arquero SOLO, asi que cualquier vida que
Malakh pierda mientras `oleada == 3` es de flecha, y no hace falta identificar al autor.

LAS FLECHAS NO SE CUENTAN MUESTREANDO, y por eso no se intenta: vuelan a 3500 cm/s, o sea
0,16 s para cruzar 550 cm, y por MCP no se llega a 1 Hz. Se anotan las que se pillen en
vuelo como pista, pero el numero que vale es la VIDA.

LA VIDA se lee en `StatsManager.Stats[0].BaseValue`. `GetStats` no es invocable desde
Python; la propiedad `Stats` si, y del struct `F_Stat` solo `BaseValue` es legible.

Si PIE no esta corriendo no falla: anota una linea de "sin partida" y se calla.

OJO CON LA CABECERA: este fichero NO puede llevar la linea "# -*- coding: utf-8 -*-".
El MCP hace exec() del codigo como CADENA, y Python prohibe ahi la declaracion de
codificacion ("encoding declaration in Unicode string"). Sale un "Python execution failed"
SIN mensaje y parece cosa del docstring; no lo es. Esto solo afecta al modo : los
ficheros de  la llevan sin problema. Acentos y enes SI valen, que el fuente es
UTF-8 por defecto.
"""
import unreal, json, os, io

DIARIO = os.path.join(unreal.Paths.project_saved_dir(), "DA_RegistroArquero.jsonl")


def anota(d):
    with io.open(DIARIO, "a", encoding="utf-8") as f:
        f.write(json.dumps(d) + "\n")


def stat0(actor):
    for c in actor.get_components_by_class(unreal.ActorComponent):
        if c.get_class().get_name() == "BP_StatsManagerComponent_C":
            try:
                return c.get_editor_property("Stats")[0].get_editor_property("BaseValue")
            except Exception:
                return None
    return None


d = {"t": None, "vida": None, "oleada": None, "estadoArena": None,
     "arqueros": [], "flechasEnVuelo": 0}

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not w:
    anota({"sinPartida": True})
    print("sin partida")
else:
    d["t"] = round(unreal.GameplayStatics.get_time_seconds(w), 2)
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    pawn = pc.get_controlled_pawn() if pc else None
    if pawn:
        d["vida"] = stat0(pawn)
        p = pawn.get_actor_location()
        d["malakh"] = [int(p.x), int(p.y), int(p.z)]

    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        n = a.get_class().get_name()
        if n == "BP_MovingProjectile_Arrow_C":
            d["flechasEnVuelo"] += 1
        elif n == "BP_DA_Arena_C":
            d["estadoArena"] = a.get_editor_property("Estado")
            d["oleada"] = a.get_editor_property("OleadaActual")

    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn):
        if "Arquero" not in p.get_name():
            continue
        pa = p.get_actor_location()
        # El Target del blackboard es LO QUE DECIDE si el arbol combate o patrulla:
        # sin el, ni apunta ni retrocede. Anotarlo es lo que faltaba la vez anterior.
        tiene = None
        ctrl = p.get_controller()
        if ctrl:
            for c in ctrl.get_components_by_class(unreal.ActorComponent):
                if "Blackboard" in c.get_class().get_name():
                    try:
                        tiene = bool(c.get_value_as_object("Target"))
                    except Exception:
                        tiene = None
        dist = None
        if pawn:
            dist = int((pawn.get_actor_location() - pa).length())
        d["arqueros"].append({"id": p.get_name(), "pos": [int(pa.x), int(pa.y)],
                              "d": dist, "vivo": p.call_method("IsAlive", ()),
                              "conBlanco": tiene})
    anota(d)
    arq = "  ".join("%s d=%s blanco=%s" % (a["id"][-2:], a["d"], a["conBlanco"])
                    for a in d["arqueros"] if a["vivo"])
    print("t=%7s vida=%5s oleada=%s flechas=%d  %s"
          % (d["t"], d["vida"], d["oleada"], d["flechasEnVuelo"], arq))
