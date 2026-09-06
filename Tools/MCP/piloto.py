import unreal, builtins, math, heapq, json
# PILOTO: lleva a Malakh por Malkuth con input real, pelea con lo que se cruza,
# interactua en los beats y deja un diario en builtins.PILOTO["diario"].
V = unreal.Vector
CARPETA = r"C:/Users/angel/AppData/Local/Temp/claude/D--Game-Projects-Unreal-DA-DarkAngelsPOC-5-8/c19031d0-24a8-4f7d-912f-382c7e735c62/scratchpad"
BEATS = [
    ("Inicio Jardin", V(-15297, -31618, 156), ""),
    ("Altar (Senda de Setos)", V(-4000, -30900, 20), "interact"),
    ("Espada del Custodio", V(10295, -30075, 20), "interact"),
    ("", V(12380, -8420, -20), ""),
    ("ZONA Mirador", V(12350, -7060, -20), ""),
    ("Decision Sariel", V(12229, -4989, 319), "decision"),
    ("", V(12380, -8420, -20), ""),
    ("", V(13155, -28878, -20), ""),
    ("ZONA El Claro", V(26212, -22920, 100), ""),
    ("Arena Claro", V(26212, -19920, -42), ""),
    ("Puerta del Claro", V(26862, -17793, -42), "interact"),
    ("Arena Heraldo", V(34540, 15065, -38), "interact"),
    ("ZONA Gazebo", V(64000, 14600, -20), ""),
    ("Tableta", V(64000, 16920, 202), "interact"),
    ("ZONA Santuario", V(42850, 47800, 110), ""),
    ("Decision Fuente", V(44598, 48048, 17), "decision"),
    ("ZONA Puente", V(21219, 60661, 20), ""),
    ("Snare 1 del Puente", V(18833, 61530, 657), ""),
    ("Snare 5 del Puente", V(10080, 64716, 2979), ""),
    ("ZONA Anfiteatro", V(-18127, 51184, 144), ""),
    ("ZONA Elevador", V(-18127, 16384, -20), ""),
    ("Arena Elevador", V(-18127, 17984, -70), "interact"),
    ("ZONA Gabriel C1", V(-18086, 12244, -20), ""),
    ("ZONA Gabriel C2", V(-23295, -5412, 130), "gabriel"),
    ("ZONA Gabriel C3", V(-36240, -5594, -20), ""),
    ("ZONA Yesod", V(-36240, 25236, -20), ""),
]
INTERACTUABLES = ("AltarOfContemplation", "GabrielHeraldo", "BP_DA_Interactuable", "BP_DA_Decision", "BP_DA_Paso",
                  "Tablet", "Cofre", "RespuestaGabriel", "LevelDoor", "DoorToMirror", "DroppedWeapon")
ENEMIGO_CLASES = ("BP_DA_Vigilante", "BP_DA_Lancero", "BP_DA_Arquero", "BP_DA_Heraldo", "BP_DA_Inspector",
                  "BP_DA_Corrupto", "BP_DA_GiantBoss", "BP_Gabriel", "BP_DA_Angel", "BP_DA_Elite")


def tecla(pc, nombre):
    k = unreal.Key(nombre) if hasattr(unreal, 'Key') else unreal.InputCoreTypes.Key(nombre)
    pc.input_key(unreal.InputKeyParams(key=k, event=unreal.InputEvent.IE_PRESSED))
    pc.input_key(unreal.InputKeyParams(key=k, event=unreal.InputEvent.IE_RELEASED))


def gw():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def construir_ruta(w):
    piezas = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor):
        c = a.static_mesh_component
        m = c.static_mesh if c else None
        if m and "Path" in m.get_name():
            l = a.get_actor_location()
            piezas.append((l.x, l.y, l.z))
    n = len(piezas)
    ady = [[] for _ in range(n)]
    for i in range(n):
        xi, yi, zi = piezas[i]
        for j in range(i + 1, n):
            xj, yj, zj = piezas[j]
            d = ((xi - xj) ** 2 + (yi - yj) ** 2 + (zi - zj) ** 2) ** 0.5
            if d < 1500:
                ady[i].append((j, d)); ady[j].append((i, d))

    def cerca(p):
        return min(range(n), key=lambda i: (piezas[i][0] - p.x) ** 2 + (piezas[i][1] - p.y) ** 2 + (piezas[i][2] - p.z) ** 2)

    def dijkstra(s, t):
        dist = [1e18] * n; prev = [-1] * n; dist[s] = 0; h = [(0, s)]
        while h:
            d, u = heapq.heappop(h)
            if u == t:
                break
            if d > dist[u]:
                continue
            for v, wgt in ady[u]:
                nd = d + wgt
                if nd < dist[v]:
                    dist[v] = nd; prev[v] = u; heapq.heappush(h, (nd, v))
        if dist[t] >= 1e18:
            return None
        cam = []; u = t
        while u != -1:
            cam.append(u); u = prev[u]
        return cam[::-1]

    ruta = []
    for k in range(len(BEATS)):
        nombre, p, tipo = BEATS[k]
        if k > 0:
            a = BEATS[k - 1][1]
            ia, ib = cerca(a), cerca(p)
            da = ((piezas[ia][0] - a.x) ** 2 + (piezas[ia][1] - a.y) ** 2) ** 0.5
            db = ((piezas[ib][0] - p.x) ** 2 + (piezas[ib][1] - p.y) ** 2) ** 0.5
            cam = dijkstra(ia, ib) if (da < 4000 and db < 4000 and tipo != "saltos") else None
            # cordura: si la carretera da un rodeo absurdo respecto a la linea recta,
            # es que las losas cercanas no son de este tramo. Mejor ir en linea.
            if cam:
                largo = da + db
                for u, v in zip(cam, cam[1:]):
                    largo += ((piezas[u][0] - piezas[v][0]) ** 2 + (piezas[u][1] - piezas[v][1]) ** 2) ** 0.5
                recta = ((p.x - a.x) ** 2 + (p.y - a.y) ** 2) ** 0.5
                if largo > 2.5 * max(recta, 1.0):
                    cam = None
            if cam:
                for idx in cam[1:-1]:
                    x, y, z = piezas[idx]
                    ruta.append(("", V(x, y, z + 60), ""))
        ruta.append((nombre, p, tipo))
    return ruta


def registrar():
    w = gw()
    P = {"ruta": construir_ruta(w), "i": 0, "diario": [], "t0": unreal.GameplayStatics.get_time_seconds(w), "pos_prev": None,
         "t_prog": 0.0, "t_scan": 0.0, "enemigos": [], "t_ataque": 0.0, "fotos": 0, "errores": {},
         "pausa": False, "fin": False, "t_salto": 0.0, "combate_desde": None, "t_int": 0.0, "modo": "andar",
         "tipo_ataque": 0, "cadencia": 1.6, "pendiente": None, "opcion": 1, "rastro": [], "tramposos": 0, "bloqueos": []}
    # Los directores de la Celestial Snare del Puente: se cachean una vez porque
    # el tick los consulta a 5 Hz. Solo los que tienen Activo puesto hieren.
    P["snares"] = []
    for _a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if not _a.get_actor_label().startswith("Snare_"):
            continue
        try:
            if not _a.get_editor_property("Activo"):
                continue
            _luz = _a.get_components_by_class(unreal.PointLightComponent)
            P["snares"].append((_a, _luz[0] if _luz else None, float(_a.get_editor_property("RadioImpacto"))))
        except Exception:
            pass
    P["t_snare"] = 0.0
    P["espera_snare"] = 0.0
    builtins.PILOTO = P

    def nota(txt):
        t = unreal.GameplayStatics.get_time_seconds(gw()) - P["t0"]
        P["diario"].append("%7.1f  %s" % (t, txt))
    P["nota"] = nota
    nota("ruta de %d puntos (%d beats)" % (len(P["ruta"]), len(BEATS)))

    def foto(pc, w, etiqueta):
        P["fotos"] += 1
        unreal.SystemLibrary.execute_console_command(w, "HighResShot 1", pc)
        nota("FOTO %d: %s" % (P["fotos"], etiqueta))

    def error(k, e):
        if k not in P["errores"]:
            P["errores"][k] = str(e)[:160]
            nota("ERROR %s: %s" % (k, str(e)[:120]))

    def interactuar(w, pawn, nombre_p, tipo_p, dest_p):
        hechos = 0
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            cn = a.get_class().get_name()
            if not any(k in cn for k in INTERACTUABLES):
                continue
            if (a.get_actor_location() - dest_p).length() > 900:
                continue
            if a.get_actor_label().endswith("_Vuelta"):
                continue
            try:
                if "BP_DA_Decision" in cn:
                    a.call_method("Elegir", (P["opcion"],))
                    nota("ELEGIR opcion %d en %s" % (P["opcion"], a.get_actor_label()))
                else:
                    a.call_method("Interact", (pawn,))
                    nota("INTERACT %s (%s)" % (a.get_actor_label(), cn))
                hechos += 1
            except Exception as e:
                error("Interact " + cn, e)
        if not hechos:
            nota("sin interactuable en %s" % nombre_p)
        armas = [x.get_actor_label() for x in pawn.get_attached_actors() if "Sword" in x.get_actor_label() or "Spear" in x.get_actor_label() or "Axe" in x.get_actor_label()]
        if armas and not P.get("armado"):
            P["armado"] = True
            nota("ARMADO: %s" % ", ".join(armas))

    def tick(dt):
        try:
            if P["fin"] or P["pausa"]:
                return
            w = gw()
            if w is None:
                return
            pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
            pc = unreal.GameplayStatics.get_player_controller(w, 0)
            if pawn is None or pc is None:
                return
            ahora = unreal.GameplayStatics.get_time_seconds(w)
            pos = pawn.get_actor_location()
            # muerte y reaparicion: el pawn cambia de identidad
            _id = pawn.get_name()
            if P.get("pawn_id") is None:
                P["pawn_id"] = _id
            elif _id != P["pawn_id"]:
                P["pawn_id"] = _id
                P["muertes"] = P.get("muertes", 0) + 1
                nota("MUERTO Y REAPARECIDO (%d) en (%.0f %.0f %.0f)" % (P["muertes"], pos.x, pos.y, pos.z))
            # --- rastro: una miga por segundo, con lo que se esta pisando
            if ahora - P.get("t_miga", -9.0) > 1.0:
                P["t_miga"] = ahora
                hit = unreal.SystemLibrary.line_trace_single(
                    w, V(pos.x, pos.y, pos.z), V(pos.x, pos.y, pos.z - 300),
                    unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn],
                    unreal.DrawDebugTrace.NONE, False)
                t = hit.to_tuple() if hit else None
                suelo = (t[9].get_actor_label() if t[9] else "?") if t and t[0] else "AIRE"
                P["rastro"].append((round(ahora, 1), round(pos.x), round(pos.y), round(pos.z), suelo, P["modo"]))
            # --- enemigos cercanos, cada 0.5 s
            if ahora - P["t_scan"] > 0.5:
                P["t_scan"] = ahora
                cerca = []
                for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
                    if a == pawn:
                        continue
                    cn = a.get_class().get_name()
                    if not cn.startswith(ENEMIGO_CLASES):
                        continue
                    try:
                        if a.get_editor_property('hidden'):
                            continue
                    except Exception:
                        pass
                    d = (a.get_actor_location() - pos).length()
                    if d > 1400 or a.get_actor_label() in P.setdefault("ignorados", set()):
                        continue
                    try:
                        vivo = a.call_method("IsAlive", ())
                    except Exception as e:
                        error("IsAlive " + cn, e); vivo = False
                    if vivo:
                        cerca.append((d, a))
                cerca.sort(key=lambda t: t[0])
                P["enemigos"] = cerca
            if P["enemigos"]:
                d, obj = P["enemigos"][0]
                if P["combate_desde"] is None:
                    P["combate_desde"] = ahora
                    nota("COMBATE con %s (%d cerca) en (%.0f %.0f)" % (obj.get_actor_label(), len(P["enemigos"]), pos.x, pos.y))
                    P["modo"] = "pelear"
                op = obj.get_actor_location()
                dirv = V(op.x - pos.x, op.y - pos.y, 0)
                yaw = math.degrees(math.atan2(dirv.y, dirv.x))
                pc.set_control_rotation(unreal.Rotator(0.0, 0.0, yaw))
                # sacar el arma: sin ToggleCombat CanMeleeAttack nunca es True
                if ahora - P["combate_desde"] > P.get("cap_combate", 90.0):
                    # El piloto no gana peleas: los enemigos bloquean casi todo. Para poder
                    # validar el resto del nivel se remata por script y queda anotado.
                    rematados = []
                    # si estamos dentro de una arena SELLADA, hay que vaciarla entera:
                    # sus oleadas siguen entrando y sus muros no dejan salir.
                    for _ar in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                        if not _ar.get_class().get_name().startswith("BP_DA_Arena"):
                            continue
                        try:
                            if _ar.get_editor_property("Estado") != 1:
                                continue
                            _c = _ar.get_actor_location()
                            _r = _ar.get_editor_property("RadioArena")
                            if abs(pos.x - _c.x) > _r or abs(pos.y - _c.y) > _r:
                                continue
                            for _q in list(_ar.get_editor_property("Enemigos")) + list(_ar.get_editor_property("EnemigosActivos")):
                                if _q and _q.get_controller():
                                    _q.call_method("Kill", ())
                                    rematados.append(_q.get_actor_label())
                            nota("ARENA VACIADA: %s (oleada %s/%s)" % (_ar.get_actor_label(), _ar.get_editor_property("OleadaActual"), _ar.get_editor_property("MaxOleada")))
                        except Exception as e:
                            error("vaciar arena", e)
                    for _d, _e in P["enemigos"]:
                        try:
                            if _e.get_controller():
                                _e.call_method("Kill", ())
                                rematados.append(_e.get_actor_label())
                        except Exception as e:
                            error("Kill", e)
                        P.setdefault("ignorados", set()).add(_e.get_actor_label())
                    P["asistidos"] = P.get("asistidos", 0) + len(rematados)
                    nota("REMATE ASISTIDO tras %.0f s: %s" % (P.get("cap_combate", 90.0), ", ".join(rematados) or "nadie"))
                    P["enemigos"] = []
                    P["t_scan"] = ahora
                    return
                if ahora - max(P.get("t_golpe", 0.0), P["combate_desde"]) > 30.0:
                    P.setdefault("ignorados", set()).add(obj.get_actor_label())
                    nota("INALCANZABLE %s (30 s sin poder golpearlo, d=%.0f, dz=%.0f): lo ignoro" % (obj.get_actor_label(), d, op.z - pos.z))
                    P["enemigos"] = [e for e in P["enemigos"] if e[1] != obj]
                    P["t_scan"] = ahora
                    return
                sin_golpe = ahora - P.get("t_golpe", P["combate_desde"]) > 8.0
                if P.get("t_toggle", -10.0) < P["combate_desde"] or (sin_golpe and ahora - P.get("t_toggle", -10.0) > 8.0):
                    try:
                        if not pawn.call_method("CanMeleeAttack", ()):
                            P["t_toggle"] = ahora
                            pawn.call_method("ToggleCombat", ())
                            nota("ToggleCombat (sacar arma)")
                    except Exception as e:
                        error("ToggleCombat", e)
                if d > 100:
                    pawn.add_movement_input(dirv.normal(), 1.0, False)
                else:
                    pawn.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
                    if ahora - P["t_ataque"] > P.get("cadencia", 1.6):
                        P["t_ataque"] = ahora
                        try:
                            if pawn.call_method("CanMeleeAttack", ()):
                                pawn.call_method("DbgAtaqueLigero", ())
                                P["golpes"] = P.get("golpes", 0) + 1
                                P["t_golpe"] = ahora
                        except Exception as e:
                            error("MeleeAttack", e)
                return
            if P["combate_desde"] is not None:
                nota("combate terminado, %.0f s (golpes acumulados %d)" % (ahora - P["combate_desde"], P.get("golpes", 0)))
                P["combate_desde"] = None
                P["modo"] = "andar"
                P["t_prog"] = ahora; P["pos_prev"] = None
            # --- interaccion pendiente (un segundo despues de llegar, quieto)
            if P["pendiente"]:
                if ahora < P["t_int"]:
                    return
                nombre_p, tipo_p, dest_p = P["pendiente"]
                P["pendiente"] = None
                interactuar(w, pawn, nombre_p, tipo_p, dest_p)
                P["t_prog"] = ahora
                return
            # --- andar hacia el punto
            if P["i"] >= len(P["ruta"]):
                if not P["fin"]:
                    nota("FIN DE RUTA")
                    P["fin"] = True
                return
            nombre, dest, tipo = P["ruta"][P["i"]]
            dirv = V(dest.x - pos.x, dest.y - pos.y, 0)
            dist = dirv.length()
            if dist < 260 or (nombre and dist < 420 and abs(dest.z - pos.z) < 600):
                if nombre:
                    nota("LLEGA a %s (z=%.0f)" % (nombre, pos.z))
                    foto(pc, w, nombre)
                    if tipo in ("interact", "decision", "gabriel"):
                        P["t_int"] = ahora + 1.0
                        P["pendiente"] = (nombre, tipo, dest)
                P["i"] += 1
                P["t_prog"] = ahora
                P["pos_prev"] = None
                return
            yaw = math.degrees(math.atan2(dirv.y, dirv.x))
            pc.set_control_rotation(unreal.Rotator(0.0, -8.0, yaw))
            # --- progreso: la distancia al punto tiene que bajar; si no, rodear (izq/der), saltar, y al final teleport
            if P["pos_prev"] is None or dist < P.get("dist_mejor", 1e9) - 60:
                P["pos_prev"] = pos; P["t_prog"] = ahora; P["dist_mejor"] = dist
            atasco = ahora - P["t_prog"]
            avance = dirv.normal()
            if atasco > 4.0 and pc.is_move_input_ignored():
                pc.reset_ignore_move_input(); pc.reset_ignore_look_input()
                nota("movimiento ignorado tras interaccion: liberado")
                P["t_prog"] = ahora
            if atasco > 1.5:
                # Rodear de verdad: abanico de trazas de capsula y me quedo con el primer
                # rumbo libre. Un tronco de 60 uu paraba al piloto para siempre porque el
                # rodeo viejo (0,4 de frente + perpendicular) seguia empujando contra el.
                lado = 1.0 if int(atasco / 3.0) % 2 == 0 else -1.0
                if ahora > P.get("t_rodeo", 0.0):
                    base = math.degrees(math.atan2(avance.y, avance.x))
                    libre = None
                    for off in (0, 35, -35, 70, -70, 88, -88):
                        rad = math.radians(base + off * lado)
                        d = V(math.cos(rad), math.sin(rad), 0)
                        h = unreal.SystemLibrary.capsule_trace_single(
                            w, V(pos.x, pos.y, pos.z + 10), V(pos.x + d.x * 350, pos.y + d.y * 350, pos.z + 10),
                            45.0, 80.0, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn],
                            unreal.DrawDebugTrace.NONE, False)
                        t = h.to_tuple() if h else None
                        if not (t and t[0]):
                            libre = d
                            break
                    P["rodeo"] = libre
                    P["t_rodeo"] = ahora + 0.5
                salida = P.get("rodeo")
                if salida is not None:
                    avance = salida
                else:
                    perp = V(-avance.y * lado, avance.x * lado, 0)
                    avance = (avance * 0.4 + perp).normal()
                if atasco > 2.0 and ahora - P["t_salto"] > 1.5:
                    P["t_salto"] = ahora
                    try:
                        pawn.call_method("CustomJump", ())
                    except Exception as e:
                        error("CustomJump", e)
                    if int(atasco) % 4 == 2:
                        nota("atasco en (%.0f %.0f %.0f) hacia %s: rodeo y salto" % (pos.x, pos.y, pos.z, nombre or "punto %d" % P["i"]))
            # --- Celestial Snare: el aviso dura 1,5 s y el rayo solo hiere dentro de
            # RadioImpacto. El punto se elige POR DELANTE del jugador, asi que la
            # jugada buena no es esquivar de lado en un puente estrecho: es frenar
            # y dejar que caiga delante. La luz Aviso a intensidad > 0 es el aviso.
            if P["snares"] and ahora > P.get("t_snare", 0.0):
                P["t_snare"] = ahora + 0.2
                delante = V(pos.x + avance.x * 420.0, pos.y + avance.y * 420.0, pos.z)
                cerca = None
                for _sn, _luz, _rad in P["snares"]:
                    if _luz is None or _luz.intensity <= 0.0:
                        continue
                    _pi = _sn.get_editor_property("PuntoImpacto")
                    if not (_pi.x or _pi.y):
                        continue
                    _d = min(math.hypot(_pi.x - pos.x, _pi.y - pos.y),
                             math.hypot(_pi.x - delante.x, _pi.y - delante.y))
                    if _d < _rad + 150.0:
                        cerca = (_sn.get_actor_label(), _d)
                        break
                P["freno_snare"] = cerca
            frenado = P.get("freno_snare")
            if frenado is not None:
                # tope de 3 s: con cadencia 1,4 y aviso de 1,5 el puente casi nunca
                # esta limpio, y quedarse parado para siempre no es cruzar.
                if P["espera_snare"] == 0.0:
                    P["espera_snare"] = ahora
                if ahora - P["espera_snare"] < 3.0:
                    P["t_prog"] = ahora          # esperar no es atascarse
                    if int((ahora - P["espera_snare"]) * 2) == 0:
                        nota("SNARE: freno por %s a %.0f uu" % frenado)
                    return
            else:
                P["espera_snare"] = 0.0
            pawn.add_movement_input(avance, 1.0, False)
            if ahora - P["t_prog"] > P.get("paciencia", 9.0):
                if P.get("sin_teleport"):
                    P["bloqueos"] = P.get("bloqueos", [])
                    P["bloqueos"].append((round(ahora, 1), round(pos.x), round(pos.y), round(pos.z), nombre or "punto %d" % P["i"], round(dest.x), round(dest.y), round(dist)))
                    nota("BLOQUEADO en (%.0f %.0f %.0f) hacia %s, a %.0f uu: lo salto de la ruta" % (pos.x, pos.y, pos.z, nombre or "punto %d" % P["i"], dist))
                    P["i"] += 1
                    P["t_prog"] = ahora; P["pos_prev"] = None
                    return
                P["tramposos"] = P.get("tramposos", 0) + 1
                nota("TELEPORT (TRAMPA %d) a %s (%.0f %.0f %.0f) tras %.0f s atascado" % (P["tramposos"], nombre or "punto %d" % P["i"], dest.x, dest.y, dest.z, ahora - P["t_prog"]))
                pawn.set_actor_location(V(dest.x, dest.y, dest.z + 100), False, True)
                P["t_prog"] = ahora; P["pos_prev"] = None
        except Exception as e:
            error("tick", e)
    P["handle"] = unreal.register_slate_post_tick_callback(tick)
    return P


def parar():
    P = getattr(builtins, "PILOTO", None)
    if P and P.get("handle"):
        unreal.unregister_slate_post_tick_callback(P["handle"])
        P["handle"] = None
        P["fin"] = True


# Tramos sueltos: (beats, preparacion). La preparacion recibe el GameState.
def quitar(prefijo):
    # los encuentros que en una partida real ya estarian muertos al llegar aqui
    w0 = gw()
    n = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(w0, unreal.Character):
        if a.get_actor_label().startswith(prefijo):
            a.destroy_actor(); n += 1
    print("quitados", n, "de", prefijo)


def prep_sariel(gs):
    gs.call_method("AnotarMarca", (1, "ORDEN"))
    quitar("Enc_T1_")


def prep_gazebo(gs):
    gs.call_method("MarcarFlag", ("GAZEBO_TABLETA_LEIDA",))
    quitar("Enc_T4_")


TRAMOS = {
    "sariel_claro": ([
        ("Decision Sariel", V(12229, -4989, 319), ""),
        ("", V(12380, -8420, -20), ""), ("", V(12300, -17200, -20), ""), ("", V(11900, -18800, 70), ""),
        ("", V(11400, -20300, -20), ""), ("", V(11400, -22300, 416), ""), ("", V(11200, -26100, 261), ""),
        ("", V(11200, -28100, -20), ""), ("", V(13155, -28878, -20), ""),
        ("ZONA El Claro", V(26212, -22920, 100), ""),
    ], prep_sariel),
    "gazebo_santuario": ([
        ("Tableta", V(64000, 16920, 202), ""),
        ("", V(64000, 16100, 202), ""),      # la plataforma esta amurallada:
        ("", V(64000, 15600, 76), ""),       # la unica salida es la escalera del sur
        ("", V(64000, 15100, -40), ""),
        ("ZONA Gazebo", V(64000, 14600, -20), ""),
        ("ZONA Santuario", V(42850, 47800, 110), ""),
    ], prep_gazebo),
    # el Umbral (donde esta la espada) hasta el Mirador, por el corredor oeste
    "umbral_mirador": ([
        ("Umbral (espada)", V(10186, -30200, 20), ""),
        ("", V(8000, -29000, -40), ""),
        ("", V(7000, -26000, -40), ""),
        ("", V(7000, -20000, -40), ""),
        ("", V(7000, -14000, -40), ""),
        ("", V(8500, -10000, -40), ""),
        ("", V(11000, -8800, -40), ""),
        ("ZONA Mirador", V(12350, -7060, -20), ""),
        ("Decision Sariel", V(12229, -4989, 319), ""),
    ], None),
    # la misma subida pero en linea recta al norte, que es lo que intentaba el piloto
    "umbral_mirador_recto": ([
        ("Umbral (espada)", V(10186, -30200, 20), ""),
        ("", V(11000, -25000, -40), ""),
        ("", V(11400, -20000, -40), ""),
        ("ZONA Mirador", V(12350, -7060, -20), ""),
    ], None),
    "heraldo_gazebo": ([
        ("Arena Heraldo", V(34540, 15065, -38), ""),
        ("ZONA Gazebo", V(64000, 14600, -20), ""),
        ("Tableta", V(64000, 16920, 202), "interact"),
    ], None),
    "puente_anfiteatro": ([
        ("ZONA Puente", V(21219, 60661, 20), ""),
        ("Snare 1 del Puente", V(18833, 61530, 657), ""),
        ("Snare 5 del Puente", V(10080, 64716, 2979), ""),
        ("ZONA Anfiteatro", V(-18127, 51184, 144), ""),
    ], None),
    "anfiteatro_elevador": ([
        ("ZONA Anfiteatro", V(-18127, 51184, 144), ""),
        ("ZONA Elevador", V(-18127, 16384, -20), ""),
        ("Arena Elevador", V(-18127, 17984, -70), "interact"),
    ], None),
    "elevador_gc1": ([
        ("Arena Elevador", V(-18127, 17984, -70), ""),
        ("ZONA Gabriel C1", V(-18086, 12244, -20), ""),
    ], None),
    "gc2_gc3": ([
        ("ZONA Gabriel C2", V(-23295, -5412, 130), ""),
        ("ZONA Gabriel C3", V(-36240, -5594, -20), ""),
    ], None),
    "gc3_yesod": ([
        ("ZONA Gabriel C3", V(-36240, -5594, -20), ""),
        ("ZONA Yesod", V(-36240, 25236, -20), ""),
    ], None),
    "fuente_puente": ([
        ("Decision Fuente", V(44598, 48048, 17), ""),
        ("ZONA Puente", V(21219, 60661, 20), ""),
    ], None),
    "gc1_gc2": ([
        ("ZONA Gabriel C1", V(-18086, 12244, -20), ""),
        ("ZONA Gabriel C2", V(-23295, -5412, 130), ""),
    ], None),
}

a = open(CARPETA + "/accion.txt").read().strip().split()
if a[0] == "tramo":
    parar()
    beats, prep = TRAMOS[a[1]]
    BEATS[:] = beats
    w0 = gw()
    if prep:
        prep(unreal.GameplayStatics.get_game_state(w0))
    p0 = unreal.GameplayStatics.get_player_pawn(w0, 0)
    ini = BEATS[0][1]
    # soltar SOBRE el suelo real: la posicion de un Character es el centro de su
    # capsula, asi que dejarlo a la cota del beat lo entierra y no se mueve nunca.
    _h = unreal.SystemLibrary.line_trace_single(w0, V(ini.x, ini.y, ini.z + 2000), V(ini.x, ini.y, ini.z - 500),
                                                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [p0],
                                                unreal.DrawDebugTrace.NONE, False)
    _t = _h.to_tuple() if _h else None
    _suelo = _t[4].z if _t and _t[0] else ini.z
    p0.set_actor_location(V(ini.x, ini.y, _suelo + 130.0), False, True)
    P = registrar()
    P["cap_combate"] = 40.0
    print("tramo", a[1], "ruta de", len(P["ruta"]), "puntos; pawn en", p0.get_actor_location())
elif a[0] == "arrancar":
    parar()
    w0 = gw()
    p0 = unreal.GameplayStatics.get_player_pawn(w0, 0)
    ini = BEATS[0][1]
    p0.set_actor_location(V(ini.x, ini.y, ini.z + 60), False, True)
    P = registrar()
    print("piloto registrado; ruta de", len(P["ruta"]), "puntos; pawn en", p0.get_actor_location())
elif a[0] == "recargar":
    viejo = builtins.PILOTO
    parar()
    P = registrar()
    for k in ("diario", "i", "t0", "fotos", "golpes", "opcion"):
        if k in viejo:
            P[k] = viejo[k]
    P["nota"]("piloto recargado en el punto %d" % P["i"])
    print("recargado; i=%d diario=%d" % (P["i"], len(P["diario"])))
elif a[0] == "estado":
    P = builtins.PILOTO
    w = gw()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
    pos = pawn.get_actor_location() if pawn else None
    print("i=%d/%d modo=%s pos=%s fin=%s errores=%d" % (P["i"], len(P["ruta"]), P["modo"], "(%.0f %.0f %.0f)" % (pos.x, pos.y, pos.z) if pos else "?", P["fin"], len(P["errores"])))
    desde = int(a[1]) if len(a) > 1 else 0
    for l in P["diario"][desde:]:
        print(l)
    print("diario_len=%d" % len(P["diario"]))
elif a[0] == "parar":
    parar(); print("piloto parado")
elif a[0] == "pausa":
    builtins.PILOTO["pausa"] = a[1] == "1"; print("pausa", a[1])
elif a[0] == "saltar":
    builtins.PILOTO["i"] = int(a[1]); builtins.PILOTO["pos_prev"] = None; builtins.PILOTO["pendiente"] = None; print("i =", a[1])
elif a[0] == "opcion":
    builtins.PILOTO["opcion"] = int(a[1]); print("opcion", a[1])
elif a[0] == "guardar":
    P = builtins.PILOTO
    json.dump(P["diario"], open(CARPETA + "/piloto_diario.json", "w"), ensure_ascii=False, indent=0)
    json.dump({"rastro": P.get("rastro", []), "tramposos": P.get("tramposos", 0), "bloqueos": P.get("bloqueos", [])},
              open(CARPETA + "/piloto_rastro.json", "w"), ensure_ascii=False)
    print("guardado: diario %d, migas %d, teleports %d, bloqueos %d" % (
        len(P["diario"]), len(P.get("rastro", [])), P.get("tramposos", 0), len(P.get("bloqueos", []))))
