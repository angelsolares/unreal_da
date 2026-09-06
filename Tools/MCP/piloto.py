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
    # OJO con este tramo: las Elevador_Terraza son MOVABLE y OSCILAN en X (+-1200 uu,
    # periodo ~6,7 s, desfasadas entre si). Cualquier punto de paso fijo aqui es
    # mentira, y el hueco entre dos losas va de ~250 uu cuando se alinean a ~2400
    # cuando estan en oposicion. Hay que cronometrarlas como la Snare y los picos.
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
    # Las filas de picos del Puente: suben y bajan con periodo 3 s (senoidal, 95 uu de
    # recorrido) y fases escalonadas. Se cachea un pico de cada fila para leer su altura.
    P["picos"] = []
    _sm = list(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor))
    for _a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if _a.get_class().get_name() != "BP_DA_PicoFila_C":
            continue
        _i = _a.get_actor_label().split("_")[-1]
        _reps = [x for x in _sm if x.get_actor_label().startswith("Pico_%s_" % _i)]
        if not _reps:
            continue
        try:
            _rad = float(_a.get_editor_property("RadioDano"))
        except Exception:
            _rad = 90.0
        P["picos"].append((_a, _reps[0], _rad, _a.get_actor_location().z))
    # Las losas oscilantes del Elevador: MOVABLE, +-1200 uu en X y ~6,7 s de periodo,
    # desfasadas. Se cachean de norte a sur; de dos apiladas en el mismo sitio se queda
    # la de arriba, que es la que se pisa.
    P["losas"] = []
    _ts = []
    for _a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if not _a.get_actor_label().startswith("Elevador_Terraza"):
            continue
        _l = _a.get_actor_location(); _b = _a.get_actor_bounds(False)
        _ts.append([_l.y, _l.z, _a, _b[1].x, _b[1].y])
    _ts.sort(key=lambda t: -t[0])
    for _t in _ts:
        if P["losas"] and abs(_t[0] - P["losas"][-1][0]) < 400:
            if _t[1] > P["losas"][-1][1]:
                P["losas"][-1] = _t
            continue
        P["losas"].append(_t)
    P["t_snare"] = 0.0
    P["espera_snare"] = 0.0
    # Calidad al minimo mientras mide el piloto. NO es cosmetico: a calidad plena este
    # nivel corre a 11,4 fps en PIE (medido con get_world_delta_seconds), y a esa cadencia
    # se distorsiona todo lo que depende del tiempo — las losas del Elevador, los picos y
    # la Snare del Puente, y el impulso que la plataforma imparte al saltar. Con esto sube
    # a ~50 fps. Ojo: con la calidad asi NO se puede juzgar ni rendimiento ni imagen.
    for _c in ("sg.ViewDistanceQuality 0", "sg.AntiAliasingQuality 0", "sg.ShadowQuality 0",
               "sg.GlobalIlluminationQuality 0", "sg.ReflectionQuality 0", "sg.PostProcessQuality 0",
               "sg.TextureQuality 0", "sg.EffectsQuality 0", "sg.FoliageQuality 0",
               "sg.ShadingQuality 0", "r.ScreenPercentage 50", "r.Lumen.DiffuseIndirect.Allow 0",
               "r.Lumen.Reflections.Allow 0", "foliage.DensityScale 0.2", "grass.DensityScale 0.2",
               "t.MaxFPS 0", "Slate.bAllowThrottling 0", "t.IdleWhenNotForeground 0"):
        try:
            unreal.SystemLibrary.execute_console_command(w, _c)
        except Exception:
            pass
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
            # Al morir, el pawn se destruye y la envoltura que devuelve get_player_pawn
            # queda podrida: leerla lanza "ObjectInstance is null". Eso ES la muerte;
            # antes se comia la excepcion 23.000 veces y la partida seguia desde el
            # checkpoint como si nada.
            try:
                pos = pawn.get_actor_location()
            except Exception:
                if ahora - P.get("t_muerte", -99.0) > 3.0:
                    P["t_muerte"] = ahora
                    P["muertes"] = P.get("muertes", 0) + 1
                    nota("MUERTO (%d): el pawn se destruyo, reaparece en checkpoint" % P["muertes"])
                P["pos_prev"] = None
                P["t_prog"] = ahora
                P["ult_pos"] = None
                return
            # muerte y reaparicion, por identidad del pawn Y por salto de posicion:
            # el respawn puede reutilizar el nombre, y un salto de kilometros andando
            # no existe.
            _id = pawn.get_name()
            if P.get("pawn_id") is None:
                P["pawn_id"] = _id
            elif _id != P["pawn_id"]:
                P["pawn_id"] = _id
                P["ult_pos"] = None
                if ahora - P.get("t_muerte", -99.0) > 3.0:      # no contar dos veces
                    P["t_muerte"] = ahora
                    P["muertes"] = P.get("muertes", 0) + 1
                    nota("MUERTO Y REAPARECIDO (%d) en (%.0f %.0f %.0f)" % (P["muertes"], pos.x, pos.y, pos.z))
            # MaxFarsa baja 10 en cada muerte (minimo 50): es el unico contador exacto
            # que se puede leer. Los otros dos avisos (pawn destruido, salto de km) no
            # ven la muerte cuando el respawn reutiliza el pawn y cae cerca, que es lo
            # que pasa en el Puente.
            try:
                _mf = float(pawn.get_editor_property("MaxFarsa"))
            except Exception:
                _mf = None
            if _mf is not None:
                _mf0 = P.get("maxfarsa")
                if _mf0 is None:
                    P["maxfarsa"] = _mf
                elif _mf < _mf0 - 0.5:
                    P["maxfarsa"] = _mf
                    P["t_muerte"] = ahora
                    P["muertes"] = P.get("muertes", 0) + 1
                    nota("MUERTO (%d) en (%.0f %.0f %.0f): MaxFarsa %.0f -> %.0f" % (
                        P["muertes"], pos.x, pos.y, pos.z, _mf0, _mf))
                elif _mf > _mf0 + 0.5:
                    P["maxfarsa"] = _mf
            _ant = P.get("ult_pos")
            if _ant is not None and ahora > P.get("salto_ok", 0.0):
                _salto = math.hypot(pos.x - _ant[0], pos.y - _ant[1])
                if _salto > 4000.0:
                    if ahora - P.get("t_muerte", -99.0) > 3.0:
                        P["t_muerte"] = ahora
                        P["muertes"] = P.get("muertes", 0) + 1
                        nota("MUERTO (%d): salto de %.0f uu a (%.0f %.0f %.0f), reaparecido" % (
                            P["muertes"], _salto, pos.x, pos.y, pos.z))
                    P["pos_prev"] = None
                    P["t_prog"] = ahora
            P["ult_pos"] = (pos.x, pos.y)
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
            # --- losas oscilantes: no hay ruta fija posible. Se persigue la X de la
            # losa siguiente desde dentro de la mia y solo se baja al borde sur cuando
            # las dos se alinean; el salto lo dispara luego el detector de huecos.
            if P["losas"]:
                _mia = None
                for _k, _lo in enumerate(P["losas"]):
                    _l = _lo[2].get_actor_location()
                    if abs(pos.x - _l.x) <= _lo[3] and abs(pos.y - _l.y) <= _lo[4] and pos.z > _l.z:
                        _mia = _k
                        break
                if _mia is not None and _mia + 1 < len(P["losas"]) and dest.y < P["losas"][_mia][0] - 500:
                    _lm = P["losas"][_mia][2].get_actor_location()
                    _ls = P["losas"][_mia + 1][2].get_actor_location()
                    _ey = P["losas"][_mia][4]
                    _dx = _ls.x - _lm.x
                    # Histeresis: se entra a por el borde con |dX| < 250 y no se
                    # abandona hasta 450, o la ventana se cierra mientras andas y el
                    # piloto se pasa la vida yendo y viniendo sin saltar nunca.
                    _yendo = P.get("ir_al_borde_%d" % _mia, False)
                    if not _yendo and abs(_dx) < 250.0:
                        _yendo = True
                        P["t_borde"] = ahora
                    elif _yendo and (abs(_dx) > 450.0 or ahora - P.get("t_borde", ahora) > 5.0):
                        _yendo = False
                    P["ir_al_borde_%d" % _mia] = _yendo
                    # Dos fases. Alinearse manda: mientras el rumbo sea lateral, las
                    # sondas de hueco miran a lo largo de la losa —donde SI hay suelo—
                    # y el salto no se dispara nunca. Solo cuando estoy encarado con la
                    # losa siguiente se va al sur en linea recta.
                    _ox = _lm.x + max(-_ey * 0.75, min(_ey * 0.75, _dx))
                    _encarado = abs(pos.x - _ls.x) < 350.0
                    if _yendo and _encarado:
                        avance = V(0.0, -1.0, 0.0)
                    else:
                        _oy = _lm.y - _ey * 0.4
                        _v = V(_ox - pos.x, _oy - pos.y, 0.0)
                        avance = _v.normal() if _v.length() > 60.0 else V(0.0, -1.0, 0.0)
                    P["t_prog"] = ahora          # esperar la alineacion no es atascarse
                    if ahora - P.get("t_aviso_losa", -9.0) > 2.0:
                        P["t_aviso_losa"] = ahora
                        nota("LOSA %d->%d dX=%+.0f  al borde=%s  me faltan %.0f uu" % (
                            _mia, _mia + 1, _dx, ("SI/encarado" if _encarado else "SI") if _yendo else "no",
                            (pos.y - (_lm.y - _ey))))
            # --- huecos del tramo de saltos: si el suelo se acaba justo delante pero
            # vuelve a haber a un salto de distancia, saltar en vez de caerse. Malakh
            # llega a 327 uu (JumpZ 400, gravedad 1, 400 de andar) y el hueco mas ancho
            # de Anfiteatro->Elevador mide 250.
            if ahora > P.get("t_hueco", 0.0):
                P["t_hueco"] = ahora + 0.05
                P["saltar_hueco"] = False
                # Sin puerta de is_falling a proposito: si esta en el aire, CustomJump
                # no hace nada (JumpMaxCount 1), y filtrar por ahi solo esconde casos.
                if True:
                    def _hay_suelo(d):
                        _x, _y = pos.x + avance.x * d, pos.y + avance.y * d
                        _h = unreal.SystemLibrary.line_trace_single(
                            w, V(_x, _y, pos.z + 40.0), V(_x, _y, pos.z - 260.0),
                            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn],
                            unreal.DrawDebugTrace.NONE, False)
                        _t = _h.to_tuple() if _h else None
                        return bool(_t and _t[0])
                    # Una sola sonda NO vale: con el borde a 170 y un hueco de 100, la
                    # sonda cae al otro lado y el hueco no se ve. Hay que barrer, con
                    # paso menor que el hueco mas estrecho.
                    faltan = [_d for _d in (60.0, 100.0, 140.0, 180.0, 220.0) if not _hay_suelo(_d)]
                    if faltan and faltan[0] <= 140.0:
                        _tras = faltan[-1]
                        for _d in (_tras + 80.0, _tras + 140.0, _tras + 200.0):
                            if _hay_suelo(_d):
                                P["saltar_hueco"] = True
                                break
            if P.get("saltar_hueco") and ahora - P.get("t_salto", 0.0) > 0.8:
                P["t_salto"] = ahora
                try:
                    pawn.call_method("CustomJump", ())
                    P["saltos_hueco"] = P.get("saltos_hueco", 0) + 1
                    nota("SALTO un hueco (%d) en (%.0f %.0f %.0f)" % (
                        P["saltos_hueco"], pos.x, pos.y, pos.z))
                except Exception as e:
                    error("CustomJump hueco", e)
            if atasco > 4.0 and pc.is_move_input_ignored():
                pc.reset_ignore_move_input(); pc.reset_ignore_look_input()
                nota("movimiento ignorado tras interaccion: liberado")
                P["t_prog"] = ahora
            if atasco > 1.5 and not P.get("saltar_hueco"):
                # Rodear de verdad: abanico de trazas de capsula y me quedo con el primer
                # rumbo libre. Un tronco de 60 uu paraba al piloto para siempre porque el
                # rodeo viejo (0,4 de frente + perpendicular) seguia empujando contra el.
                lado = 1.0 if int(atasco / 3.0) % 2 == 0 else -1.0
                if ahora > P.get("t_rodeo", 0.0):
                    base = math.degrees(math.atan2(avance.y, avance.x))
                    libre = None
                    giro = 0
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
                            giro = off
                            break
                    P["rodeo"] = libre
                    # Comprometerse con el rodeo. Re-evaluar cada 0,5 s hacia que el
                    # piloto se apartase, volviese a apuntar al objetivo y rebotase
                    # contra el mismo arbol: 794 s clavado a la salida del Gazebo.
                    P["t_rodeo"] = ahora + (2.5 if giro else 0.5)
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
                encima = None
                for _sn, _luz, _rad in P["snares"]:
                    if _luz is None or _luz.intensity <= 0.0:
                        continue
                    _pi = _sn.get_editor_property("PuntoImpacto")
                    if not (_pi.x or _pi.y):
                        continue
                    _aqui = math.hypot(_pi.x - pos.x, _pi.y - pos.y)
                    _alli = math.hypot(_pi.x - delante.x, _pi.y - delante.y)
                    if _aqui < _rad + 120.0 and (encima is None or _aqui < encima[1]):
                        encima = (_sn.get_actor_label(), _aqui, _pi)
                    elif _alli < _rad + 150.0 and cerca is None:
                        cerca = (_sn.get_actor_label(), _alli)
                # Si el rayo cae DONDE YA ESTOY, frenar no salva: hay que apartarse.
                # Con cinco directores de radio 1500-1800 solapados, pararse te deja
                # quieto dentro del circulo del siguiente.
                P["huida"] = None
                if encima is not None:
                    _nom, _d, _pi = encima
                    _base = math.degrees(math.atan2(pos.y - _pi.y, pos.x - _pi.x))
                    for _off in (0, 30, -30, 60, -60, 90, -90):
                        _r = math.radians(_base + _off)
                        _dir = V(math.cos(_r), math.sin(_r), 0)
                        _dst = V(pos.x + _dir.x * 300.0, pos.y + _dir.y * 300.0, pos.z)
                        _sh = unreal.SystemLibrary.line_trace_single(
                            w, V(_dst.x, _dst.y, _dst.z + 150), V(_dst.x, _dst.y, _dst.z - 400),
                            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn],
                            unreal.DrawDebugTrace.NONE, False)
                        _st = _sh.to_tuple() if _sh else None
                        if not (_st and _st[0]):
                            continue                      # sin suelo: por ahi se cae
                        _ch = unreal.SystemLibrary.capsule_trace_single(
                            w, V(pos.x, pos.y, pos.z + 10), V(_dst.x, _dst.y, pos.z + 10),
                            45.0, 80.0, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn],
                            unreal.DrawDebugTrace.NONE, False)
                        _ct = _ch.to_tuple() if _ch else None
                        if _ct and _ct[0]:
                            continue
                        P["huida"] = (_dir, _nom, _d)
                        break
                P["freno_snare"] = cerca
                # Filas de picos: dañan 12 al pasar y suben/bajan cada 3 s. Se frena
                # ANTES de meterse en la banda; si ya estoy dentro, lo que salva es
                # salir andando, no pararse encima.
                pica = None
                for _fa, _rep, _rad, _zf in P["picos"]:
                    _fl = _fa.get_actor_location()
                    _aqui = math.hypot(_fl.x - pos.x, _fl.y - pos.y)
                    _alli = math.hypot(_fl.x - delante.x, _fl.y - delante.y)
                    if _alli > _rad + 220.0:
                        continue
                    if _aqui < _rad + 60.0:
                        continue
                    if _rep.get_actor_location().z > _zf - 45.0:
                        pica = (_fa.get_actor_label(), _alli)
                        break
                P["freno_picos"] = pica
            huida = P.get("huida")
            if huida is not None:
                _dir, _nom, _d = huida
                if ahora - P.get("t_aviso_huida", -9.0) > 2.0:
                    P["t_aviso_huida"] = ahora
                    nota("SNARE: me aparto de %s, lo tengo a %.0f uu" % (_nom, _d))
                P["t_prog"] = ahora
                pawn.add_movement_input(_dir, 1.0, False)
                return
            frenado = P.get("freno_snare") or P.get("freno_picos")
            if frenado is not None:
                # tope de 3 s: con cadencia 1,4 y aviso de 1,5 el puente casi nunca
                # esta limpio, y quedarse parado para siempre no es cruzar.
                if P["espera_snare"] == 0.0:
                    P["espera_snare"] = ahora
                if ahora - P["espera_snare"] < 3.0:
                    P["t_prog"] = ahora          # esperar no es atascarse
                    if int((ahora - P["espera_snare"]) * 2) == 0:
                        nota("FRENO por %s a %.0f uu" % frenado)
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
                P["salto_ok"] = ahora + 1.5      # este salto lo hago yo, no es muerte
                P["ult_pos"] = None
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
    # Solo el primer hueco de las losas, para probar el salto sin el anfiteatro de por medio
    "salto_prueba": ([
        ("Antes del hueco", V(-18127, 41600, 44), ""),
        ("", V(-18127, 40200, 44), ""),
        ("Tras el hueco", V(-18127, 39400, 44), ""),
    ], None),
    "anfiteatro_elevador": ([
        ("ZONA Anfiteatro", V(-18127, 51184, 144), ""),
        ("ZONA Elevador", V(-18127, 16384, -20), ""),
        ("Arena Elevador", V(-18127, 17984, -70), ""),
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
    P["salto_ok"] = unreal.GameplayStatics.get_time_seconds(w0) + 2.0
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
