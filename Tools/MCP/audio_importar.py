"""Trae a Dark Angels el audio generado para DAShadowGate y lo importa.

POR QUE UN SCRIPT: los .mp3 de origen viven en otro proyecto y fuera de este
repo, y Unreal **no importa mp3**. Hay que convertir a wav primero. Dejarlo
escrito hace la operacion repetible cuando lleguen piezas nuevas.

QUE SE TRAE Y QUE NO: las 4 musicas y los 6 ambientes son del mismo mundo y
valen tal cual. De los 30 efectos solo vienen los que tienen un suceso REAL en
este juego. Los diez verbos --observar, tomar, usar...-- son de aventura
grafica: aqui no existe ese vocabulario y no sonarian jamas, asi que se quedan
fuera a proposito.

Ejecutar con:  node ue.mjs py audio_importar
"""

import os
import subprocess

import unreal

FFMPEG = r"C:/ffmpeg/ffmpeg-master-latest-win64-gpl-shared/bin/ffmpeg.exe"
ORIGEN = r"D:/Game Projects/DAShadowGate/da-shadow-gate/audio"
TEMP = r"C:/Users/angel/AppData/Local/Temp/da_audio_wav"

DESTINO = "/Game/DarkAngels/Audio"
CARPETAS = {"music": DESTINO + "/Musica",
            "ambient": DESTINO + "/Ambiente",
            "sfx": DESTINO + "/SFX"}

#: Musica y ambiente entran enteros; ciclan, asi que van marcados para bucle.
MUSICA = ["MUS_Umbral", "MUS_Jardin", "MUS_Lluvia_Estandarte", "MUS_Tribunal"]
AMBIENTE = ["AMB_StoneWind", "AMB_GardenBreath", "AMB_DryFountainVoices",
            "AMB_WoundedHouse", "AMB_CelestialRain", "AMB_TribunalScale"]

#: Solo los efectos con un suceso real en Dark Angels. Al lado, donde suena.
SFX = {
    "room_enter":        "BP_DA_ZoneTrigger.FireZoneEntry",
    "item_gained":       "BP_DA_DroppedWeapon.Interact",
    "door_open":         "la puerta del Claro y el ENTER del titulo",
    "choice_grace":      "BP_DA_Decision, eje Gracia",
    "choice_corruption": "BP_DA_Decision, eje Corrupcion",
    "choice_will":       "BP_DA_Decision, eje Voluntad",
    "mark_awarded":      "al conceder la Marca",
    "rain_pulse":        "el pulso de los picos del Puente",
    "scale_tip":         "la balanza de Gabriel",
}


def convertir():
    """mp3 -> wav 44.1 kHz 16 bits, que es lo que Unreal traga."""
    assert os.path.isfile(FFMPEG), "no encuentro ffmpeg en %s" % FFMPEG
    os.makedirs(TEMP, exist_ok=True)
    hechos = []
    for sub, nombres in (("music", MUSICA), ("ambient", AMBIENTE), ("sfx", list(SFX))):
        for n in nombres:
            src = os.path.join(ORIGEN, sub, n + ".mp3")
            if not os.path.isfile(src):
                print("   FALTA el origen:", src)
                continue
            dst = os.path.join(TEMP, n + ".wav")
            r = subprocess.run([FFMPEG, "-y", "-loglevel", "error",
                                "-i", src, "-ar", "44100", "-ac", "2",
                                "-c:a", "pcm_s16le", dst],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.isfile(dst):
                print("   ERROR convirtiendo %s: %s" % (n, r.stderr[:120]))
                continue
            hechos.append((sub, n, dst))
    print("convertidos: %d" % len(hechos))
    return hechos


def importar(hechos):
    tareas = []
    for sub, n, wav in hechos:
        t = unreal.AssetImportTask()
        t.filename = wav
        t.destination_path = CARPETAS[sub]
        t.destination_name = n
        t.automated = True
        t.replace_existing = True
        t.save = True
        tareas.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tareas)

    # El bucle NO viene del importador: hay que marcarlo despues, o la musica se
    # corta a los 45 s y la zona se queda muda.
    ok = 0
    for sub, n, _ in hechos:
        ruta = "%s/%s" % (CARPETAS[sub], n)
        a = unreal.EditorAssetLibrary.load_asset(ruta)
        if not a:
            print("   NO importo:", ruta)
            continue
        if sub in ("music", "ambient"):
            a.set_editor_property("looping", True)
        unreal.EditorLoadingAndSavingUtils.save_packages([a.get_outermost()], False)
        ok += 1
    print("importados y guardados: %d" % ok)
    return ok


def verificar():
    """Relee del disco: el `save` del importador no prueba nada por si solo."""
    print("\n--- verificacion ---")
    total = 0
    for sub, nombres in (("music", MUSICA), ("ambient", AMBIENTE), ("sfx", list(SFX))):
        for n in nombres:
            ruta = "%s/%s" % (CARPETAS[sub], n)
            a = unreal.EditorAssetLibrary.load_asset(ruta)
            if not a:
                print("   FALTA %s" % ruta)
                continue
            dur = a.get_editor_property("duration")
            loop = a.get_editor_property("looping")
            print("   %-9s %-26s %6.2f s  bucle=%s" % (sub, n, dur, loop))
            total += 1
    print("total en el proyecto: %d" % total)
    return total


if __name__ == "__main__":
    importar(convertir())
    verificar()
