# -*- coding: utf-8 -*-
"""Construye los montages del Espadon a partir del Two-Handed Sword Animation Pack.

    execute_python_code(code=open("Tools/MCP/espadon_montages.py").read())

POR QUE UN GUION Y NO LOS ASSETS
--------------------------------
Los montages viven en `Content/DarkAngels/Animations/`, que esta ENTERO en
`.gitignore` porque referencia animaciones de packs de pago. El asset no viaja en
el repo: lo que viaja es esta pasada. Igual que la Lanza (`montage_lanza.py`).

EL PACK: `Two-Handed Sword Animation Pack` de Greenimate, 391 animaciones. Trae dos
juegos, UE4 y UE5; **se usa el de UE5**, que es el esqueleto de Malakh.

POR QUE ESTE PACK Y NO EL Sword_Duel_Pack, medido:
  - su desplazamiento esta en el hueso ROOT (167,2 root = 167,2 pelvis), asi que
    `enable_root_motion` lo extrae de verdad. En el Sword_Duel_Pack el viaje esta
    en la PELVIS y activarlo despegaria la malla de la capsula.
  - manos a 7-22 cm durante el golpe: empunadura a dos manos real.

QUE COMBO PARA QUE ACCION, medido:
  - LIGERO = combo 01, cuatro golpes de 0,83 / 1,12 / 1,33 / 1,33 s.
  - PESADO = combo 03, tres golpes de 2,08 / 1,50 / 2,08 s, con 245 cm de
    embestida en el remate.

DE DONDE SALEN LAS VENTANAS DE GOLPE
------------------------------------
No estan a ojo. Se muestrea `hand_r` cada 0,04 s, se deriva la velocidad y se
localiza el PICO del golpe (entre 1.040 y 2.633 cm/s segun la secuencia). Sobre
ese pico se aplica la forma de la casa, la misma que se midio para la Lanza:

  hitbox       : arranca 0,045 antes del pico. Dura 0,13 s en los golpes rapidos
                 (<1,5 s) y 0,20 en los lentos.
  inputBuffer  : abre 0,069 antes del hitbox y cierra 0,091 despues -- los
                 numeros del ligero de DCS.
  ignoreRootMot: la ultima decima y media.

OJO: `enable_root_motion` se escribe SOBRE EL ASSET DEL PACK. Si se reinstala
desde Fab, se pierde y hay que volver a pasar esto.
"""
import unreal

PACK    = "/Game/Two_Handed_Sword/Animations/Sequence_UE5/"
DESTINO = "/Game/DarkAngels/Animations/Espadon"
CUE     = "/Game/DynamicCombatSystem/DCS/SFX/Weapons/Sword/CUE_SwingSmall"
ANS     = "/Game/DynamicCombatSystem/DCS/Blueprints/AnimNotifies/%s.%s_C"

#: (secuencia, nombre del montage, hitIni, hitDur, bufIni, bufDur, rmIni)
GOLPES = [
    ("AS_Combo_Attack_01_01_Seq", "M_DA_Espadon_Ligero_01", 0.28, 0.13, 0.21, 0.29, 0.68),
    ("AS_Combo_Attack_01_02_Seq", "M_DA_Espadon_Ligero_02", 0.24, 0.13, 0.17, 0.29, 0.97),
    ("AS_Combo_Attack_01_03_Seq", "M_DA_Espadon_Ligero_03", 0.36, 0.13, 0.29, 0.29, 1.18),
    ("AS_Combo_Attack_01_04_Seq", "M_DA_Espadon_Ligero_04", 0.43, 0.13, 0.36, 0.29, 1.18),
    ("AS_combo_Attack_03_01_Seq", "M_DA_Espadon_Pesado_01", 0.91, 0.20, 0.84, 0.36, 1.93),
    ("AS_combo_Attack_03_02_Seq", "M_DA_Espadon_Pesado_02", 0.52, 0.20, 0.45, 0.36, 1.35),
    ("AS_Combo_Attack_03_03_Seq", "M_DA_Espadon_Pesado_03", 0.76, 0.20, 0.69, 0.36, 1.93),
]

svc = unreal.AnimMontageService


def _ruta_de(nombre):
    """El pack reparte las secuencias en subcarpetas Y mezcla mayusculas
    (`AS_Combo_Attack_03_03` junto a `AS_combo_Attack_03_01`), asi que la ruta se
    resuelve por el registro y no se cablea."""
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path(PACK.rstrip("/"), recursive=True):
        if str(a.package_name).split("/")[-1] == nombre:
            return str(a.package_name)
    return None


def _notify_de_sonido(m):
    """El array de notifies es protegido, pero el OBJETO se alcanza por nombre. El
    sufijo sube cada vez que se rehace el montaje, asi que se barre."""
    for i in range(24):
        o = unreal.load_object(m, "AnimNotify_PlaySound_%d" % i)
        if o is not None:
            return o
    return None


def _uno(seq_nombre, montage, hi, hd, bi, bd, ri):
    SEQ = _ruta_de(seq_nombre)
    seq = unreal.load_asset(SEQ) if SEQ else None
    if seq is None:
        raise RuntimeError("no esta el Two-Handed Sword Pack: " + seq_nombre)

    # 1. root motion sobre la secuencia del pack. Aqui SI funciona: el viaje esta
    #    en el hueso root (medido), no en la pelvis.
    seq.set_editor_property("enable_root_motion", True)
    unreal.EditorAssetLibrary.save_asset(SEQ)

    # 2. el montaje. Se reconstruye ENCIMA: mientras el asset siga cargado
    #    `delete_asset` no lo quita y `create_montage_from_animation` daria cadena
    #    vacia porque el nombre esta pillado. Asi ademas la pasada es idempotente.
    ruta = DESTINO + "/" + montage
    if unreal.EditorAssetLibrary.does_asset_exist(ruta):
        for i in range(len(svc.list_notifies(ruta)) - 1, -1, -1):
            svc.remove_notify(ruta, i)
    else:
        ruta = svc.create_montage_from_animation(SEQ, DESTINO, montage)
        if not ruta:
            raise RuntimeError("no se pudo crear " + montage)

    svc.set_slot_name(ruta, 0, "FullBody")
    svc.set_blend_in(ruta, 0.25, "Linear")
    svc.set_blend_out(ruta, 0.25, "Linear")

    for nombre, clase, ini, dur in (
            ("HitBox",    ANS % ("ANS_HitBox", "ANS_HitBox"),                     hi, hd),
            ("InpBuffer", ANS % ("ANS_InputBuffer", "ANS_InputBuffer"),           bi, bd),
            ("IgnoreRM",  ANS % ("ANS_IgnoreRootMotion", "ANS_IgnoreRootMotion"), ri, 0.15)):
        if svc.add_notify_state(ruta, clase, ini, dur, nombre) < 0:
            raise RuntimeError("no entro el notify %s en %s" % (nombre, montage))

    # El sonido va aparte: add_notify no sabe asignar el cue.
    svc.add_notify(ruta, "/Script/Engine.AnimNotify_PlaySound", max(0.0, hi + 0.01), "Cue_Swing")
    son = _notify_de_sonido(unreal.load_asset(ruta))
    if son is None:
        raise RuntimeError("no encuentro el objeto del notify de sonido en " + montage)
    son.set_editor_property("sound", unreal.load_asset(CUE))

    unreal.EditorAssetLibrary.save_asset(ruta)
    return ruta


def pasada():
    return [_uno(*g) for g in GOLPES]


def verificar():
    """El editor miente en las dos direcciones: se relee campo a campo."""
    fallos = []
    for seq_nombre, montage, hi, hd, bi, bd, ri in GOLPES:
        ruta = DESTINO + "/" + montage
        m = unreal.load_asset(ruta)
        if m is None:
            fallos.append("falta " + montage); continue
        pistas = m.get_editor_property("slot_anim_tracks")
        seg = pistas[0].get_editor_property("anim_track").get_editor_property("anim_segments")[0]
        if str(pistas[0].get_editor_property("slot_name")) != "FullBody":
            fallos.append(montage + ": el slot no es FullBody")
        if seg.get_editor_property("anim_reference").get_name() != seq_nombre:
            fallos.append(montage + ": el segmento no apunta a su secuencia")
        if not unreal.load_asset(_ruta_de(seq_nombre)).get_editor_property("enable_root_motion"):
            fallos.append(seq_nombre + ": se quedo sin root motion")
        n = {x.notify_name: x for x in svc.list_notifies(ruta)}
        for nombre, ini, dur in (("HitBox", hi, hd), ("InpBuffer", bi, bd), ("IgnoreRM", ri, 0.15)):
            if nombre not in n:
                fallos.append("%s: falta el notify %s" % (montage, nombre))
            elif abs(n[nombre].trigger_time - ini) > 0.01 or abs(n[nombre].duration - dur) > 0.01:
                fallos.append("%s: el notify %s esta descolocado" % (montage, nombre))
        son = _notify_de_sonido(m)
        if son is None or son.get_editor_property("sound") is None:
            fallos.append(montage + ": el notify de sonido se quedo mudo")
    return fallos


TABLA_1H = "/Game/DynamicCombatSystem/DCS/DataTables/Montages/Player/DT_Player_1H_Montages"
TABLA_2H = "/Game/DarkAngels/DataTables/DT_DA_2H_Montages"


def tabla():
    """Crea DT_DA_2H_Montages: copia de la de una mano con las filas 1 y 2 cambiadas.

    Se DUPLICA en vez de crearla vacia para que las once acciones que el pack no
    cubre --bloqueo, parry, equipar, impacto...-- sigan cayendo en las animaciones
    de DCS. Solo se sustituye lo que tenemos.

    La tabla tampoco viaja en el repo: es copia de un asset de pago, misma regla
    que BT_DA_Guerrero. Por eso se rehace aqui.
    """
    import json
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(TABLA_2H):
        if eal.duplicate_asset(TABLA_1H, TABLA_2H) is None:
            raise RuntimeError("no pude duplicar la tabla de una mano")
    dt = eal.load_asset(TABLA_2H)
    datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(dt))
    ref = lambda n: "/Script/Engine.AnimMontage'%s/%s.%s'" % (DESTINO, n, n)
    ligeros = [ref(m) for _, m, _, _, _, _, _ in GOLPES if "Ligero" in m]
    pesados = [ref(m) for _, m, _, _, _, _, _ in GOLPES if "Pesado" in m]
    for f in datos:
        if f["Name"] == "1":
            f["Montages"] = ligeros
        if f["Name"] == "2":
            f["Montages"] = pesados
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(datos))
    eal.save_asset(TABLA_2H)

    # se relee del disco: el guardado miente
    d2 = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(
        eal.load_asset(TABLA_2H)))
    por_fila = {f["Name"]: [m.split("/")[-1].split(".")[0] for m in f.get("Montages", [])] for f in d2}
    fallos = []
    if por_fila.get("1") != [m for _, m, _, _, _, _, _ in GOLPES if "Ligero" in m]:
        fallos.append("la fila 1 (ligero) no cuajo: %s" % por_fila.get("1"))
    if por_fila.get("2") != [m for _, m, _, _, _, _, _ in GOLPES if "Pesado" in m]:
        fallos.append("la fila 2 (pesado) no cuajo: %s" % por_fila.get("2"))
    return fallos


if __name__ == "__main__":
    rutas = pasada()
    fallos = verificar() + tabla()
    print("\n".join(rutas))
    print(("[OK] %d montages" % len(rutas)) if not fallos else "[FALLO]\n   " + "\n   ".join(fallos))
