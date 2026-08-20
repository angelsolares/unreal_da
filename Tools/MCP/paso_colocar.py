# -*- coding: utf-8 -*-
import json

# Coloca el primer par de `BP_DA_Paso` de Malkuth: la puerta de bronce de El
# Claro. Lanzar DESPUES de `paso_verbo.py` y `paso_crear.py`.
#
# ### LA GEOMETRIA, MEDIDA -- NO COPIADA DE LAS NOTAS
#
# Todo lo de abajo sale de `trace_world` y `get_actor_bounds` sobre el submapa
# abierto suelto, que es donde los actores estan en **coordenadas del submapa**:
# la Level Instance del maestro les suma su offset. Escribir aqui numeros leidos
# en el maestro manda el actor a decenas de km.
#
#   - El hueco norte del anillo **esta sellado**, y no lo sella quien parece.
#     `Claro_Puerta_Bronce` --la de Tripo, la que se ve-- **no tiene colision**:
#     una traza horizontal por el eje pasa de largo a z=800, 1000 y 1200, aunque
#     su malla llegue a z=1280. Quien tapa es **`Claro_Puerta_Ruta`**, la puerta
#     modular vieja, que quedo *oculta pero no borrada* y conserva
#     `QueryAndPhysics`. El bloqueo se acaba **exactamente en z=753**, que es su
#     techo. Con el jugador de pie en el rellano (pies a 182, cabeza a ~374) se
#     esta muy por debajo: no se pasa. Es el caso de manual de que `bHidden` no
#     quita la colision.
#   - Al sur de la puerta se sube por `Claro_Escalera`: el suelo va de z=43 en
#     y=2400 a z=183 en y=3000. La cota del rellano es **~182**, no los 232 que
#     dan los bounds --los bounds son la caja del mesh entero, la traza es la
#     superficie que se pisa--.
#   - Al norte, pasada la puerta, hay un pasillo estrecho entre los acantilados
#     exteriores que se abre hacia el este. **No es una llanura**, aunque las
#     primeras trazas lo dijeran; ver mas abajo.
#
# ### VAN DOS PASOS, NO UNO
#
# El de ida tiene su gemelo de vuelta para que cruzar no sea un billete de ida:
# la puerta sigue sin dejar pasar andando en ninguno de los dos sentidos, asi
# que sin el de vuelta habria que reiniciar el nivel para seguir probando -- y
# probar ANDANDO es justo lo que pide la nota del salto de zona.
#
# ### LOS DESTINOS SON `TargetPoint` Y SU YAW IMPORTA
#
# `CruzarPaso` copia el yaw del actor `Destino` al pawn Y al controlador. Aqui:
# el de ida mira al norte (yaw 90), que es hacia donde ibas; el de vuelta mira
# al sur (yaw -90), hacia el claro. Sin esto reapareces mirando a donde mirabas
# antes de pulsar.
#
# La Z de un destino **no es la del suelo**: el origen de un Character es el
# centro de la capsula, o sea el suelo + 96. Es el mismo `+96` que ya se pago
# colocando los enemigos de El Claro.
#
# ### DOS DE LAS TRES SALIDAS DE SARIEL YA LLEGAN AQUI
#
# La decision del Mirador tiene tres, y la puerta de El Claro es donde se cobran:
#
#   1 ORDEN     "Que abras tu la puerta. Es tu oficio."       -> Sariel se disuelve
#      y reaparece junto a la puerta, y la abre el. **POR MONTAR.**
#   2 FURIA     "Arrebatarle la llave."                       -> `Requisito`, cruza
#      directo. El cartel dice "Cruzar".
#   3 NEGACION  "Nadie deberia tener que custodiar una puerta" -> `RequisitoForzar`,
#      el cartel dice "Forzar" y la E revienta el sello. Su propia revelacion lo
#      anuncia: *"El cerrojo sigue en su sitio. Tendras que vertelas tu con el."*
#
# Las dos se leen del **historico de Marcas**, no de flags, y por eso ninguna
# obligo a tocar `BP_DA_Decision`. El porque esta en `paso_verbo.py`.
#
# Forzar deja `CLARO_PUERTA_ABIERTA` en el GameState, y a partir de ahi la puerta
# esta abierta para siempre y en los dos sentidos. **Ese es el sitio definitivo
# del cerrojo**: cuando ORDEN tambien exista, lo suyo es que las tres terminen
# marcando ese mismo flag y que `REQUISITO` pase a ser el flag en vez de `FURIA`.
# No hay que tocar nada mas --`Lleva` ya mira en los dos almacenes--: es cambiar
# una cadena de aqui.
#
# Mientras ORDEN no exista, elegirla deja al jugador plantado en El Claro. No es
# un agujero de guion, es trabajo pendiente.
#
# ### EL FLAG DE IDA SI, EL DE VUELTA NO
#
# `CLARO_PUERTA_CRUZADA` queda en el GameState en cuanto se cruza, y de ahi lo
# puede leer cualquiera --el Debug HUD, una linea de Gabriel, un `BP_DA_Decision`
# que solo aparezca si has estado detras de la puerta--. La vuelta no apunta
# nada: `FlagPaso` vacio esta contemplado y no escribe.
#
# ### DONDE CAEN LAS PIEZAS DEL NORTE: MEDIDO, NO ELEGIDO
#
# El primer intento puso el destino en el eje de la puerta a y=3800 creyendo que
# detras habia llanura. No la hay: **`Claro_Cliff_Out_2` y `Out_3`, las piezas
# del anillo EXTERIOR, cierran a 250-600 uu de la hoja**, y el eje esta tapado a
# la altura del cuerpo entre y≈3600 y y≈3700.
#
# El error de metodo fue fiarse de trazas hacia abajo desde muy arriba: pasan por
# DEBAJO de los salientes y encuentran suelo, asi que un pasillo de roca se lee
# como campo abierto. Lo que si sirve es una rejilla que, en cada celda, ademas
# del suelo comprueba que **cabe un jugador de pie y que hay 200 uu libres a los
# cuatro lados**. Con eso sale el hueco de verdad: se abre a partir de y≈3500 y
# corrido al ESTE del eje, entre x 8550 y 9050.
#
# Eso son cotas de sitio libre, no una ruta. La ruta la contesto despues
# `probe_camino.py`, que busca camino de celda en celda: **del sitio donde
# aterrizas al corredor del Santuario SI se va andando** --12 celdas, todas a
# z=-42, sin un solo escalon--. Se sale al oeste hasta x=44250 y luego recto al
# norte. Sigue sin ser un NavMesh horneado, pero ya no es una suposicion.

SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Claro_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CLASE = "/Game/DarkAngels/Blueprints/Level/BP_DA_Paso.BP_DA_Paso_C"
DESTINO = "/Script/Engine.TargetPoint"
CARPETA = "Claro/Puerta"

EJE = 8245.0          # eje de la abertura norte, medido
CAPSULA = 96.0        # medio alto de la capsula del jugador

FLAG_CRUZADA = "CLARO_PUERTA_CRUZADA"
FLAG_ABIERTA = "CLARO_PUERTA_ABIERTA"
REQUISITO = "FURIA"      # la Marca de arrebatarle la llave a Sariel
FORZAR = "NEGACION"      # la Marca de negar que la puerta signifique nada

# El montage es un placeholder RAZONADO, no el definitivo: `M_UC_HeavyAttack` es
# el golpe fuerte **desarmado** de DCS, y se eligio precisamente por eso --se ve
# igual de bien lleves espada envainada o no, que es lo que no se puede dar por
# supuesto al llegar a esta puerta--. Cambiarlo es un desplegable en la instancia.
# Si se cambia, hay que recuadrar `EsperaForzar`.
MONTAGE = ("/Game/DynamicCombatSystem/DCS/Animations/UnarmedCombat/Montages/"
           "Player/M_UC_HeavyAttack.M_UC_HeavyAttack")
# Idem el VFX: `NS_EmbersLarge` es del pack gratuito de efectos, y lee como
# chispas saltando del sello. Es un NiagaraSystem, comprobado con get_asset_class.
VFX = "/Game/Effects/Embers/NS_EmbersLarge.NS_EmbersLarge"

# (etiqueta, x, y, yaw, es_paso, destino, props)
# La Z no se escribe: se mide con una traza al colocar. Ver `apoyar`.
#
# `FlagAbierta` va en LOS DOS: es la constancia de que la puerta ya esta
# franqueada, y una vez puesta abre en los dos sentidos, sin importar como se
# gano. `RequisitoForzar` solo en el de ida: por dentro no se fuerza nada, se
# vuelve por una puerta que ya esta abierta.
PIEZAS = [
    ("Destino_TrasPuerta",       8675.0, 3750.0,  90.0, False, None, {}),
    ("Destino_AntePuerta",         EJE,  2850.0, -90.0, False, None, {}),
    # el de ida: pegado a la cara sur de la puerta, sobre el rellano
    ("Paso_Puerta_Claro",          EJE,  3020.0,   0.0, True, "Destino_TrasPuerta",
     {"Requisito": REQUISITO, "FlagPaso": FLAG_CRUZADA, "FlagAbierta": FLAG_ABIERTA,
      "RequisitoForzar": FORZAR, "MontageForzar": MONTAGE, "VfxForzar": VFX}),
    # el de vuelta: en el hueco del este, a 280 uu de donde aterrizas
    ("Paso_Puerta_Claro_Vuelta", 8800.0, 3500.0,   0.0, True, "Destino_AntePuerta",
     {"Requisito": REQUISITO, "FlagPaso": "", "FlagAbierta": FLAG_ABIERTA,
      "RequisitoForzar": ""}),
]

# Cuales de esas propiedades son referencias a asset y no cadenas sueltas.
ASSETS = ("MontageForzar", "VfxForzar")


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def apoyar(x, y):
    """Cota del suelo pisable en (x, y), medida.

    Se traza DESDE 600, no desde 3000: mas arriba la traza choca con los
    salientes de los acantilados y devuelve un techo creyendo que es suelo. Es
    el error que puso el destino dentro de la roca en la primera pasada.
    """
    d = sc("trace_world", {"start": {"x": x, "y": y, "z": 600.0},
                           "end": {"x": x, "y": y, "z": -800.0}})
    if d is None:
        raise RuntimeError("sin suelo bajo (%d, %d)" % (x, y))
    return round(600.0 - d, 1)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {"puestos": {}}

    sc("load_level", {"level_path": SUB})
    if sc("get_current_level", {}) != SUB:
        return {"error": "no se abrio el submapa"}

    puestos = {}
    out["suelo"] = {}
    for etiqueta, x, y, yaw, es_paso, destino, props in PIEZAS:
        # Un paso se apoya en el suelo; un destino va al centro de la capsula del
        # jugador, o sea suelo + 96. Ese `+96` es el mismo que se pago colocando
        # los enemigos de El Claro: el origen de un Character son las caderas.
        suelo = apoyar(x, y)
        out["suelo"][etiqueta] = suelo
        z = suelo if es_paso else suelo + CAPSULA + 4
        # `set_actor_transform` RESETEA escala y rotacion si no se las pasas:
        # el xform va siempre entero.
        xf = {"location": {"x": x, "y": y, "z": z},
              "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
              "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
        a = busca(etiqueta)
        if a is None:
            a = sc("add_to_scene_from_class", {
                "actor_type": {"refPath": CLASE if es_paso else DESTINO},
                "name": etiqueta, "xform": xf, "parent": None, "snap_to_ground": False})
            at("set_label", {"actor": a, "label": etiqueta})
            out["puestos"][etiqueta] = "creado"
        else:
            out["puestos"][etiqueta] = "ya estaba"
        at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
        sc("set_actor_folder", {"actor": a, "folder_path": CARPETA})
        puestos[etiqueta] = a

        if es_paso:
            # Un campo por llamada: el setter de propiedades aplica la primera y
            # con las referencias conviene no mezclarlas con cadenas.
            ot("set_properties", {"instance": a, "values": json.dumps(
                {"Destino": {"refPath": puestos[destino]["refPath"]}})})
            for campo in sorted(props):
                valor = props[campo]
                if campo in ASSETS:
                    valor = {"refPath": valor}
                ot("set_properties", {"instance": a,
                                      "values": json.dumps({campo: valor})})

    # --- releer del actor, no del script ---
    for etiqueta, x, y, yaw, es_paso, destino, props in PIEZAS:
        a = puestos[etiqueta]
        t = at("get_actor_transform", {"actor": a})
        ficha = {"loc": [round(t["location"][k]) for k in ("x", "y", "z")],
                 "yaw": round(t["rotation"]["yaw"], 1)}
        if es_paso:
            campos = ["Destino", "FlagPaso", "Requisito", "RequisitoForzar",
                      "FlagAbierta", "EsperaForzar", "MontageForzar", "VfxForzar"]
            p = json.loads(ot("get_properties", {"instance": a, "properties": campos}))
            for campo in campos:
                v = p[campo]
                ficha[campo] = str(v).split("/")[-1] if campo in ASSETS or campo == "Destino" else v
            b = at("get_actor_bounds", {"actor": a, "only_colliding": False})
            ficha["caja"] = {"min": [round(b["min"][k]) for k in ("x", "y", "z")],
                             "max": [round(b["max"][k]) for k in ("x", "y", "z")]}
        out.setdefault("comprobado", {})[etiqueta] = ficha

    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": SUB})

    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
