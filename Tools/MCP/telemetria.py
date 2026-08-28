"""Grabador de telemetria de partida — Dark Angels / Malkuth.

Se engancha al tick de Slate (que sigue corriendo durante PIE) y vuelca un CSV
por sesion en Saved/Telemetria/. No hay que tocar nada mientras se juega: detecta
solo el arranque y el fin de PIE.

    import telemetria; telemetria.arrancar()      # dejarlo puesto y jugar
    telemetria.parar()                            # al terminar

Por que estas fuentes y no otras:
  - Los GameplayTag NO se pueden construir desde Python, asi que GetStatValue()
    del StatsManager es inalcanzable. Pero su propiedad `Stats` es un array
    legible y export_text() cuesta 0,010 ms: de ahi salen vida, aguante y
    sobre todo Stat.ReceivedHitCount, que es la mejor senal de combate que hay.
  - La lista de enemigos se refresca cada 2 s, no cada muestra: con 6.681
    actores en el Master recorrerlos a 10 Hz costaria la partida.
"""
import os, re, time
import unreal

HZ = 10.0
RADIO_CERCA = 2000.0          # uu; a esta distancia se considera que hay combate
REFRESCO_ENEMIGOS = 2.0       # s entre reconstrucciones de la lista
VOLCADO = 2.0                 # s entre escrituras a disco

I_VIDA, I_AGUANTE, I_GOLPES = 0, 2, 12   # indices en el array Stats

_handle = None
_estado = {}


def _num(struct):
    m = re.findall(r"=([0-9.]+)", struct.export_text())
    return float(m[0]) if m else 0.0


def _abrir(gw):
    carpeta = os.path.join(unreal.Paths.project_saved_dir(), "Telemetria")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "sesion_%s.csv" % time.strftime("%Y%m%d_%H%M%S"))
    f = open(ruta, "w", encoding="utf-8")
    f.write("reloj;t;x;y;z;vel;vida;aguante;golpes;cerca;vivos;objetivo\n")
    unreal.log("TELEMETRIA -> " + ruta)
    return f, ruta


def _enemigos(gw, pawn):
    fuera = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Character):
        if a == pawn:
            continue
        try:
            if a.get_editor_property("hidden"):
                continue
        except Exception:
            pass
        if a.get_instigator_controller() is None:
            continue          # sin controlador = figurante, no combatiente
        fuera.append(a)
    return fuera


def _tick(delta):
    e = _estado
    try:
        gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if gw is None:
            if e.get("f"):
                e["f"].close(); e["f"] = None
                unreal.log("TELEMETRIA cerrada: %d muestras" % e.get("n", 0))
            return
        pc = unreal.GameplayStatics.get_player_controller(gw, 0)
        pawn = pc.get_controlled_pawn() if pc else None
        if pawn is None:
            return

        if not e.get("f"):
            e["f"], e["ruta"] = _abrir(gw)
            e.update(n=0, acum=0.0, tref=0.0, tvol=0.0, enem=[], sm=None, buf=[])

        e["acum"] += delta
        if e["acum"] < 1.0 / HZ:
            return
        e["acum"] = 0.0

        t = unreal.GameplayStatics.get_time_seconds(gw)

        if e["sm"] is None or t - e["tref"] > REFRESCO_ENEMIGOS:
            e["tref"] = t
            e["enem"] = _enemigos(gw, pawn)
            e["sm"] = next((c for c in pawn.get_components_by_class(unreal.ActorComponent)
                            if c.get_class().get_name() == "BP_StatsManagerComponent_C"), None)

        p = pawn.get_actor_location()
        v = pawn.get_velocity()
        vel = (v.x * v.x + v.y * v.y + v.z * v.z) ** 0.5

        vida = aguante = golpes = -1.0
        if e["sm"]:
            st = e["sm"].get_editor_property("Stats")
            if len(st) > I_GOLPES:
                vida, aguante, golpes = _num(st[I_VIDA]), _num(st[I_AGUANTE]), _num(st[I_GOLPES])

        cerca = 0
        for a in e["enem"]:
            q = a.get_actor_location()
            if (q - p).length() <= RADIO_CERCA:
                cerca += 1

        obj = ""
        hud = pc.get_hud()
        if hud:
            try:
                obj = str(hud.get_editor_property("ObjectiveText")).replace(";", ",")
            except Exception:
                pass

        e["buf"].append("%.3f;%.2f;%.0f;%.0f;%.0f;%.0f;%.1f;%.1f;%.0f;%d;%d;%s\n"
                        % (time.time(), t, p.x, p.y, p.z, vel, vida, aguante,
                           golpes, cerca, len(e["enem"]), obj))
        e["n"] += 1

        if t - e["tvol"] > VOLCADO:
            e["tvol"] = t
            e["f"].write("".join(e["buf"])); e["buf"] = []; e["f"].flush()
    except Exception as ex:
        if e.get("n", 0) % 500 == 0:
            unreal.log_warning("TELEMETRIA: %s" % str(ex)[:120])


def arrancar():
    global _handle
    if _handle is not None:
        unreal.log("TELEMETRIA ya estaba puesta"); return
    _estado.clear()
    _handle = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("TELEMETRIA puesta a %g Hz. Juega; se graba sola." % HZ)


def parar():
    global _handle
    if _handle is None:
        return
    unreal.unregister_slate_post_tick_callback(_handle)
    _handle = None
    if _estado.get("f"):
        _estado["f"].write("".join(_estado.get("buf", [])))
        _estado["f"].close(); _estado["f"] = None
    unreal.log("TELEMETRIA parada: %d muestras en %s"
               % (_estado.get("n", 0), _estado.get("ruta", "?")))
