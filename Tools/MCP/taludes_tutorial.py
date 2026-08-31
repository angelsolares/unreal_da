"""Da colision a los dos monticulos del sendero del Jardin, para que ensenen a
esquivar y a saltar antes de que haya nada que pueda matarte.

POR QUE UN SCRIPT: las mallas SM_DA_Talud_* son COPIAS de Megascans, y
Content/Megascans/ esta excluido del repo (licencia de Fab). Igual que
BT_DA_Guerrero, se excluyen del repo y se regeneran desde aqui. Lo que SI se
sube es el nivel, que ya las referencia.

EL DEFECTO: los MossyEmbankment de Megascans traen **cero primitivas de colision
simple**. El personaje se mueve contra la colision SIMPLE, asi que los atravesaba
aunque el perfil dijera BlockAll. Se comprueba con una traza de complex=False:
sobre un talud sin tocar responde el suelo de detras, no el talud.

POR QUE UNA COPIA Y NO ARREGLAR LA MALLA: esas cinco mallas tienen cientos de
instancias repartidas por los ocho mapas de Malkuth. Tocar el asset las volveria
solidas todas de golpe, y ademas el cambio no viajaria en el repo. La copia deja
el radio de accion en exactamente dos actores.

POR QUE COMPLEX_AS_SIMPLE Y NO DESCOMPOSICION CONVEXA: son dos actores estaticos,
2.000 triangulos cada uno. La colision exacta no cuesta nada aqui y evita el
clasico muro invisible de los cascos convexos.

LOS NUMEROS (medidos, no supuestos). Malakh sube escalones de 45 uu, pendientes
de hasta 44,8 grados, y su salto llega a 184 uu (600^2 / 2*980):
  - Talud_003, LA ESQUIVA: corta el carril derecho del sendero con 53 uu de
    frente y deja libre el centro. No se toca: subirlo 40 sellaba el paso, porque
    SM_Arbol_Primer_Plano ya tapa los carriles de la izquierda.
  - Talud_011, EL SALTO: cruzaba el sendero entero pero solo levantaba 40-42 uu,
    o sea POR DEBAJO del escalon de 45: se subia andando. Subido 20 uu pide 50 de
    elevacion y cierra los tres carriles. Se salta de sobra.
El monticulo esta enterrado 475 uu bajo el cesped, asi que subirlo 20 no le
levanta el faldon.

Ejecutar con:  node ue.mjs py taludes_tutorial
"""

import unreal

MAPA = "/Game/DarkAngels/Maps/L_DA_Malkuth_Jardin_Sub"
DEST = "/Game/DarkAngels/Environment/Props"

#: actor -> (malla de origen, copia con colision, z ABSOLUTA a la que debe quedar)
#: La z va en absoluto a proposito: un "+20" relativo se aplicaria otra vez en
#: cada pasada y el monticulo acabaria flotando.
TALUDES = {
    "Jardin_Talud_003": ("/Game/Megascans/3D_Assets/MossyEmbankmentA/SM_MossyEmbankmentA_00",
                         DEST + "/SM_DA_Talud_Esquiva", -66.51),
    "Jardin_Talud_011": ("/Game/Megascans/3D_Assets/MossyEmbankmentB/SM_MossyEmbankmentB",
                         DEST + "/SM_DA_Talud_Salto",   -350.90),
}


def copiar():
    """Duplica las mallas y les pone colision exacta. Idempotente."""
    eal = unreal.EditorAssetLibrary
    for orig, nuevo, _ in TALUDES.values():
        if not eal.does_asset_exist(nuevo):
            assert eal.duplicate_asset(orig, nuevo), "no pude duplicar %s" % orig
        m = eal.load_asset(nuevo)
        bs = m.get_editor_property("body_setup")
        bs.set_editor_property("collision_trace_flag",
                               unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        m.set_editor_property("body_setup", bs)
        eal.save_asset(nuevo)
        # se relee del disco: el save devuelve True sin haber escrito
        leido = eal.load_asset(nuevo).get_editor_property("body_setup")
        ok = (leido.get_editor_property("collision_trace_flag")
              == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        print("   %-32s %s" % (nuevo.split("/")[-1], "OK" if ok else "*** NO CUAJO ***"))


def colocar():
    """Apunta los dos actores a las copias y fija la altura. Idempotente."""
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert not les.is_in_play_in_editor(), "PIE vivo: los listados mienten"
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mundo = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert mundo.get_name() == MAPA.split("/")[-1], "abre antes %s" % MAPA

    porNombre = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    for lab, (_, nuevo, z) in TALUDES.items():
        a = porNombre[lab]
        c = a.static_mesh_component
        c.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(nuevo))
        c.set_collision_profile_name("BlockAll")
        L = a.get_actor_location()
        a.set_actor_location(unreal.Vector(L.x, L.y, z), False, True)
        m = c.get_editor_property("static_mesh")
        print("   %-18s malla=%-22s z=%9.2f" % (lab, m.get_name(), a.get_actor_location().z))
    print("   guardado:", les.save_current_level())


def verificar():
    """Traza con complex=False -- la colision que siente de verdad el personaje."""
    print("\n--- verificacion: quien responde a la traza SIMPLE ---")
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    porNombre = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    bien = 0
    for lab in TALUDES:
        a = porNombre[lab]
        o, e = a.get_actor_bounds(False)
        h = unreal.SystemLibrary.line_trace_single(
            w, unreal.Vector(o.x, o.y, o.z + e.z + 200), unreal.Vector(o.x, o.y, o.z - e.z - 200),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
        d = h.to_dict() if h else None
        act = d["hit_actor"] if d and d["blocking_hit"] else None
        quien = act.get_actor_label() if act else "NADA"
        # el 011 esta enterrado en su propio centro: ahi manda el Landscape, y es correcto
        ok = quien in (lab, "Landscape")
        bien += ok
        print("   %-18s -> %-22s %s" % (lab, quien, "OK" if ok else "*** SIGUE SIN COLISION ***"))
    return bien == len(TALUDES)


if __name__ == "__main__":
    copiar()
    colocar()
    verificar()
