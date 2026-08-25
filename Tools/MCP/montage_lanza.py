# -*- coding: utf-8 -*-
"""
Reconstruye el ataque ligero de la Lanza a partir del Spear Animation Pack.

    execute_python_code(code=open("Tools/MCP/montage_lanza.py").read())

POR QUE EXISTE ESTE FICHERO
---------------------------
El montaje vive en `Content/DarkAngels/Animations/`, que esta ENTERO en
`.gitignore` porque esa carpeta referencia animaciones de packs de pago. O sea
que el asset no viaja en el repo: lo que viaja es esta pasada. Igual que
`M_DA_ArrojarLanza`, que tampoco esta en git.

LAS TRES COSAS QUE SE MIDIERON ANTES DE ESCRIBIRLO
--------------------------------------------------
1. QUE SECUENCIA. De los cinco combos, `Combo_Attack_01_01` es la que menos
   viaja (111,6 cm) y la que mas llega (224 cm del root a la punta). Las otras
   viajan entre 191 y 274 cm, que en un ataque ligero es demasiado.

2. DONDE VA EL HITBOX. Muestreando la punta del asta, el golpe vive entre
   t=0,18 y t=0,37: el alcance salta de 146 a 224 cm en t=0,244 y la punta va a
   5000 cm/s. La ventana se pone en 0,20 + 0,17. Lo de t=1,0..1,35 es el
   RECOGER el arma, no un segundo golpe.

3. ROOT MOTION SI, Y NO ES UNA LICENCIA. La espada de DCS ya embiste: todas sus
   secuencias de ataque llevan `enable_root_motion = True` y viajan 46,9 /
   164,6 / 103 / 113,9 cm. Los 111,6 de la lanza caen justo en medio. Sin
   activarlo, el mesh se desplaza 111 cm respecto a la capsula y pega un
   tiron al terminar.

OJO: el flag de root motion se escribe SOBRE EL ASSET DEL PACK. Si Angel
reinstala el Spear Pack desde Fab, se pierde y hay que volver a pasar esto.

Los tiempos de los notifies son los del ligero de DCS reescalados: alli el
InputBuffer abre 0,069 s antes del hitbox y cierra 0,091 despues, y el
IgnoreRootMotion ocupa la ultima decima y media.
"""
import unreal

SEQ     = "/Game/Spear/Animation/Sequence/02_Attack/01_Combo_Attack_01/AS_Combo_Attack_01_01_Seq"
DESTINO = "/Game/DarkAngels/Animations/Lanza"
NOMBRE  = "M_DA_Lanza_AtaqueLigero_01"
MONTAJE = DESTINO + "/" + NOMBRE
CUE     = "/Game/DynamicCombatSystem/DCS/SFX/Weapons/Sword/CUE_SwingSmall"

ANS = "/Game/DynamicCombatSystem/DCS/Blueprints/AnimNotifies/%s.%s_C"
NOTIFIES = [
    ("HitBox",    ANS % ("ANS_HitBox", "ANS_HitBox"),                   0.20, 0.17),
    ("InpBuffer", ANS % ("ANS_InputBuffer", "ANS_InputBuffer"),         0.13, 0.33),
    ("IgnoreRM",  ANS % ("ANS_IgnoreRootMotion", "ANS_IgnoreRootMotion"), 1.68, 0.15),
]

svc = unreal.AnimMontageService


def _notify_de_sonido(m):
    """El array de notifies es protegido, pero el OBJETO se alcanza por nombre desde
    el montaje. El sufijo va subiendo cada vez que se rehace, asi que se barre."""
    for i in range(12):
        o = unreal.load_object(m, "AnimNotify_PlaySound_%d" % i)
        if o is not None:
            return o
    return None


def pasada():
    seq = unreal.load_asset(SEQ)
    if seq is None:
        raise RuntimeError("no esta el Spear Pack: " + SEQ)

    # 1. root motion sobre la secuencia del pack (ver cabecera)
    seq.set_editor_property("enable_root_motion", True)
    unreal.EditorAssetLibrary.save_asset(SEQ)

    # 2. el montaje. SE RECONSTRUYE ENCIMA, no se borra y se rehace: mientras el
    #    asset siga cargado `delete_asset` no lo quita —devuelve sin quejarse y ahi
    #    sigue—, y entonces `create_montage_from_animation` da cadena vacia porque el
    #    nombre esta pillado. Asi ademas la pasada es idempotente.
    if unreal.EditorAssetLibrary.does_asset_exist(MONTAJE):
        ruta = MONTAJE
        for i in range(len(svc.list_notifies(ruta)) - 1, -1, -1):
            svc.remove_notify(ruta, i)
    else:
        ruta = svc.create_montage_from_animation(SEQ, DESTINO, NOMBRE)
        if not ruta:
            raise RuntimeError("no se pudo crear el montaje")

    # 3. la forma de la casa: FullBody y 0,25 de mezcla, como todo DCS
    svc.set_slot_name(ruta, 0, "FullBody")
    svc.set_blend_in(ruta, 0.25, "Linear")
    svc.set_blend_out(ruta, 0.25, "Linear")

    for nombre, clase, ini, dur in NOTIFIES:
        if svc.add_notify_state(ruta, clase, ini, dur, nombre) < 0:
            raise RuntimeError("no entro el notify " + nombre)

    # El sonido va aparte: AddNotify no sabe asignar el cue, pero el objeto del
    # notify SI se alcanza por nombre desde el montaje.
    svc.add_notify(ruta, "/Script/Engine.AnimNotify_PlaySound", 0.21, "Cue_SwingSmall")
    m = unreal.load_asset(ruta)
    son = _notify_de_sonido(m)
    if son is None:
        raise RuntimeError("no encuentro el objeto del notify de sonido")
    son.set_editor_property("sound", unreal.load_asset(CUE))

    unreal.EditorAssetLibrary.save_asset(ruta)
    return ruta


def verificar(ruta):
    """El editor miente en las dos direcciones: se relee campo a campo."""
    m = unreal.load_asset(ruta)
    s = unreal.load_asset(SEQ)
    pistas = m.get_editor_property("slot_anim_tracks")
    seg = pistas[0].get_editor_property("anim_track").get_editor_property("anim_segments")[0]
    fallos = []
    if str(pistas[0].get_editor_property("slot_name")) != "FullBody":
        fallos.append("el slot no es FullBody")
    if seg.get_editor_property("anim_reference").get_name() != SEQ.split("/")[-1]:
        fallos.append("el segmento no apunta a la secuencia buena")
    if not s.get_editor_property("enable_root_motion"):
        fallos.append("la secuencia se quedo sin root motion")
    n = {x.notify_name: x for x in svc.list_notifies(ruta)}
    for nombre, _, ini, dur in NOTIFIES:
        if nombre not in n:
            fallos.append("falta el notify " + nombre)
        elif abs(n[nombre].trigger_time - ini) > 0.01 or abs(n[nombre].duration - dur) > 0.01:
            fallos.append("el notify %s esta descolocado" % nombre)
    son = _notify_de_sonido(m)
    if son is None or son.get_editor_property("sound") is None:
        fallos.append("el notify de sonido se quedo mudo")
    return fallos


if __name__ == "__main__":
    ruta = pasada()
    fallos = verificar(ruta)
    print(("[OK] " + ruta) if not fallos else "[FALLO]\n   " + "\n   ".join(fallos))
