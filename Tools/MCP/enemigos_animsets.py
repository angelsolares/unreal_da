# -*- coding: utf-8 -*-
"""Da a los enemigos los animsets nuevos: Espadon al Heraldo, Lanza al Lancero.

    execute_python_code(code=open("Tools/MCP/enemigos_animsets.py").read())

EL PROBLEMA. Los montages nuevos (Two-Handed Sword Pack y Spear Pack) solo los
usaba el JUGADOR, porque el enrutado vive en el `GetMontages` sobrescrito de
`BP_DA_PlayerCharacter`. Los enemigos heredan de `BP_BaseAI`, cuyo `GetMontages`
--que en realidad esta en `BP_CombatCharacter`-- enruta por ESTILO DE COMBATE y
manda todo el mele armado a `DT_AI_1H_Montages`. Medido en PIE: con el Heraldo ya
empunando el espadon, `IsTwoHandedWeaponEquipped` daba True y `GetMontages`
seguia devolviendo `DT_AI_1H_Montages`.

LA SALIDA, y por que esta. Los cuatro enemigos de DA YA tenian un `GetMontages`
propio, pero vacio: llamaba al padre y devolvia su resultado. O sea que el gancho
ya existia y solo habia que darle contenido. No se toca DCS.

LA CADENCIA: POR QUE LOS ENEMIGOS NO USAN LOS MONTAGES DEL JUGADOR TAL CUAL
---------------------------------------------------------------------------
`calibracion.json` fija para el Lancero y el Heraldo un ataque de **2,206 s**
(impacto 0,915, ventana 0,214), y toda la matriz de la Forja esta medida con eso.
Los montages del pack duran otra cosa --el ligero del Espadon, 0,83 s, es casi
tres veces mas rapido--, asi que enchufarlos crudos convertia al Heraldo en un
enemigo distinto del que dice el diseno: "pared con dientes... tarda 2,21 s".

Por eso la IA no comparte montage con el jugador: se le hacen COPIAS con
`rate_scale` ajustado para que duren exactamente 2,206 s. Las copias viven en
`Animations/IA/` y llevan sufijo `_IA`.

QUE ANIMACION PARA CADA UNO, y por que:
  - HERALDO: sus ligeros salen de las secuencias PESADAS del Espadon (2,08 s), no
    de las ligeras (0,83-1,33). Dos motivos: estirar 0,83 hasta 2,21 es camara
    lenta --un factor 2,6--, y el golpe pesado es lo que pide su arquetipo. Con
    las pesadas el ajuste es de solo 0,94, o sea casi ninguno.
  - LANCERO: NO valen las mismas secuencias que usa el jugador. Aquellas se
    eligieron por VIAJAR POCO, y las de poco viaje del Spear Pack pican todas muy
    pronto: el impacto caia en 0,11-0,26 s, o sea que el Lancero pegaba casi sin
    telegrafiar (DCS lo hacia en 0,915). Van las TRES QUE MAS TARDAN en picar de
    las veinte del pack, medido:

        AS_Combo_Attack_04_04   impacto al 38,1%  748 uu
        AS_Combo_Attack_01_04   impacto al 32,9%  749 uu
        AS_Combo_Attack_05_04   impacto al 31,5%  642 uu

    SE ELIGE EL VIAJE LARGO A PROPOSITO, y esto contradice el criterio del
    JUGADOR: alli 748 uu era inaceptable --Angel se quejo de que el golpe se iba
    lejos-- pero en un enemigo el viaje es CERRAR DISTANCIA, que es lo que hace un
    lancero, y el telegrafiado es lo que decide si el jugador puede reaccionar.
    Lo probo la matriz de la Forja: con las de poco viaje (impacto 0,397) el caso
    Cierre pasaba de -49% a -23% y el daño base del caso DOBLABA, de 49 a 105.

LAS VENTANAS SE MIDEN AQUI, no se copian. `_pico()` muestrea `hand_r` cada 0,04 s
sobre la secuencia del pack y busca el maximo de velocidad; encima va la forma de
la casa (hitbox 0,045 antes del pico, InputBuffer 0,07 antes y 0,36 de ancho,
IgnoreRootMotion la ultima decima y media). Asi la ventana sigue cayendo sobre el
golpe aunque se cambie de secuencia.

Las once acciones que el pack no cubre --bloqueo, parry, equipar, impacto,
especial...-- siguen cayendo en las animaciones de DCS: las tablas son COPIAS
COMPLETAS de `DT_AI_1H_Montages` con solo dos filas cambiadas.

Nada de esto viaja en el repo --las tablas son copia de un asset de pago y los
montages referencian packs de pago--, salvo el grafo de cada enemigo. Viaja esta
pasada.
"""
import json

import unreal

AI_1H = "/Game/DynamicCombatSystem/DCS/DataTables/Montages/AI/DT_AI_1H_Montages"
DEST_IA = "/Game/DarkAngels/Animations/IA"

#: `calibracion.json` -> arquetipos.lancero_del_alba / elite_pesado -> ataque.duracion
CADENCIA_IA = 2.206

CUE = "/Game/DynamicCombatSystem/DCS/SFX/Weapons/Sword/CUE_SwingSmall"
ANS = "/Game/DynamicCombatSystem/DCS/Blueprints/AnimNotifies/%s.%s_C"

#: enemigo -> (tabla, secuencias del ligero, secuencias del pesado, pack, prefijo)
RECETA = {
    "BP_DA_Heraldo": (
        "/Game/DarkAngels/DataTables/DT_DA_AI_2H_Montages",
        ["AS_combo_Attack_03_01_Seq", "AS_Combo_Attack_03_03_Seq"],
        ["AS_combo_Attack_03_02_Seq"],
        "/Game/Two_Handed_Sword",
        "M_DA_IA_Espadon",
    ),
    "BP_DA_Lancero": (
        "/Game/DarkAngels/DataTables/DT_DA_AI_Lanza_Montages",
        ["AS_Combo_Attack_04_04_Seq", "AS_Combo_Attack_01_04_Seq", "AS_Combo_Attack_05_04_Seq"],
        ["AS_Combo_Attack_02_04_Seq"],
        "/Game/Spear",
        "M_DA_IA_Lanza",
    ),
}

FILA_LIGERO = "1"
FILA_PESADO = "4"

svc = unreal.AnimMontageService


def _ruta_seq(pack, nombre):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path(pack, recursive=True):
        if str(a.package_name).split("/")[-1] == nombre:
            return str(a.package_name)
    raise RuntimeError("no esta la secuencia %s en %s" % (nombre, pack))


def _pico(ruta):
    """Devuelve (duracion, instante del pico de velocidad de `hand_r`)."""
    import math
    s = unreal.EditorAssetLibrary.load_asset(ruta)
    d = s.get_editor_property("sequence_length") / max(0.001, s.get_editor_property("rate_scale"))
    P, T = [], []
    t = 0.0
    while t <= d:
        b = [x for x in unreal.AnimSequenceService.get_pose_at_time(ruta, t, True)
             if str(x.bone_name) == "hand_r"][0].transform.translation
        P.append((b.x, b.y, b.z)); T.append(t); t += 0.04
    _, tp = max((math.dist(P[i], P[i - 1]) / 0.04, T[i]) for i in range(1, len(P)))
    return d, tp


def _notify_de_sonido(m):
    for i in range(24):
        o = unreal.load_object(m, "AnimNotify_PlaySound_%d" % i)
        if o is not None:
            return o
    return None


def _montage_ia(pack, seq_nombre, nombre):
    """Construye un montage de IA: notifies sobre el pico y cadencia 2,206.

    `rate_scale` no toca los tiempos de los notifies --viven en el espacio del
    montage-- asi que la ventana se escala sola y sigue cayendo sobre el golpe.
    """
    eal = unreal.EditorAssetLibrary
    SEQ = _ruta_seq(pack, seq_nombre)
    dur, pico = _pico(SEQ)

    # ROOT MOTION. Sin esto la CAPSULA se queda quieta y la MALLA se va sola: el
    # enemigo se despega de su propio cuerpo. Medido en PIE antes de arreglarlo:
    # 749 uu de separacion en el Lancero. Es el mismo fallo que se documento para
    # el tercer golpe del jugador, y se colo aqui porque este guion construia los
    # montages sin tocar la secuencia. Se escribe SOBRE EL ASSET DEL PACK.
    s = eal.load_asset(SEQ)
    if not s.get_editor_property("enable_root_motion"):
        s.set_editor_property("enable_root_motion", True)
        eal.save_asset(SEQ)

    hi = max(0.0, pico - 0.045)
    bi = max(0.0, hi - 0.07)
    ri = max(0.0, dur - 0.15)

    ruta = DEST_IA + "/" + nombre
    if eal.does_asset_exist(ruta):
        for i in range(len(svc.list_notifies(ruta)) - 1, -1, -1):
            svc.remove_notify(ruta, i)
        seg = svc.list_anim_segments(ruta, 0)
        if not seg or str(seg[0].anim_name) != seq_nombre:
            for i in range(len(seg) - 1, -1, -1):
                svc.remove_anim_segment(ruta, 0, i)
            svc.add_anim_segment(ruta, 0, SEQ, 0.0)
    else:
        ruta = svc.create_montage_from_animation(SEQ, DEST_IA, nombre)
        if not ruta:
            raise RuntimeError("no se pudo crear " + nombre)

    svc.set_slot_name(ruta, 0, "FullBody")
    svc.set_blend_in(ruta, 0.25, "Linear")
    svc.set_blend_out(ruta, 0.25, "Linear")
    for et, clase, ini, d in (
            ("HitBox",    ANS % ("ANS_HitBox", "ANS_HitBox"),                     hi, 0.20),
            ("InpBuffer", ANS % ("ANS_InputBuffer", "ANS_InputBuffer"),           bi, 0.36),
            ("IgnoreRM",  ANS % ("ANS_IgnoreRootMotion", "ANS_IgnoreRootMotion"), ri, 0.15)):
        if svc.add_notify_state(ruta, clase, ini, d, et) < 0:
            raise RuntimeError("no entro el notify %s en %s" % (et, nombre))
    svc.add_notify(ruta, "/Script/Engine.AnimNotify_PlaySound", max(0.0, hi + 0.01), "Cue_Swing")
    son = _notify_de_sonido(eal.load_asset(ruta))
    if son is not None:
        son.set_editor_property("sound", eal.load_asset(CUE))

    m = eal.load_asset(ruta)
    m.set_editor_property("rate_scale", m.get_editor_property("sequence_length") / CADENCIA_IA)
    eal.save_asset(ruta)
    return ruta


def _ref(ruta):
    n = ruta.split("/")[-1]
    return "/Script/Engine.AnimMontage'%s.%s'" % (ruta, n)


def _tabla(destino, ligeros, pesados):
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(destino):
        if eal.duplicate_asset(AI_1H, destino) is None:
            raise RuntimeError("no pude duplicar " + AI_1H)
    dt = eal.load_asset(destino)
    datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(dt))
    for f in datos:
        if f["Name"] == FILA_LIGERO:
            f["Montages"] = [_ref(m) for m in ligeros]
        if f["Name"] == FILA_PESADO:
            f["Montages"] = [_ref(m) for m in pesados]
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(datos))
    eal.save_asset(destino)


def _nombres(prefijo, cuantos_l, cuantos_p):
    l = ["%s_Ligero_%02d" % (prefijo, i + 1) for i in range(cuantos_l)]
    p = ["%s_Pesado_%02d" % (prefijo, i + 1) for i in range(cuantos_p)]
    return l, p


def tablas():
    for _, (destino, ligeros, pesados, pack, prefijo) in RECETA.items():
        nl, np_ = _nombres(prefijo, len(ligeros), len(pesados))
        _tabla(destino,
               [_montage_ia(pack, s, n) for s, n in zip(ligeros, nl)],
               [_montage_ia(pack, s, n) for s, n in zip(pesados, np_)])


def verificar_tablas():
    """Se relee del disco: el guardado miente en las dos direcciones."""
    eal = unreal.EditorAssetLibrary
    fallos = []
    for enemigo, (destino, ligeros, pesados, pack, prefijo) in RECETA.items():
        nl, np_ = _nombres(prefijo, len(ligeros), len(pesados))
        if not eal.does_asset_exist(destino):
            fallos.append("falta la tabla de %s" % enemigo); continue
        datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(
            eal.load_asset(destino)))
        por = {f["Name"]: [m.split("/")[-1].split(".")[0] for m in f.get("Montages", [])] for f in datos}
        if por.get(FILA_LIGERO) != nl:
            fallos.append("%s: la fila del ligero no cuajo: %s" % (enemigo, por.get(FILA_LIGERO)))
        if por.get(FILA_PESADO) != np_:
            fallos.append("%s: la fila del pesado no cuajo: %s" % (enemigo, por.get(FILA_PESADO)))
        if len(datos) != 12:
            fallos.append("%s: la tabla perdio filas (%d de 12)" % (enemigo, len(datos)))
        for nombre, seq in zip(nl + np_, ligeros + pesados):
            ruta = DEST_IA + "/" + nombre
            a = eal.load_asset(ruta)
            if a is None:
                fallos.append("falta el montage %s" % ruta); continue
            dur = a.get_editor_property("sequence_length") / a.get_editor_property("rate_scale")
            if abs(dur - CADENCIA_IA) > 0.01:
                fallos.append("%s dura %.3f y la calibracion pide %.3f" % (nombre, dur, CADENCIA_IA))
            pistas = a.get_editor_property("slot_anim_tracks")
            s0 = pistas[0].get_editor_property("anim_track").get_editor_property("anim_segments")[0]
            if s0.get_editor_property("anim_reference").get_name() != seq:
                fallos.append("%s no apunta a %s" % (nombre, seq))
            n = {x.notify_name: x for x in svc.list_notifies(ruta)}
            if "HitBox" not in n:
                fallos.append("%s: falta el notify HitBox" % nombre)
    return fallos


#: El Heraldo cambia el hacha por el Espadon. Va AQUI y no en el .uasset porque
#: `DA_DA_Espadon` esta en .gitignore --es copia de un asset de pago-- y el
#: blueprint del Heraldo SI viaja: sin esta pasada, un clon recien bajado se
#: encuentra la ranura vacia.
#: Y no es un capricho: `calibracion.json` ya le asigna `"arma": "espadon_alabarda"`.
HERALDO_EQ = ("/Game/DarkAngels/Blueprints/Enemies/BP_DA_Heraldo"
              ".BP_DA_Heraldo_C:Equipment_GEN_VARIABLE")
ESPADON = "/Game/DarkAngels/Blueprints/Items/DA_DA_Espadon"


def arma_del_heraldo():
    """Pone el Espadon en la ranura de melé del Heraldo.

    OJO CON LOS STRUCTS: el editor devuelve COPIAS. Mutar `items[0]` en el sitio
    NO escribe nada --probado, se relee igual que estaba--; hay que devolver cada
    copia modificada a su array y reasignar de dentro afuera. Y luego contar los
    elementos, porque el bug conocido de los arrays de structs se come el ultimo.
    """
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(ESPADON):
        raise RuntimeError("falta %s; pasa antes espadon_item.py" % ESPADON)
    eqt = unreal.load_object(None, HERALDO_EQ)
    if eqt is None:
        raise RuntimeError("no encuentro la plantilla de equipo del Heraldo")
    esp = eal.load_asset(ESPADON)

    ms = eqt.get_editor_property("MeleeWeaponSlots")
    slots = list(ms.get_editor_property("Slots"))
    items = list(slots[0].get_editor_property("Items"))
    it0 = items[0]; it0.set_editor_property("Item", esp); items[0] = it0
    s0 = slots[0]; s0.set_editor_property("Items", items); slots[0] = s0
    ms.set_editor_property("Slots", slots)
    eqt.set_editor_property("MeleeWeaponSlots", ms)

    P = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Heraldo"
    unreal.BlueprintEditorLibrary.compile_blueprint(eal.load_asset(P))
    eal.save_asset(P)


def verificar_arma():
    ms = unreal.load_object(None, HERALDO_EQ).get_editor_property("MeleeWeaponSlots")
    items = ms.get_editor_property("Slots")[0].get_editor_property("Items")
    nombres = [i.get_editor_property("Item").get_name() if i.get_editor_property("Item") else None
               for i in items]
    fallos = []
    if nombres[:1] != ["DA_DA_Espadon"]:
        fallos.append("el Heraldo no quedo con el Espadon: %s" % nombres)
    if len(items) != 3:
        fallos.append("la ranura perdio elementos (%d de 3)" % len(items))
    return fallos


def verificar_variables():
    """La tabla se enchufa por una variable `TablaMontages` que lee el GetMontages
    propio de cada enemigo. El grafo SI viaja en el .uasset; esto solo comprueba
    que el default no se ha perdido."""
    fallos = []
    for enemigo, (destino, _, _, _, _) in RECETA.items():
        P = "/Game/DarkAngels/Blueprints/Enemies/" + enemigo
        cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_asset(P).generated_class())
        try:
            v = cdo.get_editor_property("TablaMontages")
        except Exception:
            fallos.append("%s: no tiene la variable TablaMontages" % enemigo); continue
        if v is None or v.get_path_name().split(".")[0] != destino:
            fallos.append("%s: TablaMontages apunta a %s" % (enemigo, v))
    return fallos


def impactos():
    """Devuelve, por enemigo, cuando cae el golpe en segundos REALES.

    Sirve para contrastar con `calibracion.json` (impacto 0,915, ventana 0,214).
    El notify vive en el espacio del montage, asi que el tiempo real es
    `trigger_time / rate_scale`.
    """
    eal = unreal.EditorAssetLibrary
    out = {}
    for enemigo, (_, ligeros, pesados, _, prefijo) in RECETA.items():
        nl, _np = _nombres(prefijo, len(ligeros), len(pesados))
        filas = []
        for nombre in nl:
            ruta = DEST_IA + "/" + nombre
            a = eal.load_asset(ruta)
            rate = a.get_editor_property("rate_scale")
            n = {x.notify_name: x for x in svc.list_notifies(ruta)}
            hb = n.get("HitBox")
            if hb:
                filas.append((nombre, hb.trigger_time / rate, hb.duration / rate))
        out[enemigo] = filas
    return out


if __name__ == "__main__":
    tablas()
    arma_del_heraldo()
    f = verificar_tablas() + verificar_arma() + verificar_variables()
    print("[OK] enemigos con sus animsets, a la cadencia de la Forja"
          if not f else "[FALLO]\n   " + "\n   ".join(f))
    for enemigo, filas in impactos().items():
        for nombre, ini, dur in filas:
            print("   %-14s %-34s impacto %.3f  ventana %.3f" % (enemigo, nombre, ini, dur))
