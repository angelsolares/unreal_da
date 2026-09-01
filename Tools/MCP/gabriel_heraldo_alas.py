# -*- coding: utf-8 -*-
import unreal

# Las alas del Gabriel heraldo: el del Elevador y el de Yesod despegan aleteando.
#
#     node ue.mjs py gabriel_heraldo_alas        <- CON PIE PARADO
#
# EL PROBLEMA. Los dos Gabriel que te paran a hablar --`Elev_Gabriel` y
# `Yesod_Gabriel`, hijos de `BP_DA_GabrielHeraldo`-- se van VOLANDO al terminar la
# conversacion (`SeVaAlHablar`: asciende `AlturaVuelo` y avanza `AvanceVuelo` en
# `SegundosVuelo`), pero no tenian alas. Un angel que asciende recto y desaparece,
# sin batir nada.
#
# ## DONDE ESTA CADA COSA, QUE NO ES OBVIO
#
# El heraldo NO es el que se ve. `BP_DA_GabrielHeraldo` hereda de
# `BP_DA_Interactuable` y es la CAJA de interaccion, con su camara y sus tres
# renglones de dialogo; su componente `Malla` esta VACIO. El cuerpo es un
# `SkeletalMeshActor` aparte --`<X>_Gabriel_Malla`, con `SK_DA_Gabriel` a escala
# 2,7 y `Anim_U_Idle` en AnimationSingleNode-- al que la caja apunta con la
# variable `Animado`, y es a ESE al que mueve y oculta el Tick. Por eso las alas
# cuelgan del cuerpo y no del heraldo.
#
# ## LAS ALAS SON UN ACTOR, NO UN COMPONENTE
#
# En los seis enemigos las alas son un componente del blueprint del personaje
# (`enemigos_alas`). Aqui no se puede: el cuerpo es un `SkeletalMeshActor`
# pelado colocado en el mapa. Asi que son un actor propio,
# `BP_DA_AlasHeraldo`, colgado del `SkeletalMeshComponent` de Gabriel en el socket
# `Alas`.
#
# **El socket se pone desde Python y con nombre**, `attach_to_component(malla,
# 'Alas', ...)`. La nota vieja de `enemigos_alas` --"el socket hay que
# asignarlo a mano, `AttachSocketName` no la expone el MCP"-- vale para el
# componente de un blueprint; para un ACTOR de nivel si se puede, y de un tiron.
#
# Medido: con la malla a 2,7 y las alas a 0,7 relativas, salen a 1,89 de escala de
# mundo y 406 de envergadura -- exactamente la misma proporcion cuerpo/alas que el
# Vigilante (1,8273 y 1,279). Y el transform de las alas respecto a `spine_05`
# sale identico al suyo: traslacion cero, pitch -90, escala 0,7.
#
# ## POR QUE LAS ALAS SE ANIMAN SOLAS Y NO SE LO DICE EL HERALDO
#
# `ABP_DA_Alas` --el AnimBP de las alas de los enemigos-- lee al portador con
# `TryGetPawnOwner` + `CastToCharacter`. Un `SkeletalMeshActor` no es un Pawn, asi
# que ese cast falla siempre y las alas se quedarian plegadas para siempre.
#
# En vez de cablear el heraldo (su EventGraph funciona y reescribirlo por DSL es el
# riesgo tonto: `write_graph_dsl` acumula nodos y el lector no lo delata),
# `BP_DA_AlasHeraldo` **se lo mira el mismo**: en cada Tick compara la Z de
# `GetAttachParentActor` con la del tick anterior. Si sube mas de `UmbralSubida`
# (0,5 uu) esta despegando -> `AS__AS_W5_flapping` en bucle y visible; si deja de
# subir -> `AS__AS_W5_idle_ground` y **se oculta**, que es justo cuando el heraldo
# oculta a Gabriel. Asi no depende de nada de fuera y no toca ningun grafo ajeno.
#
# Lo de ocultarse hace falta porque **`SetActorHiddenInGame` NO se propaga a los
# actores enganchados**: solo apaga los componentes del propio actor. Sin esto las
# alas se quedaban flotando a 2.600 de altura despues de que Gabriel desapareciera.
#
# ## VERIFICADO EN PIE (2026-09-01)
#
# Con el Master cargado, llamando al Tick de las alas a mano y subiendo a Gabriel
# 12,4 uu por tick (2.600 uu / 3,5 s a 60 fps):
#
#     reposo        gabZ=  -42.0 alasZ=  159.0 | Vol=False ocul=False | idle_ground
#     subiendo 1..4 gabZ= ->  7.6 alasZ= -> 208.6 | Vol=True  ocul=False | flapping
#     parado        gabZ=    7.6 alasZ=  208.6 | Vol=False ocul=True  | idle_ground
#
# Las alas siguen a Gabriel uu a uu (+49,6 = 4 x 12,4).
#
# ## LO QUE NO HACE ESTE GUION
#
# `BP_DA_AlasHeraldo` viaja en git; no se regenera aqui. Su EventGraph se escribio
# con `BlueprintTools.write_graph_dsl` (42 nodos, uno de cada) y sus dos
# animaciones van en variables `UAnimSequence` --`AnimAleteo` y `AnimPlegadas`--
# porque un asset no entra por literal en un pin de objeto.
#
# Tampoco crea el socket: `SkeletalMesh.add_socket` de Python pide un socket ya
# hecho, y el que lo crea de cero es `SkeletalMeshTools.add_socket` de Epic. Si
# falta, este guion para y dice la llamada exacta. Ya esta puesto y viaja en el
# .uasset de `SK_DA_Gabriel`, que si es nuestro.
#
# ## Y UNA TRAMPA DEL MCP QUE COSTO MEDIA HORA
#
# `execute_python_code` FALLA --"Python execution failed", sin traza-- si el
# codigo contiene en cualquier sitio, aunque sea en un comentario, un token con
# forma de fichero de Python (nombre + punto + p-y minuscula). Con mayusculas o
# con otra extension pasa. Por eso aqui los guiones hermanos se citan SIN
# extension. Los guiones viejos que se citan a si mismos con extension en la
# cabecera ya no se pueden mandar enteros por esta via.

MALLA_GABRIEL = "/Game/DarkAngels/Characters/Bosses/SK_DA_Gabriel"
ALAS_BP = "/Game/DarkAngels/Blueprints/Alas/BP_DA_AlasHeraldo.BP_DA_AlasHeraldo_C"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"

HUESO = "spine_05"
SOCKET = "Alas"
# La malla de Gabriel va a 2,7 y estas a 0,7 de ella: 1,89 de mundo, 406 de
# envergadura. Misma proporcion que el Vigilante (1,8273 x 0,7).
ESCALA = 0.7

SITIOS = [
    {"mapa": "/Game/DarkAngels/Maps/L_DA_Malkuth_Elevador_Sub",
     "cuerpo": "Elev_Gabriel_Malla", "alas": "Elev_Gabriel_Alas"},
    {"mapa": "/Game/DarkAngels/Maps/L_DA_Malkuth_Yesod_Sub",
     "cuerpo": "Yesod_Gabriel_Malla", "alas": "Yesod_Gabriel_Alas"},
]


def socket_en_la_espalda(out):
    """El socket vive en la MALLA, no en el esqueleto: el del GiantBoss es de pago."""
    malla = unreal.load_asset(MALLA_GABRIEL)
    if malla.find_socket(SOCKET) is None:
        # `SkeletalMesh.add_socket` de Python pide un objeto socket ya hecho; el
        # que crea uno de cero es el toolset de Epic.
        raise RuntimeError(
            "falta el socket '%s' en %s: crearlo con "
            "SkeletalMeshTools.add_socket(mesh, '%s', '%s')" % (SOCKET, MALLA_GABRIEL, SOCKET, HUESO))
    s = malla.find_socket(SOCKET)
    out["socket"] = {"hueso": str(s.get_editor_property("bone_name")),
                     "loc": [getattr(s.get_editor_property("relative_location"), k) for k in "xyz"]}


def por_etiqueta(nombre):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == nombre:
            return a
    return None


def colgar(sitio, out):
    lvl = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    lvl.load_level(sitio["mapa"])
    d = {"mapa": sitio["mapa"].split("/")[-1]}

    cuerpo = por_etiqueta(sitio["cuerpo"])
    if cuerpo is None:
        d["error"] = "no esta " + sitio["cuerpo"]
        out["sitios"].append(d)
        return

    alas = por_etiqueta(sitio["alas"])
    if alas is None:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        alas = eas.spawn_actor_from_class(unreal.load_class(None, ALAS_BP),
                                          cuerpo.get_actor_location(),
                                          cuerpo.get_actor_rotation())
        alas.set_actor_label(sitio["alas"])
        d["actor"] = "creado"
    else:
        d["actor"] = "ya estaba"

    malla = cuerpo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    R = unreal.AttachmentRule
    alas.attach_to_component(malla, SOCKET, R.SNAP_TO_TARGET, R.SNAP_TO_TARGET,
                             R.KEEP_RELATIVE, False)
    raiz = alas.get_editor_property("root_component")
    raiz.set_editor_property("relative_scale3d", unreal.Vector(ESCALA, ESCALA, ESCALA))
    # Sin esto la raiz se queda con el ComponentToWorld viejo y la relectura
    # miente (los hijos si se actualizan, la raiz no).
    alas.set_actor_location(alas.get_actor_location(), False, False)

    # --- releer, que el editor miente en las dos direcciones ---
    E = unreal.RelativeTransformSpace
    comp = alas.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    rel = unreal.MathLibrary.make_relative_transform(
        comp.get_world_transform(), malla.get_socket_transform(HUESO, E.RTS_WORLD))
    caja = alas.get_actor_bounds(False)
    d["colgado_de"] = "%s @ %s" % (alas.get_attach_parent_actor().get_actor_label(),
                                   alas.get_attach_parent_socket_name())
    d["rel_a_" + HUESO] = {"loc": [round(getattr(rel.translation, k), 3) for k in "xyz"],
                           "rot": [round(v, 1) for v in (rel.rotation.rotator().roll,
                                                         rel.rotation.rotator().pitch,
                                                         rel.rotation.rotator().yaw)],
                           "esc": round(rel.scale3d.x, 3)}
    d["envergadura"] = round(caja[1].y * 2.0, 1)
    d["escala_mundo"] = round(alas.get_actor_scale3d().x, 3)

    d["guardado"] = unreal.EditorAssetLibrary.save_asset(sitio["mapa"], False)
    out["sitios"].append(d)


def run():
    if unreal.EditorLevelLibrary.is_playing_in_editor() if hasattr(
            unreal.EditorLevelLibrary, "is_playing_in_editor") else False:
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}
    out = {"sitios": []}
    socket_en_la_espalda(out)
    for s in SITIOS:
        colgar(s, out)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAESTRO)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, ensure_ascii=False))
