# -*- coding: utf-8 -*-
"""Construye los combos de la Lanza a partir del Spear Animation Pack.

    execute_python_code(code=open("Tools/MCP/lanza_montages.py").read())

Amplia lo que hizo `montage_lanza.py`, que solo monto el PRIMER golpe
(`M_DA_Lanza_AtaqueLigero_01`). Ese se deja como esta --su ventana de golpe se
midio sobre la PUNTA del asta, que es mejor referencia que la mano-- y aqui se
anaden los tres que faltan del combo ligero y los tres del pesado.

QUE FAMILIA PARA QUE ACCION, y por que. Medido el avance (root) de los cinco
combos enteros:

    combo 01   111 / 296 / 579 / 410     total  1396
    combo 02   217 / 251 / 206 / 292     total   965
    combo 03   275 / 232 / 330 / 118     total   955   picos mas LENTOS (2100-2500)
    combo 04   192 / 178 / 195 / 409     total   975   el mas consistente
    combo 05   118 / 292 / 415 / 351     total  1177

  LIGERO = combo 01, porque su primer golpe YA esta en juego y cambiar de familia
           a mitad de cadena se ve raro. Precio: su tercer golpe embiste 579 cm.
  PESADO = combo 03, el de picos de velocidad mas bajos (2107-2468 frente a los
           3450-4993 del 01), que es lo que hace que un golpe se sienta pesado.

OJO CON EL AVANCE, Y CON LA ESCALA. Los numeros de arriba son los del HUESO ROOT
de la secuencia, y NO son centimetros de mundo: la malla de Malakh va a escala
1,8273 y el root motion se multiplica por ella. Comprobado en juego --195 de root
dieron 357 uu andados-- asi que lo que se siente es esto:

    golpe 1  AS_Combo_Attack_01_01   112 root ->  204 uu
    golpe 2  AS_Combo_Attack_01_02   296 root ->  541 uu
    golpe 3  AS_Combo_Attack_04_03   195 root ->  357 uu
    golpe 4  AS_Combo_Attack_01_04   410 root ->  749 uu

La espada de DCS, sobre la misma malla, viaja de 86 a 302 uu de mundo. Los golpes
2 y 4 se salen de esa banda; el 3 --el unico del que se quejo Angel, y con 1.058
uu era el peor con diferencia-- ya esta dentro.

DE DONDE SALEN LAS VENTANAS: se muestrea `hand_r` cada 0,04 s, se deriva la
velocidad y se busca el pico. Sobre el pico, la forma de la casa: hitbox 0,045
antes, InputBuffer 0,069 antes y 0,091 despues, IgnoreRootMotion la ultima
decima y media.

OJO: `enable_root_motion` se escribe SOBRE EL ASSET DEL PACK. Si se reinstala
desde Fab, se pierde y hay que volver a pasar esto.
"""
import unreal

PACK    = "/Game/Spear"
DESTINO = "/Game/DarkAngels/Animations/Lanza"
CUE     = "/Game/DynamicCombatSystem/DCS/SFX/Weapons/Sword/CUE_SwingSmall"
ANS     = "/Game/DynamicCombatSystem/DCS/Blueprints/AnimNotifies/%s.%s_C"

#: Secuencias cuyo avance NO se quiere.
#:
#: ESTA LISTA CASI NUNCA ES LO QUE QUIERES, y se aprendio caro el 2026-08-31.
#: Apagar `enable_root_motion` NO deja el golpe en el sitio: deja la CAPSULA en el
#: sitio mientras la MALLA sigue viajando, porque el desplazamiento esta horneado
#: en el hueso root y la animacion lo sigue aplicando. Medido con el salto de la
#: lanza: capsula 1 uu, hueso root 109 uu, y creciendo hasta 579. El personaje se
#: despega de su propia capsula y luego pega el tiron de vuelta.
#: Si un golpe viaja demasiado, la salida buena es CAMBIAR LA SECUENCIA por una
#: que viaje menos --que es lo que se hizo con el tercer golpe-- o recortar el
#: montage, si el impacto no cae dentro del tramo que se corta.
SIN_AVANCE = []

#: (secuencia, montage, hitIni, hitDur, bufIni, bufDur, rmIni)
GOLPES = [
    ("AS_Combo_Attack_01_02_Seq", "M_DA_Lanza_AtaqueLigero_02", 0.20, 0.20, 0.13, 0.36, 1.85),
    # El tercer golpe NO es del combo 01. El suyo (01_03) embiste 579 de root, o
    # sea 1.058 uu de mundo --el salto entero ocurre entre 0,6 y 1,0 s y el impacto
    # pica en 0,76, justo en medio, asi que recortarlo perderia el golpe--. Se
    # sustituye por el tercero del combo 04: 195 de root, 357 uu, dentro de la
    # banda de DCS. Su pico esta en 0,16 (1.608 cm/s), de ahi el hitbox en 0,12.
    ("AS_Combo_Attack_04_03_Seq", "M_DA_Lanza_AtaqueLigero_03", 0.12, 0.20, 0.05, 0.36, 2.17),
    ("AS_Combo_Attack_01_04_Seq", "M_DA_Lanza_AtaqueLigero_04", 0.92, 0.20, 0.85, 0.36, 2.77),
    ("AS_Combo_Attack_03_01_Seq", "M_DA_Lanza_Pesado_01",       0.08, 0.20, 0.01, 0.36, 2.52),
    ("AS_Combo_Attack_03_02_Seq", "M_DA_Lanza_Pesado_02",       0.56, 0.20, 0.49, 0.36, 2.35),
    ("AS_Combo_Attack_03_03_Seq", "M_DA_Lanza_Pesado_03",       0.28, 0.20, 0.21, 0.36, 2.35),
]

#: El que ya existia, montado por `montage_lanza.py`. Aqui solo se referencia.
LIGERO_01 = "M_DA_Lanza_AtaqueLigero_01"

svc = unreal.AnimMontageService


def _ruta_de(nombre):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path(PACK, recursive=True):
        if str(a.package_name).split("/")[-1] == nombre:
            return str(a.package_name)
    return None


def _notify_de_sonido(m):
    for i in range(24):
        o = unreal.load_object(m, "AnimNotify_PlaySound_%d" % i)
        if o is not None:
            return o
    return None


def _uno(seq_nombre, montage, hi, hd, bi, bd, ri):
    SEQ = _ruta_de(seq_nombre)
    seq = unreal.load_asset(SEQ) if SEQ else None
    if seq is None:
        raise RuntimeError("no esta el Spear Pack: " + seq_nombre)

    seq.set_editor_property("enable_root_motion", seq_nombre not in SIN_AVANCE)
    unreal.EditorAssetLibrary.save_asset(SEQ)

    ruta = DESTINO + "/" + montage
    if unreal.EditorAssetLibrary.does_asset_exist(ruta):
        for i in range(len(svc.list_notifies(ruta)) - 1, -1, -1):
            svc.remove_notify(ruta, i)
        # Si el montage ya existia pero apunta a OTRA secuencia --paso cuando se
        # cambio el tercer golpe de combo-- hay que cambiarle el segmento. Borrar
        # el asset y rehacerlo no vale: `delete_asset` no quita un asset cargado.
        seg = svc.list_anim_segments(ruta, 0)
        actual = str(seg[0].anim_name) if seg else None
        if actual != seq_nombre:
            for i in range(len(seg) - 1, -1, -1):
                svc.remove_anim_segment(ruta, 0, i)
            svc.add_anim_segment(ruta, 0, SEQ, 0.0)
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

    svc.add_notify(ruta, "/Script/Engine.AnimNotify_PlaySound", max(0.0, hi + 0.01), "Cue_Swing")
    son = _notify_de_sonido(unreal.load_asset(ruta))
    if son is None:
        raise RuntimeError("no encuentro el notify de sonido en " + montage)
    son.set_editor_property("sound", unreal.load_asset(CUE))

    unreal.EditorAssetLibrary.save_asset(ruta)
    return ruta


def pasada():
    return [_uno(*g) for g in GOLPES]


def tabla():
    """Rellena las filas 1 (ligero) y 2 (pesado) de DT_DA_Lanza_Montages."""
    import json
    T = "/Game/DarkAngels/DataTables/DT_DA_Lanza_Montages"
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(T):
        raise RuntimeError("falta la tabla; pasa antes lanza_en_dt_1h.py")
    dt = eal.load_asset(T)
    datos = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(dt))
    ref = lambda n: "/Script/Engine.AnimMontage'%s/%s.%s'" % (DESTINO, n, n)
    ligeros = [ref(LIGERO_01)] + [ref(m) for _, m, _, _, _, _, _ in GOLPES if "Ligero" in m]
    pesados = [ref(m) for _, m, _, _, _, _, _ in GOLPES if "Pesado" in m]
    for f in datos:
        if f["Name"] == "1":
            f["Montages"] = ligeros
        if f["Name"] == "2":
            f["Montages"] = pesados
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(datos))
    eal.save_asset(T)

    d2 = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(eal.load_asset(T)))
    por = {f["Name"]: [m.split("/")[-1].split(".")[0] for m in f.get("Montages", [])] for f in d2}
    fallos = []
    if len(por.get("1", [])) != 4:
        fallos.append("la fila 1 no quedo con los cuatro ligeros: %s" % por.get("1"))
    if len(por.get("2", [])) != 3:
        fallos.append("la fila 2 no quedo con los tres pesados: %s" % por.get("2"))
    return fallos


def verificar():
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


if __name__ == "__main__":
    rutas = pasada()
    fallos = verificar() + tabla()
    print("\n".join(rutas))
    print(("[OK] %d montages + tabla" % len(rutas)) if not fallos else "[FALLO]\n   " + "\n   ".join(fallos))
