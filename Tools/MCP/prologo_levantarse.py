"""Reconstruye AM_DA_PrologoLevantarse, el montage con el que Malakh se levanta
tras el derribo del custodio en el prologo.

POR QUE UN SCRIPT Y NO EL ASSET: `Content/DarkAngels/Animations/` esta en el
.gitignore --es derivada de packs de pago con el repo publico--, asi que el
.uasset no viaja. Las dos secuencias de origen son de DCS y ya estan en disco.
Mismo criterio que `finisher_marcas.py`.

EL PROBLEMA QUE RESUELVE: el montage de reaccion del pack (3,633 s) termina con
el jugador en el suelo y el AnimBP vuelve a idle de golpe -- Malakh se levantaba
"como si nunca hubiera estado en el suelo". Este montage encadena un instante
tendido y un levantarse de verdad.

RECETA:
  seg 0  Anim_GetHitBackFall   3.10 -> 3.31 a rate 0.20  = 1.036 s tendido quieto
  seg 1  Anim_GetHitBackStandUp 0.00 -> 4.65 a rate 1.75  = 2.657 s levantandose
  total 3.693 s, slot FullBody, blend in 0.35 / out 0.25

El blend in va largo a proposito: la pose final de la reaccion y la inicial del
levantarse no son identicas (pelvis z 18,6 vs 14,3; roll 25 vs 87), y 0,35 s
las cose sin que se note.

Ejecutar con:  node ue.mjs py prologo_levantarse
"""

import unreal

DESTINO_CARPETA = "/Game/DarkAngels/Animations/Player"
NOMBRE = "AM_DA_PrologoLevantarse"
M = "%s/%s" % (DESTINO_CARPETA, NOMBRE)

CAER = "/Game/DynamicCombatSystem/DCS/Animations/Common/Anim_GetHitBackFall"
SUBIR = "/Game/DynamicCombatSystem/DCS/Animations/Common/Anim_GetHitBackStandUp"

CAER_DESDE, CAER_HASTA, CAER_RATE = 3.10, 3.3072919845581055, 0.20
#: `Anim_GetHitBackStandUp` dura 7,542 s pero se recorta en 4,65: la cola es
#: relleno de idle y alarga el plano sin aportar nada. El corte viene de
#: AM_DA_Knockdown, que ya lo tenia asi.
SUBIR_HASTA, SUBIR_RATE = 4.6500000954, 1.75
SLOT = "FullBody"
BLEND_IN, BLEND_OUT = 0.35, 0.25

S = unreal.AnimMontageService


def construir(ruta=M):
    """Crea o corrige el montage. Idempotente: se puede llamar mil veces."""
    if not unreal.EditorAssetLibrary.does_asset_exist(ruta):
        creado = S.create_montage_from_animation(CAER, DESTINO_CARPETA, ruta.split("/")[-1])
        assert creado, "no se pudo crear el montage desde %s" % CAER
        print("creado:", creado)
    S.set_slot_name(ruta, 0, SLOT)

    segs = S.list_anim_segments(ruta, 0)
    assert len(segs) >= 1, "el montage no tiene ni un segmento"

    # seg 0: solo la cola de la caida, muy lenta -> se queda tendido
    S.set_segment_start_position(ruta, 0, 0, CAER_DESDE)
    S.set_segment_end_position(ruta, 0, 0, CAER_HASTA)
    S.set_segment_play_rate(ruta, 0, 0, CAER_RATE)
    S.set_segment_start_time(ruta, 0, 0, 0.0)
    dur0 = (CAER_HASTA - CAER_DESDE) / CAER_RATE

    # seg 1: el levantarse, pegado detras
    if len(S.list_anim_segments(ruta, 0)) < 2:
        i = S.add_anim_segment(ruta, 0, SUBIR, dur0, SUBIR_RATE)
        assert i >= 0, "no se pudo anadir el segmento de levantarse"
    S.set_segment_end_position(ruta, 0, 1, SUBIR_HASTA)
    S.set_segment_play_rate(ruta, 0, 1, SUBIR_RATE)
    S.set_segment_start_time(ruta, 0, 1, dur0)

    S.set_blend_in(ruta, BLEND_IN, "Linear")
    S.set_blend_out(ruta, BLEND_OUT, "Linear")

    a = unreal.EditorAssetLibrary.load_asset(ruta)
    unreal.EditorLoadingAndSavingUtils.save_packages([a.get_outermost()], False)
    return ruta


def verificar(ruta=M):
    """Relee del asset. El `True` de los setters no prueba nada por si solo."""
    segs = S.list_anim_segments(ruta, 0)
    print("%s  ->  %.3f s" % (ruta.split("/")[-1], S.get_montage_length(ruta)))
    for s in segs:
        print("   [%d] %-24s en %.3f  dura %.3f  rate %.2f  fuente %.2f->%.2f" % (
            s.segment_index, s.anim_name, s.start_time, s.duration,
            s.play_rate, s.anim_start_pos, s.anim_end_pos))
    pistas = S.list_slot_tracks(ruta)
    print("   slot:", pistas[0].slot_name if pistas else "?")
    ok = (len(segs) == 2
          and abs(segs[0].duration - 1.036) < 0.01
          and abs(segs[1].duration - 2.657) < 0.01
          and str(pistas[0].slot_name) == SLOT)
    print("   VERIFICADO" if ok else "   *** NO CUADRA ***")
    return ok


if __name__ == "__main__":
    construir()
    verificar()
