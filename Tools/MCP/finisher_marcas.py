import unreal
import json
# -*- coding: utf-8 -*-
#
# OJO: `import unreal` va en la PRIMERA linea. execute_python_code lo valida
# y el runner falla con un escueto "Python execution failed" si no lo ve.
#
# REAPLICA LAS MARCAS DE LOS FINISHERS DESDE `finisher_marcas.json`.
#
#   Se lanza desde Tools/MCP con:   node ue.mjs py finisher_marcas
#
# OJO al modo del runner: **py, no script**. `ue.mjs script` corre en el sandbox
# de la ProgrammaticToolset, que solo deja importar re/json/time/math/datetime/copy
# y NO tiene el modulo `unreal`. `ue.mjs py` va por execute_python_code, con la API
# entera. Lanzarlo con `script` muere con "Import of os is not permitted".
#
# ### POR QUE EXISTE ESTO
#
# `Content/DarkAngels/Animations/` esta en el `.gitignore`: los 40 montages son
# assets DERIVADOS del Sword Takedown Pack, que es de pago, y el repo es publico.
# Asi que el trabajo caro de esos montages --20 sacudidas y 26 encuadres de
# camara, sacados midiendo animacion fotograma a fotograma-- vivia SOLO en el
# disco de Angel. Un formateo, o reinstalar el pack desde Fab, y se perdia.
#
# Esto lo arregla sin subir un solo asset de pago: los numeros viven en un JSON
# de 12 KB que si esta en git, y este script los vuelve a poner.
#
# **Cubre mas que un `.uasset` commiteado.** Reinstalar el pack desde Fab borra
# la reasignacion de esqueleto y deja los montages inservibles, y eso un binario
# en git NO lo arregla, porque lo que se pierde vive en `Content/Sword_Takedown/`,
# que esta ignorado. Lo que NO cubre son las 40 cascaras de montage: crearlas es
# `Create -> Create AnimMontage` y cambiar el slot a `FullBody`, tedioso pero
# mecanico y sin criterio. El criterio esta aqui.
#
# ### ES IDEMPOTENTE
#
# Antes de anadir nada mira si ya hay una marca de esa clase a menos de 10 ms.
# Se puede relanzar sin miedo: la segunda pasada no duplica.
#
# ### LAS DOS TRAMPAS QUE COSTARON LA PRIMERA VEZ
#
# 1. **`AnimSequenceService` es el servicio EQUIVOCADO para un montage**:
#    `list_notifies` devuelve `[]` y `get_notify_info` devuelve `None`, sin
#    fallar. El bueno es `AnimMontageService`.
# 2. **El listado de avisos da tiempos sin propiedades, y los objetos dan
#    propiedades sin tiempo.** No hay forma de casarlos. Por eso, para escribir
#    los valores de una camara recien creada, hay que fotografiar los nombres de
#    objeto ANTES y DESPUES de `add_notify` y quedarse con el que aparece.
#
# Y ojo: si `add_notify` devuelve -1, el servicio puede quedarse sin poder releer
# ESE montage el resto de la sesion (se recupera solo al rato). No es corrupcion:
# el asset no se ensucia siquiera.


# `__file__` no existe al ejecutarse por execute_python_code: la ruta se saca
# del proyecto, que es lo unico fijo.
JSON = (unreal.SystemLibrary.get_project_directory()
        + "Tools/MCP/finisher_marcas.json")

SACUDIDA = ("/Game/DarkAngels/Blueprints/Combat/BP_DA_NotifySacudida"
            ".BP_DA_NotifySacudida_C")
CAMARA = ("/Game/DarkAngels/Blueprints/Combat/BP_DA_NotifyCamara"
          ".BP_DA_NotifyCamara_C")
CAMPOS = ("Lado", "Frente", "Alto", "Mira", "FOV", "Desfase")
EPS = 0.01          # dos marcas a menos de 10 ms son la misma marca


def _objetos(montage, base):
    """Los objetos de aviso de una clase, alcanzables por nombre.

    El array `Notifies` esta protegido en Python y `ObjectTools` tampoco lo lee;
    esta es la unica via."""
    out = {}
    for i in range(40):
        o = unreal.find_object(montage, "%s_%d" % (base, i))
        if o is not None:
            out[o.get_name()] = o
    return out


def _ya_esta(avisos, clase, t):
    return any(clase in str(a.notify_class) and abs(a.trigger_time - t) < EPS
               for a in avisos)


def aplicar(ruta_json=JSON):
    cfg = json.load(open(ruta_json, encoding="utf-8"))
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    informe = {}

    for clave, d in sorted(cfg["takedowns"].items()):
        p = d["montage"]
        if not eas.does_asset_exist(p):
            informe[clave] = "FALTA EL MONTAGE (¿pack sin instalar?)"
            continue
        m = unreal.load_asset(p)
        puestas, saltadas, fallos = 0, 0, []

        # --- sacudidas: no llevan parametros, la clase incrusta CS_DA_Finisher
        for t in d["sacudidas"]:
            if _ya_esta(unreal.AnimMontageService.list_notifies(p), "Sacudida", t):
                saltadas += 1
                continue
            if unreal.AnimMontageService.add_notify(p, SACUDIDA, t, "Sacudida") < 0:
                fallos.append("sacudida t=%.3f" % t)
            else:
                puestas += 1

        # --- camaras: hay que escribirles los seis numeros despues de crearlas
        for c in d["camara"]:
            t = c["t"]
            if _ya_esta(unreal.AnimMontageService.list_notifies(p), "NotifyCamara", t):
                saltadas += 1
                continue
            antes = set(_objetos(m, "BP_DA_NotifyCamara_C"))
            if unreal.AnimMontageService.add_notify(p, CAMARA, t, "Camara") < 0:
                fallos.append("camara t=%.3f" % t)
                continue
            nuevos = _objetos(m, "BP_DA_NotifyCamara_C")
            recien = [n for n in nuevos if n not in antes]
            if not recien:
                fallos.append("camara t=%.3f creada pero no la encuentro" % t)
                continue
            o = nuevos[recien[0]]
            for campo in CAMPOS:
                o.set_editor_property(campo, float(c[campo]))
            puestas += 1

        eas.save_asset(p, only_if_is_dirty=False)

        # --- relectura: aqui el `true` miente, asi que se cuenta lo que quedo
        av = unreal.AnimMontageService.list_notifies(p)
        informe[clave] = {
            "puestas": puestas, "ya_estaban": saltadas,
            "sacudidas": sum(1 for a in av if "Sacudida" in str(a.notify_class)),
            "esperadas_sac": len(d["sacudidas"]),
            "camaras": sum(1 for a in av if "NotifyCamara" in str(a.notify_class)),
            "esperadas_cam": len(d["camara"]),
        }
        if fallos:
            informe[clave]["FALLOS"] = fallos

    return informe


def comprobar(ruta_json=JSON):
    """Sin escribir nada: dice que falta respecto al JSON."""
    cfg = json.load(open(ruta_json, encoding="utf-8"))
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    out = {}
    for clave, d in sorted(cfg["takedowns"].items()):
        p = d["montage"]
        if not eas.does_asset_exist(p):
            out[clave] = "FALTA EL MONTAGE"
            continue
        av = unreal.AnimMontageService.list_notifies(p)
        faltan = [t for t in d["sacudidas"] if not _ya_esta(av, "Sacudida", t)]
        faltan += [c["t"] for c in d["camara"] if not _ya_esta(av, "NotifyCamara", c["t"])]
        out[clave] = "al dia" if not faltan else "faltan %d marcas: %s" % (
            len(faltan), [round(t, 3) for t in faltan])
    return out


resultado = aplicar()
print("--- APLICAR ---")
for k in sorted(resultado):
    print(" ", k, resultado[k])
print("--- COMPROBAR ---")
for k, v in sorted(comprobar().items()):
    print(" ", k, v)
