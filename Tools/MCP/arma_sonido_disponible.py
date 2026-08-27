# -*- coding: utf-8 -*-
#
# EL SONIDO DEL ARMA DISPONIBLE (S9). Crea SC_DA_ArmaDisponible y su atenuacion.
#
#   node ue.mjs py arma_sonido_disponible.py
#
# Idempotente y relee del disco al final, que aqui el true miente. El porque de
# cada decision esta en Tools/MCP/PDF_V2_ESTADO.md, S9; aqui solo lo que hace
# falta para tocarlo:
#
#   - DOS CAPAS, porque en el proyecto no hay ningun sonido celestial (se
#     listaron los 151 SoundWaves de /Game que no son de DCS: pueblo, pasos,
#     fuego y truenos). WAV_UnsheathSword subido de tono dice ARMA;
#     WAV_PotionHeal bajado y flojo dice CELESTIAL. Para cambiarlo, las dos
#     rutas de FILO y MAGIA: ni el grafo ni el blueprint se tocan.
#   - SOUNDCUE Y NO METASOUND: los MetaSounds de UI matan el editor en este
#     proyecto (UI_Select_MS). Es la misma razon por la que los clics del Debug
#     HUD son cues.
#   - LA ATENUACION NO ES ADORNO: sin ella el sonido no dice "ha caido un arma
#     ALLI", dice "ha caido un arma". Radio 2500, caida 6000, para una arena de
#     2200 de radio.
#
# NOMBRES DE PROPIEDAD QUE NO SALEN EN dir(), y que costaron media tarde:
#
#     SoundNodeWavePlayer      -> sound_wave_asset_ptr   (sound_wave esta
#                                 deprecado; sound_wave_asset NO existe)
#     SoundNodeModulator       -> pitch_min/max, volume_min/max
#     SoundAttenuationSettings -> attenuate y spatialize, NO enable_attenuation
#
# dir() sobre esos nodos devuelve casi nada y parece que no se pueden tocar desde
# Python: es mentira, set_editor_property va por reflexion y los encuentra. Por
# eso prop() prueba y APUNTA lo que no cuela en vez de morirse.
#
# ### EL input_volume DEL MIXER TUMBA EL EDITOR, Y NO AL CREARLO: AL SONAR
#
# Un SoundNodeMixer guarda un array InputVolume con UNA entrada por hijo. Si lo
# dejas vacio, el asset se crea, se guarda, se relee perfecto y el grafo se ve
# bien en el editor. Y la primera vez que el cue SUENA, el motor indexa
# InputVolume[0] sobre un array de cero y se lleva el editor por delante:
#
#     Assertion failed: (Index >= 0) & (Index < ArrayNum)  [Array.h:1339]
#     Array index out of bounds: 0 into an array of size 0
#
# Paso el 2026-08-26 al matar al Lancero en PIE: crash duro, sin dialogo. No hubo
# perdida porque todo estaba guardado, pero la leccion es que **un SoundCue mal
# formado no se detecta releyendolo**. Se detecta sonando.

import unreal
import traceback
import io

CARPETA = "/Game/DarkAngels/Audio"
CUE = "SC_DA_ArmaDisponible"
ATT = "ATT_DA_ArmaDisponible"

FILO = "/Game/DynamicCombatSystem/DCS/SFX/Weapons/Sword/WAV_UnsheathSword"
MAGIA = "/Game/DynamicCombatSystem/DCS/SFX/Actions/WAV_PotionHeal"

# (onda, pitch_min, pitch_max, vol_min, vol_max)
CAPAS = [(FILO, 1.35, 1.45, 0.50, 0.60),
         (MAGIA, 0.88, 0.94, 0.80, 0.90)]

RADIO, CAIDA = 2500.0, 6000.0

out = []
RASTRO = r"C:/Users/angel/AppData/Local/Temp/claude/D--Game-Projects-Unreal-DA-DarkAngelsPOC-5-8/b0f72002-3869-4e3b-ae7b-1d1121948fa2/scratchpad/rastro.txt"


def marca(t):
    """El print se pierde si el script muere; esto no."""
    try:
        with io.open(RASTRO, "a", encoding="utf-8") as f:
            f.write(t + chr(10))
    except Exception:
        pass


def prop(obj, nombre, valor):
    try:
        obj.set_editor_property(nombre, valor)
        return True
    except Exception as e:
        out.append("   OJO: %s.%s no cuela (%s)"
                   % (obj.get_class().get_name(), nombre, str(e)[:70]))
        return False


def cargar(ruta):
    return unreal.load_object(None, ruta + "." + ruta.split("/")[-1])


def crear(nombre, clase, factoria):
    ruta = CARPETA + "/" + nombre
    if unreal.EditorAssetLibrary.does_asset_exist(ruta):
        out.append("%s: ya existia" % nombre)
        return cargar(ruta)
    a = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        nombre, CARPETA, clase, factoria())
    out.append("%s: creado" % nombre)
    return a


def construir():
    if not unreal.EditorAssetLibrary.does_directory_exist(CARPETA):
        unreal.EditorAssetLibrary.make_directory(CARPETA)
        out.append("carpeta %s creada" % CARPETA)

    marca('A: atenuacion')
    att = crear(ATT, unreal.SoundAttenuation, unreal.SoundAttenuationFactory)
    a = att.get_editor_property("attenuation")
    prop(a, "attenuate", True)
    prop(a, "spatialize", True)
    prop(a, "falloff_distance", CAIDA)
    prop(a, "attenuation_shape_extents", unreal.Vector(RADIO, 0.0, 0.0))
    att.set_editor_property("attenuation", a)
    unreal.EditorAssetLibrary.save_asset(CARPETA + "/" + ATT)

    marca('B: cue')
    cue = crear(CUE, unreal.SoundCue, unreal.SoundCueFactoryNew)

    # El grafo, de abajo arriba. Cada capa lleva SU modulador para poder afinarla
    # por separado; el mezclador las suma; el atenuador manda sobre todo.
    marca('C: nodos')
    mezcla = unreal.new_object(unreal.SoundNodeMixer, outer=cue)
    hijos = []
    for ruta, pmin, pmax, vmin, vmax in CAPAS:
        onda = cargar(ruta)
        if onda is None:
            out.append("   FALTA la onda %s: esa capa NO entra" % ruta)
            continue
        reproductor = unreal.new_object(unreal.SoundNodeWavePlayer, outer=cue)
        prop(reproductor, "sound_wave_asset_ptr", onda)
        modulador = unreal.new_object(unreal.SoundNodeModulator, outer=cue)
        prop(modulador, "pitch_min", pmin)
        prop(modulador, "pitch_max", pmax)
        prop(modulador, "volume_min", vmin)
        prop(modulador, "volume_max", vmax)
        modulador.set_editor_property("child_nodes", [reproductor])
        hijos.append(modulador)
    mezcla.set_editor_property("child_nodes", hijos)
    # UNA ENTRADA DE VOLUMEN POR HIJO, O EL EDITOR SE MUERE. Ver la nota de arriba.
    prop(mezcla, "input_volume", [1.0] * len(hijos))

    marca('D: atenuador')
    atenuador = unreal.new_object(unreal.SoundNodeAttenuation, outer=cue)
    prop(atenuador, "attenuation_settings", att)
    atenuador.set_editor_property("child_nodes", [mezcla])

    marca('E: first_node')
    cue.set_editor_property("first_node", atenuador)
    marca('F: guardar cue')
    unreal.EditorAssetLibrary.save_asset(CARPETA + "/" + CUE)
    marca('G: guardado')


def releer():
    """El asset recargado, no el objeto que acabamos de tocar."""
    out.append("")
    out.append("RELEIDO:")
    cue = cargar(CARPETA + "/" + CUE)
    raiz = cue.get_editor_property("first_node")
    out.append("  first_node = %s" % (raiz.get_class().get_name() if raiz else None))
    if raiz is None:
        return
    mez = raiz.get_editor_property("child_nodes")
    out.append("  -> %s" % [n.get_class().get_name() for n in mez])
    if not mez:
        return
    for c in mez[0].get_editor_property("child_nodes"):
        w = c.get_editor_property("child_nodes")
        onda = w[0].get_editor_property("sound_wave_asset_ptr") if w else None
        out.append("     pitch %.2f-%.2f  vol %.2f-%.2f  onda = %s"
                   % (c.get_editor_property("pitch_min"),
                      c.get_editor_property("pitch_max"),
                      c.get_editor_property("volume_min"),
                      c.get_editor_property("volume_max"),
                      onda.get_name() if onda else "NINGUNA"))
    att = cargar(CARPETA + "/" + ATT)
    a = att.get_editor_property("attenuation")
    out.append("  atenuacion: radio=%s caida=%s activa=%s"
               % (a.get_editor_property("attenuation_shape_extents").x,
                  a.get_editor_property("falloff_distance"),
                  a.get_editor_property("attenuate")))


try:
    construir()
    releer()
except Exception:
    out.append("REVENTO:")
    out.append(traceback.format_exc())

print(chr(10).join(out))
