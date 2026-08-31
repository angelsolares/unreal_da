"""Asigna a cada BP_DA_ZoneTrigger su musica y su ambiente.

POR QUE POR INSTANCIA Y NO EN CODIGO: asi se cambia la pista de una zona desde
el panel de detalles, sin tocar un grafo. El precio es que **siete de los doce
disparadores viven dentro de submapas**, asi que hay que abrirlos uno a uno --de
ahi este script, que hace la pasada sola.

CRITERIO DEL REPARTO: hay 4 musicas para 12 zonas, asi que van por tramo, no por
sala; cortar la pista en cada puerta destrozaria la continuidad. El ambiente si
distingue: cada uno se pega al sitio que describe --la casa herida a las ruinas,
la fuente seca al santuario, la lluvia celestial al puente.

Ejecutar con:  node ue.mjs py audio_zonas   (una vez por mapa abierto)
"""

import unreal

MUS = "/Game/DarkAngels/Audio/Musica/%s"
AMB = "/Game/DarkAngels/Audio/Ambiente/%s"

#: zona -> (musica, ambiente). La clave es el ZoneName tal cual lo muestra el HUD.
REPARTO = {
    "Jardin Geometrico":    ("MUS_Jardin", "AMB_GardenBreath"),
    "Mirador de Sariel":    ("MUS_Jardin", "AMB_StoneWind"),
    "El Claro":             ("MUS_Jardin", "AMB_GardenBreath"),
    "Ruinas del Gazebo":    ("MUS_Umbral", "AMB_WoundedHouse"),
    "Santuario de Malkuth": ("MUS_Umbral", "AMB_DryFountainVoices"),
    "Puente Ascendente":    ("MUS_Lluvia_Estandarte", "AMB_CelestialRain"),
    "Anfiteatro":           ("MUS_Lluvia_Estandarte", "AMB_StoneWind"),
    "Elevador del Trono":   ("MUS_Tribunal", "AMB_StoneWind"),
    "Gabriel - Camara I":   ("MUS_Tribunal", "AMB_TribunalScale"),
    "Segundo Circulo":      ("MUS_Tribunal", "AMB_TribunalScale"),
    "Gabriel - Camara III": ("MUS_Tribunal", "AMB_TribunalScale"),
    "Portal a Yesod":       ("MUS_Umbral", "AMB_CelestialRain"),
}

#: Los ocho mapas que contienen disparadores.
MAPAS = [
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Master",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Gazebo_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Puente_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Elevador_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_GabrielC1_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_GabrielC3_Sub",
    "/Game/DarkAngels/Maps/L_DA_Malkuth_Yesod_Sub",
]


def aplicar():
    """Rellena los disparadores del mapa ABIERTO. Idempotente."""
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert not les.is_in_play_in_editor(), "PIE vivo: los listados mienten"
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mundo = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    tocados, sin_receta = 0, []
    for a in eas.get_all_level_actors():
        if not a.get_class().get_name().startswith("BP_DA_ZoneTrigger"):
            continue
        zona = str(a.get_editor_property("ZoneName"))
        if zona not in REPARTO:
            sin_receta.append(zona)
            continue
        mus, amb = REPARTO[zona]
        a.set_editor_property("Musica", unreal.EditorAssetLibrary.load_asset(MUS % mus))
        a.set_editor_property("Ambiente", unreal.EditorAssetLibrary.load_asset(AMB % amb))
        # se relee del actor, que el set no avisa si no cuaja
        m = a.get_editor_property("Musica")
        n = a.get_editor_property("Ambiente")
        ok = m is not None and n is not None
        print("   %-22s %-24s %-24s %s" % (zona, m.get_name() if m else "-",
                                           n.get_name() if n else "-",
                                           "OK" if ok else "*** NO CUAJO ***"))
        tocados += 1 if ok else 0

    print("%s: %d disparadores puestos%s" % (
        mundo.get_name(), tocados,
        ("  | sin receta: %s" % sin_receta) if sin_receta else ""))
    if tocados:
        print("   guardado:", les.save_current_level())
    return tocados
