"""Toma UNA muestra de la partida y la anota. Pensado para llamarse en bucle mientras
alguien JUEGA.

    node ue.mjs py registro_arquero.py

POR QUE EXISTE. El 26/08 se probo el umbral nuevo del Arquero (450 en vez de 300) moviendo
a Malakh por Python, y NO SE PUDO MEDIR SI DISPARA: el teleport le tira el blanco -Target
vacio en el blackboard- y toda la rama de apuntar cuelga de "Is Target Set?". Asi que el
Arquero patrullaba en vez de combatir, y salieron tres tandas seguidas con 100 de vida.
La unica forma de contestarlo es que alguien lo juegue y que esto lo mida por el.

DOS RELOJES, Y CADA UNO MIDE LO SUYO. Esta es la idea entera:

  - 50 Hz, DENTRO del juego: `BP_DA_MedidorDano`, ya colocado en el nivel, cuenta golpes y
    daño por CAIDAS DE VIDA con un temporizador de 0,02 s. A esa frecuencia no se escapa
    ningun impacto. Esta pasada lo ARRANCA sola en cuanto hay partida.
  - ~1 Hz, desde fuera: posiciones, distancias, oleada, y de CADA enemigo si esta vivo, si
    tiene blanco y si su ARBOL CORRE. Eso cambia despacio y no necesita mas.

EL CAMPO QUE DISTINGUE UN DORMIDO DE UN COLGADO es `ia` (corre / pausada / PARADA), y sin
el se pierden tardes enteras. El 26/08 los dos arqueros pasaron 63 s vivos, con blanco y
quietos despues de que a Angel lo mataran, y parecia un cuelgue: era el escalonado
haciendo su trabajo. `AplicarOleadas` para con StopLogic a todo el que sea de una oleada
futura y solo `EntrarOleada` lo reanuda; al morir el jugador la arena vuelve a la oleada 1,
asi que los arqueros —que son de la 3— se duermen otra vez. Tener blanco NO significa
combatir: la percepcion y el arbol son cosas distintas.

Lo que NO se puede hacer es contar flechas muestreando desde fuera: vuelan a 3500 cm/s, o
sea 0,16 s para cruzar 550 cm, y por MCP no se llega a 1 Hz. Por eso el numero que vale es
el del medidor.

COMO SE ATRIBUYE EL DAÑO, que es la gracia: la receta "Romper la linea" entra DE UNO EN
UNO. La oleada 3 es el Arquero SOLO, asi que todo golpe contado mientras `oleada == 3` es
una flecha. No hace falta identificar al autor: lo hace el guion del encuentro.

EL CONTADOR DE FLECHAS VA DENTRO, Y ESTO CORRIGE LO QUE ESTE FICHERO PROMETIA. Durante
una temporada aqui ponia que `maxIndiceFlecha` —el mayor N de
`BP_MovingProjectile_Arrow_C_<N>`— servia de COTA INFERIOR de los disparos. NO SIRVE: solo
mira las flechas VIVAS, asi que en cuanto ninguna esta en vuelo vuelve a -1 y el maximo se
pierde. Medido el 26/08 en dos partidas jugadas (113 s): 2 flechas pilladas en vuelo, y de
casualidad.

No era afinable, era imposible por construccion: la flecha cruza la arena en 0,16 s y por
MCP no se llega a 1 Hz. Asi que el conteo se hizo DENTRO, donde ya vive el medidor: a 50 Hz
una flecha dura ~8 muestras y no se escapa. `BP_DA_MedidorDano` cuenta ahora los FLANCOS de
subida del numero de flechas vivas y guarda `Flechas` y `TiemposFlecha` (segundos desde
`TInicio`), que es lo que da la cadencia. `flechasEnVuelo` y `maxIndiceFlecha` se siguen
anotando, pero SOLO como testigo: el numero bueno es el del medidor.

Lo unico que el flanco no distingue es una flecha que nace en el MISMO tick de 0,02 s en
que otra muere. Con dos arqueros y una cadencia de segundos eso es despreciable.

LA VIDA se lee en `StatsManager.Stats[0].BaseValue`. `GetStats` no es invocable desde
Python; la propiedad `Stats` si, y del struct `F_Stat` solo `BaseValue` es legible.

Si PIE no esta corriendo no falla: anota "sin partida" y se calla.

OJO CON LA CABECERA: este fichero NO puede llevar la linea "# -*- coding: utf-8 -*-". El
MCP hace exec() del codigo como CADENA, y Python prohibe ahi la declaracion de
codificacion. Sale un "Python execution failed" SIN mensaje y parece cosa del docstring; no
lo es. Solo afecta al modo `py`: los de `script` la llevan sin problema. Acentos y enes
valen igual, que el fuente es UTF-8 por defecto.
"""
import unreal, json, os, io, re

DIARIO = os.path.join(unreal.Paths.project_saved_dir(), "DA_RegistroArquero.jsonl")
RX_FLECHA = re.compile(r"BP_MovingProjectile_Arrow_C_(\d+)")


def anota(d):
    with io.open(DIARIO, "a", encoding="utf-8") as f:
        f.write(json.dumps(d) + "\n")


def comp(actor, nombre):
    for c in actor.get_components_by_class(unreal.ActorComponent):
        if c.get_class().get_name() == nombre:
            return c
    return None


def vida(actor):
    c = comp(actor, "BP_StatsManagerComponent_C")
    if not c:
        return None
    try:
        return round(c.get_editor_property("Stats")[0].get_editor_property("BaseValue"), 1)
    except Exception:
        return None


d = {}
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not w:
    anota({"sinPartida": True})
    print("sin partida")
else:
    d["t"] = round(unreal.GameplayStatics.get_time_seconds(w), 2)
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    pawn = pc.get_controlled_pawn() if pc else None
    if pawn:
        d["vida"] = vida(pawn)
        p = pawn.get_actor_location()
        d["malakh"] = [int(p.x), int(p.y), int(p.z)]

    medidor = None
    flechas = 0
    maxN = -1
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        n = a.get_class().get_name()
        if n == "BP_MovingProjectile_Arrow_C":
            flechas += 1
            m = RX_FLECHA.match(a.get_name())
            if m:
                maxN = max(maxN, int(m.group(1)))
        elif n == "BP_DA_Arena_C":
            d["estadoArena"] = a.get_editor_property("Estado")
            d["oleada"] = a.get_editor_property("OleadaActual")
        elif n == "BP_DA_MedidorDano_C":
            medidor = a
    d["flechasEnVuelo"] = flechas
    d["maxIndiceFlecha"] = maxN

    # EL MEDIDOR SE ARRANCA SOLO. `Arrancar` pone los contadores a cero, asi que se llama
    # UNA vez por partida: mientras `Midiendo` sea true no se vuelve a tocar.
    if medidor is not None and pawn is not None:
        try:
            if not medidor.get_editor_property("Midiendo"):
                medidor.call_method("Arrancar", ())
                d["medidorArrancado"] = True
            d["golpes"] = medidor.get_editor_property("Golpes")
            d["danoTotal"] = round(medidor.get_editor_property("DanoTotal"), 1)
            # Lo que de verdad contesta la cadencia. Ver la cabecera.
            d["flechas"] = medidor.get_editor_property("Flechas")
            d["tiemposFlecha"] = [round(float(x), 2)
                                  for x in medidor.get_editor_property("TiemposFlecha")]
        except Exception as e:
            d["medidorError"] = str(e)[:120]
    else:
        d["medidorError"] = "no hay medidor en el nivel"

    d["arqueros"] = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn):
        if "Arquero" not in p.get_name():
            continue
        pa = p.get_actor_location()
        # El Target del blackboard es LO QUE DECIDE si el arbol combate o patrulla: sin el,
        # ni apunta ni retrocede. Anotarlo es lo que faltaba la vez anterior.
        tiene = None
        ctrl = p.get_controller()
        if ctrl:
            for c in ctrl.get_components_by_class(unreal.ActorComponent):
                if "Blackboard" in c.get_class().get_name():
                    try:
                        tiene = bool(c.get_value_as_object("Target"))
                    except Exception:
                        tiene = None
        d["arqueros"].append({
            "id": p.get_name()[-2:],
            "pos": [int(pa.x), int(pa.y)],
            "d": int((pawn.get_actor_location() - pa).length()) if pawn else None,
            "vivo": p.call_method("IsAlive", ()),
            "conBlanco": tiene,
            "vida": vida(p),
        })
    # Y AHORA TODOS LOS ENEMIGOS, NO SOLO LOS ARQUEROS. Lo que decide si uno esta
    # "trabado" NO es que tenga blanco: es si su ARBOL CORRE. `AplicarOleadas` de la arena
    # para con StopLogic a todo el que sea de una oleada futura, y solo `EntrarOleada` lo
    # reanuda con RestartLogic. Un enemigo vivo, con blanco y quieto suele ser uno dormido
    # esperando su turno — no un fallo. El 26/08 se vieron los dos arqueros asi durante 63 s
    # tras revivir, y sin este campo no habia forma de distinguirlo de un cuelgue.
    #
    # `tags` lleva el numero de oleada: es como la arena marca a quien toca cuando.
    # BLINDADO A PROPOSITO: si un solo enemigo peta, se pierde LA MUESTRA ENTERA y con ella
    # la sesion jugada, que no se puede repetir a voluntad. Cada uno va en su try y el que
    # falle se anota como {"error": ...} en vez de tumbar el registro.
    d["enemigos"] = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn):
      try:
        if pawn is not None and p.get_name() == pawn.get_name():
            continue
        pa = p.get_actor_location()
        tiene = None
        ia = None
        ctrl = p.get_controller()
        if ctrl:
            for c in ctrl.get_components_by_class(unreal.ActorComponent):
                if "Blackboard" in c.get_class().get_name():
                    try:
                        tiene = bool(c.get_value_as_object("Target"))
                    except Exception:
                        tiene = None
            try:
                brain = ctrl.get_editor_property("BrainComponent")
                if brain:
                    if brain.is_running():
                        ia = "corre"
                    elif brain.is_paused():
                        ia = "pausada"
                    else:
                        ia = "PARADA"
            except Exception:
                ia = None
        try:
            vivo = p.call_method("IsAlive", ())
        except Exception:
            vivo = None
        d["enemigos"].append({
            "id": p.get_name(),
            "clase": p.get_class().get_name(),
            "pos": [int(pa.x), int(pa.y)],
            "d": int((pawn.get_actor_location() - pa).length()) if pawn else None,
            "vivo": vivo,
            "conBlanco": tiene,
            "ia": ia,
            "vida": vida(p),
            "tags": [str(t) for t in p.tags],
        })
      except Exception as e:
        d["enemigos"].append({"error": str(e)[:120]})

    anota(d)
    arq = "  ".join("%s d=%s blanco=%s" % (a["id"], a["d"], a["conBlanco"])
                    for a in d["arqueros"] if a["vivo"])
    vivos = [e for e in d["enemigos"] if e["vivo"]]
    corren = len([e for e in vivos if e["ia"] == "corre"])
    print("t=%7s vida=%5s ol=%s golpes=%s dano=%s flechas=%s  ia %s/%s  %s"
          % (d.get("t"), d.get("vida"), d.get("oleada"), d.get("golpes"),
             d.get("danoTotal"), d.get("flechas"), corren, len(vivos), arq))
